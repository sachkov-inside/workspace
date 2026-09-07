# Inside tracker automation

The owning module is `.github/scripts/inside_tracker.py`, with pure decisions in
`.github/scripts/tracker_policy.py`. Workspace's `harness/tests/test_tracker.py` owns policy,
pagination, failure and event-boundary fitness. All installed copies are versioned by the harness.

## Facts and decisions

Issues and PRs hold facts; Projects display them. Developer Pipeline uses Inbox, Ready, In progress,
Review, Blocked and Done. Human Backlog uses Todo, In Progress and Done. Only Workspace issues may
carry `backlog:human`. Human outcomes keep their manually accepted open state and close explicitly.
Priority, Area and product decisions are not inferred from prose.

- Closed issues project to Done, retaining `completed` or `not_planned` on the issue.
- Merged PRs project to Done. Closed, unmerged PR rows are archived. Draft PRs project to In progress;
  open non-draft PRs project to Review. A linked draft does not prove review readiness.
- Unresolved native blockers, `needs-info`, `ready-for-human` or `tracker:gate` keep a leaf Blocked.
  A dependency closed as `not_planned` needs an explicit scope decision and removal of that edge.
- Complete readiness with no active work projects to Ready. Existing active manual states without
  session metadata remain unchanged and are reported for adoption; do not take over another session.
- Aggregate progress is not inferred from one blocked child. Preserve its manual open status.
- Archived items and `tracker:paused` work are never restored automatically. Untracked closed or
  needs-info work is skipped by the sweep; an explicit bounded request may add an untracked issue.

## Parent completion

`tracker:auto-complete` is explicit permission for a fully decomposed delivery aggregate. Before
applying it, represent every remaining acceptance step as a native child or blocker. The controller
closes only a nonempty set of completed children, with completed blockers and no owner gate. It never
closes a `backlog:human` issue. Do not apply this label while decomposition is in progress.

The central Workspace sweep owns automatic closure. A reopened child does not silently undo an
owner's accepted result; inspect that inconsistency and explicitly reopen/replan the parent.
The legacy shell entry point is read-only and cannot bypass these checks.

## Recovery and activation

Event workflows execute only default-branch code, including Dependabot/fork PR metadata. No PR code,
artifact or dependency installation runs with the tracker secret. Events coalesce; the Workspace
sweep runs twice an hour and repairs missed events. GitHub scheduling can be delayed. There is no
claim of instantaneous consistency or guaranteed event ordering.

All installations start in report mode. Set repository variable `INSIDE_TRACKER_APPLY=true` only
after bounded acceptance; dispatch input `apply=true` permits a specific live check before enabling
scheduled writes. Disable that variable to return automatic events to report mode.

```bash
python3 .github/scripts/inside_tracker.py --issue platform#310
python3 .github/scripts/inside_tracker.py --repository platform
# Explicit write after inspecting the report:
python3 .github/scripts/inside_tracker.py --issue platform#310 --apply
```

Workspace workflow_dispatch can reconcile a bounded issue or all repositories. Other repositories
can only request their own scope. Every decision is JSONL in the Actions artifact. Failures retain
partial reports and fail the run. Reads/idempotent PATCH retry transient errors at most three times;
unknown create/mutation results are reconciled by a fresh run, not blindly retried. State is reread
before writes, then read back from Projects. A concurrent edit fails that item and the next run
recalculates it. Cross-repository parent chains may need another sweep as children settle.

The `INSIDE_PROJECT_TOKEN` needs organization Projects write and repository Issues write, plus
Metadata/Pull requests read over the participating repositories. Checkout uses GITHUB_TOKEN with
Contents read, not the PAT. Do not copy this PAT into Dependabot secrets. Using GITHUB_TOKEN for
cross-repository issue writes or assuming it will trigger downstream close workflows is unsupported.

Before enabling, inspect the Workflows page of both Projects. Disable competing Status/auto-close
rules and auto-add rules that bypass `backlog:human` routing. Validate a completed child/parent in
one repository and across repositories, pending gate, not_planned, draft/ready/reopen, closed unmerged
PR, missed event, archive and routing. Keep test issues as closed history. Merge remains owner-gated.
