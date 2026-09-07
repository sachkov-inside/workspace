import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'packages/inside-engineering/github'
sys.path.insert(0, str(SOURCE))
from inside_tracker import GitHub, TrackerError, connection, identity
from tracker_event import arguments
from tracker_policy import decide


class PolicyTest(unittest.TestCase):
    def issue(self, **changes):
        return dict(kind='Issue', state='OPEN', labels=['ready-for-agent'], children=[], blockers=[], prs=[]) | changes

    def test_leaf_ready_then_claim_then_review(self):
        item = self.issue()
        self.assertEqual(decide(item).status, 'Ready')
        self.assertEqual(decide(item | {'session': {'phase': 'active'}}).status, 'In progress')
        self.assertEqual(decide(item | {'prs': [{'state': 'OPEN', 'isDraft': False}]}).status, 'Review')

    def test_draft_cannot_override_acceptance_gate(self):
        item = self.issue(labels=['ready-for-human'], prs=[{'state': 'OPEN', 'isDraft': True}])
        self.assertEqual(decide(item).status, 'Blocked')

    def test_not_planned_dependency_stays_blocked(self):
        self.assertEqual(decide(self.issue(blockers=[{'state': 'CLOSED', 'stateReason': 'NOT_PLANNED'}])).status, 'Blocked')

    def test_release_makes_specified_task_ready(self):
        self.assertEqual(decide(self.issue(session={'phase': 'released'}), 'In progress').status, 'Ready')

    def test_legacy_active_work_is_preserved(self):
        for status in ['In progress', 'Blocked', 'Review']:
            self.assertEqual(decide(self.issue(), status).status, status)

    def test_human_vocabulary_and_manual_decision(self):
        item = self.issue(labels=['backlog:human'])
        self.assertEqual(decide(item, 'In Progress').status, 'In Progress')
        self.assertEqual(decide(item, 'Review').status, 'Todo')
        self.assertEqual(decide(item | {'state': 'CLOSED'}).status, 'Done')

    def test_reopen_does_not_stay_done(self):
        self.assertEqual(decide(self.issue(), 'Done').status, 'Ready')

    def test_pr_lifecycle(self):
        pr = dict(kind='PullRequest', labels=[], state='OPEN', draft=True)
        self.assertEqual(decide(pr).status, 'In progress')
        self.assertEqual(decide(pr | {'draft': False}).status, 'Review')
        self.assertTrue(decide(pr | {'state': 'CLOSED'}).archive)
        self.assertEqual(decide(pr | {'state': 'MERGED'}).status, 'Done')

    def test_archive_and_pause_are_sticky(self):
        self.assertIsNone(decide(self.issue(archived=True)).status)
        self.assertIsNone(decide(self.issue(labels=['tracker:paused'])).status)

    def test_one_blocked_child_does_not_block_entire_aggregate(self):
        self.assertEqual(decide(self.issue(children=[{'state': 'OPEN'}]), 'In progress').status, 'In progress')

    def test_repeated_decision_converges(self):
        item = self.issue(prs=[{'state': 'OPEN', 'isDraft': False}])
        first = decide(item, 'In progress')
        self.assertEqual(first, decide(item, first.status))


class EventBoundaryTest(unittest.TestCase):
    def test_untrusted_pr_event_is_rejected(self):
        with self.assertRaises(TrackerError):
            arguments('pull_request', {}, 'sachkov-inside/platform', True)

    def test_default_is_report_only(self):
        self.assertEqual(arguments('issues', {'issue': {'number': 42}}, 'sachkov-inside/platform', False),
                         ['--issue', 'sachkov-inside/platform#42'])

    def test_only_workspace_can_sweep_all_repositories(self):
        with self.assertRaises(TrackerError):
            arguments('schedule', {}, 'sachkov-inside/platform', True)
        self.assertIn('--close-parents', arguments('schedule', {}, 'sachkov-inside/workspace', True))

    def test_noncentral_dispatch_cannot_write_other_repository(self):
        with self.assertRaises(TrackerError):
            arguments('workflow_dispatch', {}, 'sachkov-inside/platform', False, True, 'workspace#1')

    def test_manual_dispatch_remains_dry_even_when_events_enabled(self):
        self.assertNotIn('--apply', arguments('workflow_dispatch', {}, 'sachkov-inside/workspace', True))

    def test_shell_syntax_cannot_enter_issue_reference(self):
        for value in ['platform#1;echo x', 'other/repo#1', 'platform#0']:
            with self.assertRaises(TrackerError):
                identity(value)

    def test_privileged_workflow_uses_only_default_branch(self):
        workflow = (SOURCE / 'add-to-inside-project.yml').read_text()
        self.assertIn('pull_request_target:', workflow)
        self.assertIn('ref: ${{ github.event.repository.default_branch }}', workflow)
        self.assertNotIn('head.sha', workflow)
        self.assertNotIn('head.ref', workflow)
        self.assertIn('persist-credentials: false', workflow)


