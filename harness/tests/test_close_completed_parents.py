"""Acceptance protection for the replacement of the old blind parent-chain script."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'packages/inside-engineering/github'))
from tracker_policy import decide


class ParentCompletionTest(unittest.TestCase):
    def parent(self, **changes):
        value = dict(kind='Issue', state='OPEN', labels=['tracker:auto-complete'],
                     children=[dict(state='CLOSED', stateReason='COMPLETED')], blockers=[])
        return value | changes

    def test_opt_in_complete_children_close(self):
        self.assertTrue(decide(self.parent()).close)

    def test_no_opt_in_keeps_parent_open(self):
        self.assertFalse(decide(self.parent(labels=[])).close)

    def test_no_children_cannot_complete_parent(self):
        self.assertFalse(decide(self.parent(children=[])).close)

    def test_open_or_cancelled_children_cannot_complete_parent(self):
        for state, reason in [('OPEN', None), ('CLOSED', 'NOT_PLANNED')]:
            with self.subTest(state=state):
                self.assertFalse(decide(self.parent(children=[dict(state=state, stateReason=reason)])).close)

    def test_outstanding_native_blocker_prevents_completion(self):
        self.assertFalse(decide(self.parent(blockers=[dict(state='OPEN', stateReason=None)])).close)

    def test_acceptance_and_human_outcome_cannot_auto_complete(self):
        for label in ['tracker:gate', 'needs-info', 'ready-for-human', 'backlog:human']:
            with self.subTest(label=label):
                self.assertFalse(decide(self.parent(labels=['tracker:auto-complete', label])).close)

    def test_closed_parent_is_not_closed_again(self):
        self.assertFalse(decide(self.parent(state='CLOSED')).close)

    def test_archived_or_paused_aggregate_is_not_completed(self):
        self.assertFalse(decide(self.parent(archived=True)).close)
        self.assertFalse(decide(self.parent(labels=['tracker:auto-complete', 'tracker:paused'])).close)
