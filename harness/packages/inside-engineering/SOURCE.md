# inside-engineering 0.4.11

This package contains 30 skills selected through repository profiles:

- the complete stable suite from [`mattpocock/skills`](https://github.com/mattpocock/skills):
  18 engineering skills and 7 productivity skills;
- `karpathy-guidelines` in every profile;
- 4 frontend and web-development skills in the `frontend` profile.

Experimental `in-progress` and `misc` directories from Matt Pocock's repository are intentionally
excluded.

## Sources

| Skills | Source | Imported snapshot | License |
| --- | --- | --- | --- |
| Matt Pocock stable suite (25) | [`mattpocock/skills`](https://github.com/mattpocock/skills), release `v1.2.3`, commit `885e2ca4d842d139e9aef4e48d366c63cb1b8013` | Base import on 2026-08-19; Inside adaptations below | MIT; package `LICENSE` |
| `impeccable` | [`pbakaus/impeccable`](https://github.com/pbakaus/impeccable) | Landing `cfa90027f5450dc3fcd05de13415168c1354044d` | Apache-2.0 upstream |
| `karpathy-guidelines` | [Andrej Karpathy's original guidance](https://x.com/karpathy/status/2015883857489522876) | Landing `bdd0177905df723ca4e4e2fb9288a4d8dc95701b` | MIT declared in skill metadata |
| `modern-web-guidance` | [`GoogleChrome/modern-web-guidance-src`](https://github.com/GoogleChrome/modern-web-guidance-src) | Landing `cfa90027f5450dc3fcd05de13415168c1354044d` | Apache-2.0 software; CC-BY-4.0 guides |
| `playwright-cli` | [`microsoft/playwright-cli`](https://github.com/microsoft/playwright-cli) | Landing `cfa90027f5450dc3fcd05de13415168c1354044d` | Apache-2.0 upstream |
| `vercel-react-best-practices` | [`vercel-labs/agent-skills`](https://github.com/vercel-labs/agent-skills) | Landing `cfa90027f5450dc3fcd05de13415168c1354044d` | MIT declared in skill metadata |

The package-level `LICENSE` applies to the Matt Pocock suite only. Each additional skill remains
subject to its own upstream terms.

The `core` profile contains the Matt Pocock suite plus `karpathy-guidelines`. The `frontend`
profile adds `impeccable`, `modern-web-guidance`, `playwright-cli`, and
`vercel-react-best-practices`. `frontend-design` and `web-design-guidelines` were removed because
their recurring branches are already covered by this smaller set.

## Inside adaptations to the Matt base

- Shared conversation rules use the user's language, plain wording, and decision-focused choices;
  `grilling` keeps each question to one decision and groups independent questions into readable
  rounds, and `wait-what` re-explains in the user's language instead of forcing English.
- `implement` closes every review finding, repeats review after fixes, commits and pushes once
  the checks for the change and review closure pass, owns current-head pull request CI through a
  terminal result, publishes a final Implementation Report for owner review, and promotes only
  reusable learning to a durable authority.
- `domain-modeling` requires ADR lifecycle status and preserves accepted decisions through
  deprecation or supersession.
- Shared delivery routing includes the autonomous `inside-telegram` application repository and
  marks the deprecated `inside-landing` as closed to new work.
- The shared entrypoint and `WORKFLOW.md` make the pipeline stages owner-driven: an agent does not
  chain Specification, Ticket breakdown, or Implementation without an explicit owner request, a
  request that names several stages starts each of them, and a development session starts in the
  repository that owns the outcome.
- `WORKFLOW.md` keeps an owner approval for its stated scope, scopes verification to the change,
  and names when a failing check calls for `diagnosing-bugs`.
- `WORKFLOW.md` gives every issue one native GitHub issue type (`Epic`, `Feature`, `Improvement`,
  `Bug`, `Task`) instead of category labels; `to-spec`, `to-tickets`, `triage`, and the GitHub
  tracker template set that type.
- `WORKFLOW.md` places every agent worktree in one predictable location outside tracked files and
  apart from primary checkouts, and makes session cleanup (containers, processes, worktrees,
  branches, stash entries, tracker session) the final task step; `implement` points to it.
- Tracker automation retries idempotent GitHub reads through dropped connections, and the session
  CLI finds its run among runs created since its timestamped request identifier instead of listing
  the complete run history.
- `WORKFLOW.md` adds the `Acceptance` delivery state with the `tracker:acceptance` label, and lists
  the current `Area` values; the tracker projects the label and the session CLI refuses to start
  such an issue.
- Managed workflows pin every third-party action to a commit SHA with a version comment, which
  `inside-harness` package validation enforces; the managed `inside-harness-health.yml` runs
  `health` in every installed repository against the Workspace release tag of its version, and a
  managed `.github/scripts/.gitignore` ignores Python bytecode.
- Agent knowledge lives in the repository: `WORKFLOW.md` adds `Rule sources` (a new rule needs a
  Specification, ADR, owner decision, or confirmed environment fact, otherwise it is an owner
  proposal), `Documentation impact` (reconcile changed durable facts with their owning documents
  and the Specification), and `Session learning` (move session knowledge to a script, issue, or
  owning document, never runtime-local memory); `to-spec` adds a `Documents and rules` section,
  `implement` points to the new sections, the `code-review` Spec axis checks missing document
  updates and unsourced rules, and the pull request template asks for both.
- `WORKFLOW.md` lets the writing agent fast-forward the primary checkout after its merge, integrates
  published branches by merge instead of rebase, reads `mergeable` when no check starts, reads the
  reported head by command, and states how review ended; the shared `AGENTS.md` block asks for a
  decision criterion when a choice waits on measurement; tracker automation documents unique
  session identifiers and owner adoption of an assigned issue.
- `inside-harness health` requires a Claude Code bridge beside every nested `AGENTS.md` and checks
  local pointers in product, specification, and ADR documents.

Upstream updates are never pulled automatically. Review the upstream diff, import a deliberate
revision here, bump `manifest.json`, test a pilot repository, and only then update other
repositories.
