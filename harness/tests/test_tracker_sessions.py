import copy
import json
import subprocess
import sys
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'packages/inside-engineering/github'
sys.path.insert(0, str(SOURCE))
import inside_tracker
from inside_tracker import MARKER, TrackerError
from tracker_sessions import operate, read_session, transition, WRITER


def issue(**changes):
    return dict(kind='Issue', repo='sachkov-inside/platform', number=123, state='OPEN',
                labels=['ready-for-agent'], children=[], blockers=[], assignees=[], prs=[]) | changes


def child(number, state='OPEN', reason='', repository='sachkov-inside/platform'):
    return dict(id=f'I_{number}', number=number, state=state, stateReason=reason,
                repository={'nameWithOwner': repository})


def linked_pr(number, state='OPEN'):
    return dict(number=number, state=state, isDraft=False, headRefName='feat/123-test',
                repository={'nameWithOwner': 'sachkov-inside/platform'})


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
        for changes in [dict(children=[child(330)]), dict(blockers=[dict(state='OPEN')]),
                        dict(blockers=[dict(state='CLOSED', stateReason='NOT_PLANNED')]),
                        dict(labels=['ready-for-human']), dict(labels=['ready-for-agent', 'tracker:gate']),
                        dict(labels=['ready-for-agent', 'tracker:paused']), dict(state='CLOSED')]:
            with self.subTest(changes=changes), self.assertRaises(TrackerError):
                start(issue(**changes))

    def test_aggregate_with_closed_decomposition_can_start(self):
        children = [child(330, 'CLOSED', 'NOT_PLANNED'), child(331, 'CLOSED', 'NOT_PLANNED'),
                    child(332, 'CLOSED', 'COMPLETED')]
        self.assertEqual(start(issue(children=children))['phase'], 'active')

    def test_open_child_blocks_start_and_is_named(self):
        children = [child(332, 'CLOSED', 'COMPLETED'), child(330),
                    child(45, repository='sachkov-inside/inside-telegram')]
        with self.assertRaisesRegex(TrackerError, r'platform#330.*inside-telegram#45') as raised:
            start(issue(children=children))
        self.assertNotIn('#332', str(raised.exception))

    def test_occupied_session_identifier_with_new_request_grants_nothing(self):
        state = start()
        with self.assertRaisesRegex(TrackerError, r'--request request-one.*unique session'):
            start(state=state, request='request-two')

    def test_same_session_resumes_from_blocked_or_review(self):
        blocked = transition(issue(), start(), 'block', 'session-one', '', 'waiting', 'request-two')
        review = transition(issue(prs=[linked_pr(7)]), start(), 'handoff', 'session-one', '', 'verified', 'request-two')
        for state in [blocked, review]:
            with self.subTest(phase=state['phase']):
                resumed = start(issue(assignees=[WRITER], prs=[linked_pr(7)]), state, request='request-three')
                self.assertEqual((resumed['phase'], resumed['request']), ('active', 'request-three'))

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

    def test_handoff_after_merge_points_to_release(self):
        merged = linked_pr(552, 'MERGED')
        with self.assertRaisesRegex(TrackerError, r'platform#552 is already merged.*release'):
            transition(issue(prs=[merged]), start(), 'handoff', 'session-one', '', 'verified', 'request-two')
        foreign = merged | {'headRefName': 'feat/123-earlier'}
        with self.assertRaisesRegex(TrackerError, 'requires a linked open non-draft PR'):
            transition(issue(prs=[foreign]), start(), 'handoff', 'session-one', '', 'verified', 'request-two')

    def test_snapshot_reads_child_and_pr_identity(self):
        raw = dict(node_id='I_123', state='open', labels=[], assignees=[], html_url='https://github.com/x',
                   updated_at='2026-09-15T00:00:00Z', state_reason=None)
        class API:
            def call(self, endpoint):
                return raw
        with patch.object(inside_tracker, 'connection', side_effect=lambda *args: args[4]):
            item = inside_tracker.snapshot(API(), 'sachkov-inside/platform', 123)
        for field in ['children', 'prs']:
            with self.subTest(field=field):
                self.assertRegex(item[field], r'\bnumber\b')
                self.assertIn('repository { nameWithOwner }', item[field])

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