class GitHubBoundaryTest(unittest.TestCase):
    def result(self, status, out='', err=''):
        return subprocess.CompletedProcess([], status, out, err)

    @patch('inside_tracker.time.sleep')
    @patch('inside_tracker.subprocess.run')
    def test_transient_read_retried_and_recovers(self, run, sleep):
        run.side_effect = [self.result(1, err='HTTP 503'), self.result(0, '{}')]
        self.assertEqual(GitHub().call('repos/x/y'), {})
        self.assertEqual(run.call_count, 2)

    @patch('inside_tracker.subprocess.run')
    def test_permission_failure_is_not_hidden_or_retried(self, run):
        run.return_value = self.result(1, err='HTTP 403')
        with self.assertRaises(TrackerError):
            GitHub().call('repos/x/y')
        self.assertEqual(run.call_count, 1)

    @patch('inside_tracker.subprocess.run')
    def test_unknown_create_result_is_not_blindly_retried(self, run):
        run.return_value = self.result(1, err='connection reset')
        with self.assertRaises(TrackerError):
            GitHub().call('repos/x/y/issues/1/comments', {'body': 'claim'}, 'POST')
        self.assertEqual(run.call_count, 1)

    @patch('inside_tracker.time.sleep')
    @patch('inside_tracker.subprocess.run')
    def test_retry_limit(self, run, sleep):
        run.return_value = self.result(1, err='HTTP 429')
        with self.assertRaises(TrackerError):
            GitHub().call('repos/x/y')
        self.assertEqual(run.call_count, 3)

    def test_rest_pagination_includes_later_page(self):
        api = GitHub()
        with patch.object(api, 'call', side_effect=[list(range(100)), [100]]):
            self.assertEqual(api.pages('repos/x/y/issues'), list(range(101)))

    def test_graphql_pagination_includes_later_blocker(self):
        class API:
            def __init__(self):
                self.cursors = []
            def graphql(self, query, **variables):
                self.cursors.append(variables['cursor'])
                more = variables['cursor'] is None
                return {'node': {'blockedBy': {'nodes': [{'state': 'CLOSED' if more else 'OPEN'}],
                        'pageInfo': {'hasNextPage': more, 'endCursor': 'next'}}}}
        api = API()
        values = connection(api, 'node', 'Issue', 'blockedBy', 'state')
        self.assertEqual(values[-1]['state'], 'OPEN')
        self.assertEqual(api.cursors, [None, 'next'])


if __name__ == '__main__':
    unittest.main()

class ReconciliationTest(unittest.TestCase):
    def fixture(self, human=False):
        import copy
        from inside_tracker import Reconciler
        def card(identifier, status, **fields):
            return {'id': identifier, 'isArchived': False, 'fieldValues': {'nodes': [
                {'field': {'name': k}, 'name': v} for k, v in {'Status': status, **fields}.items()]}}
        class API:
            def __init__(self):
                self.cards = {('sachkov-inside/workspace', 1): {1: card('old', 'Ready', Priority='Now', Area='Operations')}}
                self.writes = []
            def graphql(self, query, **v):
                self.writes.append((query, v))
                cards = self.cards[('sachkov-inside/workspace', 1)]
                project = int(v['project'])
                if 'addProjectV2ItemById' in query:
                    cards[project] = card('new', '')
                    return {'addProjectV2ItemById': {'item': {'id': 'new'}}}
                if 'updateProjectV2ItemFieldValue' in query:
                    fields = cards[project]['fieldValues']['nodes']
                    fields[:] = [x for x in fields if x['field']['name'] != v['field']]
                    fields.append({'field': {'name': v['field']}, 'name': v['option']})
                    return {}
                if 'deleteProjectV2Item' in query:
                    del cards[project]
                    return {}
                if 'archiveProjectV2Item' in query:
                    cards[project]['isArchived'] = True
                    return {}
                raise AssertionError(query)
        api = API()
        runner = Reconciler.__new__(Reconciler)
        runner.api, runner.apply, runner.close_parents = api, True, False
        runner.projects = {n: {'id': str(n), 'fields': {
            name: {'id': name, 'options': [{'id': v, 'name': v} for v in values]}
            for name, values in {'Status': ['Ready', 'Todo', 'Done', 'In progress'],
                                 'Priority': ['Now'], **({'Area': ['Operations']} if n == 1 else {})}.items()}}
            for n in (1, 2)}
        runner.refresh = lambda: setattr(runner, 'cards', copy.deepcopy(api.cards))
        runner.refresh()
        item = dict(id='issue', repo='sachkov-inside/workspace', number=1, kind='Issue', state='OPEN',
                    labels=['backlog:human'] if human else ['ready-for-agent'], children=[], blockers=[], prs=[])
        return runner, api, item

    def test_route_to_human_and_retry_converge_without_area_field(self):
        from inside_tracker import field_values
        runner, api, item = self.fixture(human=True)
        with patch('inside_tracker.snapshot', return_value=item):
            runner.one(item['repo'], 1)
            count = len(api.writes)
            runner.one(item['repo'], 1)
        cards = api.cards[(item['repo'], 1)]
        self.assertEqual(set(cards), {2})
        self.assertEqual(field_values(cards[2]), {'Status': 'Todo', 'Priority': 'Now'})
        self.assertEqual(len(api.writes), count)

    def test_concurrent_project_edit_aborts_before_any_write(self):
        runner, api, item = self.fixture(human=True)
        api.cards[(item['repo'], 1)][1]['isArchived'] = True
        with patch('inside_tracker.snapshot', return_value=item), self.assertRaises(TrackerError):
            runner.one(item['repo'], 1)
        self.assertEqual(api.writes, [])

    def test_deferred_issue_does_not_return_on_ordinary_event(self):
        runner, api, item = self.fixture()
        api.cards = {}; runner.refresh(); item['labels'] = ['needs-info']
        with patch('inside_tracker.snapshot', return_value=item):
            row = runner.one(item['repo'], 1)
        self.assertEqual(row['action'], 'skip')
        self.assertEqual(api.writes, [])

    @patch('inside_tracker.subprocess.run')
    def test_graphql_unknown_mutation_not_retried(self, run):
        run.return_value = subprocess.CompletedProcess([], 1, '', 'connection reset')
        with self.assertRaises(TrackerError):
            GitHub().graphql('mutation { example }')
        self.assertEqual(run.call_count, 1)
