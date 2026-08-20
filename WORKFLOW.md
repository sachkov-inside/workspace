# Developer Pipeline

This is the project-specific engineering agreement for Sachkov Inside. Installed skills define
their own invocation and steps; this file defines only the shared rules for repositories, branches,
pull requests, and owner gates.

## Routing

Create an issue in the repository that owns the outcome:

| Outcome | Repository |
|---|---|
| Product discovery, owner decision, shared document, or cross-repository initiative | `workspace` |
| Change or bug in the public landing | `inside-landing` |
| Change or bug in the Membership platform | `platform` |

A cross-repository initiative has a parent issue in Workspace and repository-local child issues.
The issue holds discussion and execution history; record confirmed durable knowledge once in a
versioned document. When connected, GitHub Project remains a projection over issues and pull
requests.

## Issues, branches, and pull requests

Product work, bugs, architecture, and substantial documentation changes start from one primary
repository-local issue. Trivial docs or chore work may go directly to a short pull request when it
needs no discussion, tracking, or owner decision.

Create branches from the current `main`. Tracked work uses `<type>/<issue>-<slug>`; trivial
untracked work uses `<type>/<slug>`. Supported types are `feat`, `fix`, `docs`, `chore`, `research`,
and `prototype`.

One meaningful task uses one branch and one pull request. For tracked work, the pull request
includes `Closes #<issue>`. Every pull request states the result, verification, `Not tested`, and
open owner decisions. Add UI evidence only for interface changes. GitHub deletes the head branch
after merge.

### Long-lived branches and deployment

`main` is the only long-lived integration branch. Preview, staging, and production are deployment
environments, not branches.

Create a temporary `release/<version>` only for a real maintenance boundary: supporting multiple
production versions, freezing a release candidate while `main` advances, or meeting an external
calendar or certification requirement. Record its support period and deletion condition when it is
created. A normal hotfix uses `fix/<issue>-<slug>` into `main`; use a backport pull request only for
an active release branch.

## Ready and Done

Tracked work is ready for implementation when the result, scope, acceptance criteria, blockers,
and owner decisions are known. Multi-session delivery also requires an agreed decomposition and
dependencies. Read readiness roles from the repository-local `docs/agents/triage-labels.md` and
Wayfinder structure from `docs/agents/issue-tracker.md`.

Work is ready for owner merge when:

- acceptance criteria are met without silently expanding scope;
- relevant focused checks and full repository verification pass;
- durable documents and ADRs are updated when a confirmed decision changed;
- the pull request follows its template, links an issue when applicable, and states `Not tested`;
- a UI change includes mobile and desktop evidence and passes the repository-specific UI
  Definition of Done;
- the owner gives explicit merge approval.

Implementation, specification, and architecture changes run Standards and Spec `code-review` from
an agreed fixed point. Trivial docs or chore work needs only a bounded diff review and relevant
verification.

## Owner gates

Explicit owner approval is required for:

- product and visual decisions;
- hard-to-reverse ADRs with a real trade-off;
- testing seams and ticket breakdown when the selected skill requires approval;
- publishing, payments, credentials, external messages, and other risky external writes;
- every pull request merge.

An agent implements a `ready-for-agent` issue autonomously within these boundaries. Only the owner,
or an agent acting after explicit owner approval, may squash-merge a pull request. Review readiness
alone is not merge permission.