class ClientReceiptTest(unittest.TestCase):
    def setup_request(self, **changes):
        from argparse import Namespace
        from tracker_sessions import fingerprint
        args = Namespace(command='start', issue='platform#123', session='session-one', branch='feat/123-test',
                         reason='', request='request-one', timeout=5)
        for k, v in changes.items():setattr(args, k, v)
        values = dict(command=args.command, issue='sachkov-inside/platform#123', session=args.session,
                      branch=args.branch, reason=args.reason, request=args.request)
        run = dict(id=42, display_title=f"session {args.request} {fingerprint(values)}",
                   status='completed', conclusion='success', run_attempt=1, html_url='https://github.com/test/run/42')
        state = start(request=args.request or 'request-one')
        result = dict(ok=True, issue=values['issue'], **state)
        return args, run, state, result

    class API:
        def __init__(self, runs, state):
            self.runs, self.state, self.writes, self.reads = runs, state, [], []
        def call(self, endpoint, payload=None, method=None):
            if method == 'POST':
                self.writes.append(endpoint)
                return None
            self.reads.append(endpoint)
            value = self.runs.pop(0) if len(self.runs) > 1 else self.runs[0]
            return {'workflow_runs': value, 'total_count': len(value)}
        def pages(self, endpoint):
            return [dict(id=1, user={'login':WRITER}, body=MARKER+'\n'+json.dumps(self.state))]

    def invoke(self, args, api, result):
        from tracker_sessions import request_command
        def download(command, **kw):
            Path(command[command.index('--dir')+1], 'tracker-session-result.json').write_text(json.dumps(result))
            return subprocess.CompletedProcess(command, 0, '', '')
        with patch('tracker_sessions.GitHub', return_value=api), patch('tracker_sessions.subprocess.run', side_effect=download), patch('tracker_sessions.time.sleep'):
            request_command(args)

    def test_correct_start_receipt_and_live_state_are_required(self):
        args, run, state, result = self.setup_request()
        self.invoke(args, self.API([[run]], state), result)

    def test_release_receipt_cannot_authorize_start(self):
        args, run, state, result = self.setup_request()
        state |= {'command':'release', 'phase':'released', 'reason':'stop'}
        result |= state
        with self.assertRaises(TrackerError):
            self.invoke(args, self.API([[run]], state), result)

    def test_wrong_issue_branch_or_superseded_state_is_rejected(self):
        for change in [{'issue':'sachkov-inside/platform#999'}, {'branch':'feat/other'}, {'request':'request-else'}]:
            args, run, state, result = self.setup_request()
            with self.subTest(change=change), self.assertRaises(TrackerError):
                self.invoke(args, self.API([[run]], state), result | change)
        args, run, state, result = self.setup_request()
        with self.assertRaises(TrackerError):
            self.invoke(args, self.API([[run]], state | {'request':'request-new'}), result)

    def test_reusing_request_for_different_inputs_fails_before_write(self):
        args, run, state, result = self.setup_request()
        args.branch = 'feat/another'
        api = self.API([[run]], state)
        with self.assertRaises(TrackerError):self.invoke(args, api, result)
        self.assertEqual(api.writes, [])

    def test_newly_cancelled_run_does_not_grant_ownership(self):
        args, run, state, result = self.setup_request()
        run |= {'conclusion':'cancelled'}
        with self.assertRaisesRegex(TrackerError, 'cancelled'):
            self.invoke(args, self.API([[], [run]], state), result)

    def test_timeout_does_not_grant_ownership(self):
        args, run, state, result = self.setup_request(timeout=0)
        with self.assertRaisesRegex(TrackerError, 'timed out'):
            self.invoke(args, self.API([[]], state), result)

    def test_explicit_retry_of_failed_projection_reruns_same_operation(self):
        args, run, state, result = self.setup_request()
        api = self.API([[run | {'conclusion':'failure'}], [run | {'run_attempt':2}]], state)
        self.invoke(args, api, result)
        self.assertEqual(api.writes, ['repos/sachkov-inside/workspace/actions/runs/42/rerun'])

    def test_partial_trusted_state_is_invalid(self):
        args, run, state, result = self.setup_request()
        for change in ['command', 'reason', 'updated_at']:
            broken = {k:v for k,v in state.items() if k != change}
            with self.assertRaises(TrackerError):
                read_session(self.API([[]], broken), 'sachkov-inside/platform', 123)


