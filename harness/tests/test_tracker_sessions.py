import copy
import json
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'packages/inside-engineering/github'
sys.path.insert(0, str(SOURCE))
from inside_tracker import MARKER, TrackerError
from tracker_sessions import operate, read_session, transition, WRITER


def issue(**changes):
    return dict(kind='Issue', repo='sachkov-inside/platform', number=123, state='OPEN',
                labels=['ready-for-agent'], children=[], blockers=[], assignees=[], prs=[]) | changes


def start(item=None, state=None, session='session-one', request='request-one'):
    return transition(item or issue(), state, 'start', session, 'feat/123-test', '', request)


class SessionPolicyTest(unittest.TestCase):
    def test_two_serialized_starts_have_one_owner(self):
        state = start()
        with self.assertRaisesRegex(TrackerError, 'occupied'):
            start(state=state, session='session-two', request='request-two')

    def test_same_request_is_idempotent(self):
        state = start()
        self.assertEqual(start(state=state), state)

    def test_request_id_cannot_be_reused_for_another_operation(self):
        state = start()
        with self.assertRaises(TrackerError):
            transition(issue(), state, 'release', 'session-one', '', 'stop', 'request-one')

    def test_foreign_session_cannot_release_or_handoff(self):
        for command in ['release', 'handoff', 'block']:
            with self.subTest(command=command), self.assertRaises(TrackerError):
                transition(issue(), start(), command, 'session-two', '', 'reason', 'request-two')

    def test_legacy_assigned_or_pr_work_is_not_claimable(self):
        for changes in [dict(assignees=['KirillSachkov']), dict(prs=[{'state': 'OPEN'}])]:
            with self.assertRaises(TrackerError):
                start(issue(**changes))

    def test_children_blockers_gate_and_closed_issue_are_not_claimable(self):
        for changes in [dict(children=[{}]), dict(blockers=[dict(state='OPEN')]),
                        dict(labels=['ready-for-human']), dict(labels=['ready-for-agent', 'tracker:gate']),
                        dict(labels=['ready-for-agent', 'tracker:paused']), dict(state='CLOSED')]:
            with self.subTest(changes=changes), self.assertRaises(TrackerError):
                start(issue(**changes))

    def test_block_and_release_require_reason(self):
        with self.assertRaises(TrackerError):
            transition(issue(), start(), 'block', 'session-one', '', '', 'request-two')

    def test_handoff_requires_own_nondraft_pr(self):
        state = start()
        for prs in [[], [dict(state='OPEN', isDraft=True)], [dict(state='OPEN', isDraft=False, headRefName='other')]]:
            with self.assertRaises(TrackerError):
                transition(issue(prs=prs), state, 'handoff', 'session-one', '', 'tests passed', 'request-two')
        pr = dict(state='OPEN', isDraft=False, headRefName='feat/123-test', repository={'nameWithOwner':'sachkov-inside/platform'})
        result = transition(issue(prs=[pr]), state, 'handoff', 'session-one', '', 'tests passed', 'request-two')
        self.assertEqual(result['phase'], 'review')

    def test_released_task_without_pr_can_be_claimed(self):
        state = transition(issue(), start(), 'release', 'session-one', '', 'stopped', 'request-two')
        result = start(issue(assignees=[WRITER]), state, session='session-two', request='request-three')
        self.assertEqual(result['session'], 'session-two')

    def test_old_timestamp_does_not_expire_ownership(self):
        state = start() | {'updated_at': '2000-01-01T00:00:00Z'}
        with self.assertRaises(TrackerError):
            start(state=state, session='session-two', request='request-two')


class SessionRemoteTest(unittest.TestCase):
    class API:
        def __init__(self, lose_response=False):
            self.comments = []
            self.lose_response = lose_response
            self.creates = 0
        def pages(self, endpoint):
            return copy.deepcopy(self.comments)
        def call(self, endpoint, payload=None, method=None):
            if method == 'POST':
                self.creates += 1
                self.comments.append(dict(id=1, user={'login':WRITER}, **payload))
                if self.lose_response:
                    raise TrackerError('connection reset after accepted write')
                return self.comments[0]
            if method == 'PATCH' and 'comments/' in endpoint:
                self.comments[0].update(payload)
                return self.comments[0]
            if method == 'PATCH':
                return {'assignees':[{'login':WRITER}]}
            return {'assignees':[{'login':WRITER}]}

    def test_unknown_create_response_reconciles_without_duplicate(self):
        api = self.API(lose_response=True)
        with patch('tracker_sessions.snapshot', return_value=issue()):
            result = operate(api, 'sachkov-inside/platform', 123, 'start', 'session-one', 'feat/123-test', '', 'request-one')
        self.assertTrue(result['ok'])
        self.assertEqual(api.creates, 1)
        self.assertEqual(len(api.comments), 1)

    def test_duplicate_or_malformed_trusted_state_fails_closed(self):
        api = self.API()
        api.comments = [dict(id=1, user={'login':WRITER}, body=MARKER+'\n{}')]
        with self.assertRaises(TrackerError):
            read_session(api, 'sachkov-inside/platform', 123)
        api.comments *= 2
        with self.assertRaises(TrackerError):
            read_session(api, 'sachkov-inside/platform', 123)

    def test_untrusted_comment_cannot_claim_task(self):
        api = self.API()
        api.comments = [dict(id=1, user={'login':'someone-else'}, body=MARKER+'\n{}')]
        self.assertEqual(read_session(api, 'sachkov-inside/platform', 123), (None, None))

    def test_concurrent_callers_under_single_writer_produce_one_grant(self):
        api, lock, results = self.API(), threading.Lock(), []
        def request(session):
            with lock:  # models the one Workspace Actions concurrency group
                try:
                    results.append(operate(api, 'sachkov-inside/platform', 123, 'start', session,
                                           'feat/123-test', '', 'request-'+session))
                except TrackerError:
                    results.append({'ok':False})
        with patch('tracker_sessions.snapshot', return_value=issue()):
            threads = [threading.Thread(target=request, args=(s,)) for s in ['session-one','session-two']]
            for t in threads:t.start()
            for t in threads:t.join()
        self.assertEqual(sum(r['ok'] for r in results), 1)
        self.assertEqual(api.creates, 1)

    def test_workflow_enforces_single_central_writer(self):
        workflow = (SOURCE/'inside-agent-sessions.yml').read_text()
        self.assertIn('group: inside-agent-session-writer', workflow)
        self.assertIn('cancel-in-progress: false', workflow)
        self.assertIn("github.repository == 'sachkov-inside/workspace'", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertNotIn('pull_request:', workflow)


if __name__ == '__main__':
    unittest.main()