class RequestHistoryTest(unittest.TestCase):
    setup_request = ClientReceiptTest.setup_request
    invoke = ClientReceiptTest.invoke
    API = ClientReceiptTest.API
    def test_previous_request_on_second_page_is_recovered_without_dispatch(self):
        args, run, state, result = self.setup_request()
        unrelated = [run | {'display_title': 'session different-operation'} for _ in range(100)]
        api = self.API([unrelated, [run], unrelated, [run]], state)
        self.invoke(args, api, result)
        self.assertEqual(api.writes, [])

    def test_different_operation_on_second_page_is_rejected_before_dispatch(self):
        args, run, state, result = self.setup_request()
        unrelated = [run | {'display_title': 'session different-operation'} for _ in range(100)]
        args.branch = 'feat/changed'
        api = self.API([unrelated, [run]], state)
        with self.assertRaises(TrackerError):self.invoke(args, api, result)
        self.assertEqual(api.writes, [])


class RequestWindowTest(unittest.TestCase):
    """A timestamped request is searched only among runs created since shortly before it."""
    setup_request = ClientReceiptTest.setup_request
    invoke = ClientReceiptTest.invoke
    API = ClientReceiptTest.API

    def test_recovered_request_reads_one_filtered_page(self):
        args, run, state, result = self.setup_request(request='20260924T191000Z-0123456789abcdef')
        api = self.API([[run]], state)
        self.invoke(args, api, result)
        listings = [e for e in api.reads if '/runs?' in e]
        self.assertTrue(listings)
        for endpoint in listings:
            self.assertIn('created=%3E%3D2026-09-24T18:55:00Z', endpoint)
            self.assertIn('page=1', endpoint)
        self.assertEqual(api.writes, [])

    def test_new_request_is_timestamped_and_searched_from_its_creation(self):
        from tracker_sessions import fingerprint
        args, _, _, _ = self.setup_request(request=None)
        api = ClientReceiptTest.API([[]], None)
        dispatched = {}

        def call(endpoint, payload=None, method=None):
            if method == 'POST':
                dispatched.update(payload['inputs'])
                return None
            if not dispatched:
                return {'workflow_runs': [], 'total_count': 0}
            searched.append(endpoint)
            run = dict(id=42, display_title=f"session {dispatched['request']} {dispatched['fingerprint']}",
                       status='completed', conclusion='success', run_attempt=1, html_url='https://github.com/test/run/42')
            return {'workflow_runs': [run], 'total_count': 1}
        api.call = call
        searched = []
        before = datetime.now(timezone.utc).replace(microsecond=0)
        state = start(request='placeholder-id')

        def download(command, **kw):
            state.update(request=dispatched['request'])
            api.state = state
            Path(command[command.index('--dir')+1], 'tracker-session-result.json').write_text(
                json.dumps(dict(ok=True, issue='sachkov-inside/platform#123', **state)))
            return subprocess.CompletedProcess(command, 0, '', '')
        from tracker_sessions import request_command
        with patch('tracker_sessions.GitHub', return_value=api), \
                patch('tracker_sessions.subprocess.run', side_effect=download), patch('tracker_sessions.time.sleep'):
            request_command(args)
        self.assertRegex(dispatched['request'], r'^\d{8}T\d{6}Z-[0-9a-f]{16}$')
        issued = datetime.strptime(dispatched['request'][:16], '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
        self.assertLessEqual(before, issued)
        window = (issued - timedelta(minutes=15)).strftime('%Y-%m-%dT%H:%M:%SZ')
        self.assertTrue(searched)
        self.assertTrue(all(f'created=%3E%3D{window}' in e for e in searched))
        values = {k: v for k, v in dispatched.items() if k != 'fingerprint'}
        self.assertEqual(dispatched['fingerprint'], fingerprint(values))

    def test_receipt_download_survives_dropped_connection(self):
        from tracker_sessions import request_command
        args, run, state, result = self.setup_request()
        attempts = []

        def download(command, **kw):
            attempts.append(command)
            if len(attempts) == 1:
                return subprocess.CompletedProcess(command, 1, '', 'error connecting to api.github.com: EOF')
            Path(command[command.index('--dir')+1], 'tracker-session-result.json').write_text(json.dumps(result))
            return subprocess.CompletedProcess(command, 0, '', '')
        with patch('tracker_sessions.GitHub', return_value=self.API([[run]], state)), \
                patch('tracker_sessions.subprocess.run', side_effect=download), patch('tracker_sessions.time.sleep'):
            request_command(args)
        self.assertEqual(len(attempts), 2)

    def test_window_at_search_cap_reads_complete_history_without_dispatch(self):
        args, run, state, result = self.setup_request(request='20260924T191000Z-0123456789abcdef')
        class CappedAPI(ClientReceiptTest.API):
            def call(self, endpoint, payload=None, method=None):
                if method == 'POST':raise AssertionError('must not dispatch')
                self.reads.append(endpoint)
                if 'created=' in endpoint:
                    return {'workflow_runs': [], 'total_count': 1000}
                return {'workflow_runs': [run], 'total_count': 1}
        api = CappedAPI([[]], state)
        self.invoke(args, api, result)
        self.assertTrue(any('created=' not in e for e in api.reads if '/runs?' in e))

    def test_recovered_run_before_its_window_is_found_in_complete_history(self):
        # The local clock ran fast when the request was issued: its run predates the window.
        args, run, state, result = self.setup_request(request='20260924T191000Z-0123456789abcdef')
        class SkewedAPI(ClientReceiptTest.API):
            def call(self, endpoint, payload=None, method=None):
                if method == 'POST':raise AssertionError('must not dispatch a recovered request twice')
                self.reads.append(endpoint)
                runs = [] if 'created=' in endpoint else [run]
                return {'workflow_runs': runs, 'total_count': len(runs)}
        api = SkewedAPI([[]], state)
        self.invoke(args, api, result)
        self.assertEqual(api.writes, [])

    def test_unreachable_history_while_waiting_keeps_waiting(self):
        from inside_tracker import TransientError
        args, run, state, result = self.setup_request()
        api = self.API([[run]], state)
        call, failures = api.call, [TransientError('EOF')]
        def flaky(endpoint, payload=None, method=None):
            if '/runs?' in endpoint and api.writes and failures:
                raise failures.pop()
            return call(endpoint, payload, method)
        api.call = flaky
        api.runs = [[], [run]]
        self.invoke(args, api, result)
        self.assertEqual(failures, [])

    def test_impossible_request_timestamp_is_rejected(self):
        args, run, state, result = self.setup_request(request='20261399T000000Z-abcdefgh')
        with self.assertRaisesRegex(TrackerError, 'invalid request identifier'):
            self.invoke(args, self.API([[run]], state), result)


class CompleteHistoryTest(unittest.TestCase):
    def test_legacy_request_reads_complete_unfiltered_history(self):
        args, run, state, result = ClientReceiptTest().setup_request()
        api = ClientReceiptTest.API([[run]], state)
        ClientReceiptTest().invoke(args, api, result)
        self.assertTrue(all('created=' not in e for e in api.reads))

    def test_truncated_history_refuses_dispatch(self):
        args, run, state, result = ClientReceiptTest().setup_request()
        class TruncatedAPI(ClientReceiptTest.API):
            def call(self, endpoint, payload=None, method=None):
                if method == 'POST':raise AssertionError('must not dispatch')
                return {'workflow_runs': [], 'total_count': 1001}
        with self.assertRaisesRegex(TrackerError, 'Incomplete request history'):
            ClientReceiptTest().invoke(args, TruncatedAPI([[]], state), result)


class RepositoryOwnershipTest(unittest.TestCase):
    def test_workshop_pr_can_handoff_its_platform_tracker_issue(self):
        pr = dict(state='OPEN', isDraft=False, headRefName='feat/123-test',
                  repository={'nameWithOwner':'sachkov-inside/workshop-cases'})
        state = transition(issue(prs=[pr]), start(), 'handoff', 'session-one', '', 'verified', 'request-two')
        self.assertEqual(state['phase'], 'review')
        pr['repository']['nameWithOwner'] = 'outside/unknown'
        with self.assertRaises(TrackerError):
            transition(issue(prs=[pr]), start(), 'handoff', 'session-one', '', 'verified', 'request-two')

    def test_main_exception_is_scoped_to_inside_content(self):
        item = issue(repo='sachkov-inside/inside-content')
        state = transition(item, None, 'start', 'session-one', 'main', '', 'request-one')
        from tracker_sessions import validate_state
        validate_state(state, item['repo'])
        with self.assertRaises(TrackerError):
            transition(issue(), None, 'start', 'session-one', 'main', '', 'request-one')

class DispatchBoundaryTest(unittest.TestCase):
    def invoke(self, wire, expected):
        import tracker_sessions as sessions
        from unittest.mock import MagicMock
        value = wire | {'fingerprint': sessions.fingerprint(expected)}
        api = MagicMock()
        api.call.return_value = {'login': WRITER}
        with patch.dict('os.environ', {'GITHUB_REPOSITORY': sessions.CONTROLLER,
                'GITHUB_WORKFLOW': 'Inside agent sessions', 'GITHUB_REF': 'refs/heads/main',
                'GITHUB_EVENT_PATH': '/event.json'}), patch.object(sessions, 'GitHub', return_value=api), \
                patch.object(sessions.Path, 'read_text', return_value=json.dumps({'inputs': value})), \
                patch.object(sessions.Path, 'write_text'), patch.object(sessions, 'Reconciler'), \
                patch.object(sessions, 'operate', return_value={}) as operation:
            sessions.worker()
            operation.assert_called_once_with(api, 'sachkov-inside/platform', 123,
                expected['command'], expected['session'], expected['branch'],
                expected['reason'], expected['request'])

    def values(self, **changes):
        return dict(command='start', issue='sachkov-inside/platform#123', session='session-one',
                    branch='feat/123-test', reason='', request='request-one') | changes

    def test_empty_optional_reason_survives_github_delivery(self):
        expected = self.values()
        for wire in [{k:v for k,v in expected.items() if k != 'reason'}, expected | {'reason': None}]:
            with self.subTest(wire=wire): self.invoke(wire, expected)

    def test_empty_optional_branch_survives_non_start_delivery(self):
        expected = self.values(command='release', branch='', reason='Acceptance completed')
        for wire in [{k:v for k,v in expected.items() if k != 'branch'}, expected | {'branch': None}]:
            with self.subTest(wire=wire): self.invoke(wire, expected)

    def test_changed_command_fields_remain_rejected(self):
        expected = self.values()
        with self.assertRaises(TrackerError): self.invoke(expected | {'branch':'feat/123-other'}, expected)

    def test_unknown_inputs_remain_rejected(self):
        expected = self.values()
        with self.assertRaises(TrackerError): self.invoke(expected | {'unexpected':'value'}, expected)

    def test_invalid_optional_input_type_is_rejected(self):
        expected = self.values()
        with self.assertRaises(TrackerError): self.invoke(expected | {'reason':False}, expected)
