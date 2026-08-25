---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets. Resolve the fixed point before
editing so verification and review compare the whole implementation against one stable baseline.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

## Review closure

Run `/code-review` from the fixed point. Account for every actionable finding:

- fix it in this change;
- defer it to a linked tracker issue when it is valid but outside scope;
- or reject it with concrete evidence when it does not apply.

After fixes, re-run the relevant checks and re-run `/code-review` from the same fixed point. Repeat
until both review axes pass or every remaining finding has an explicit disposition.

Promote only reusable learning. Prefer an executable constraint; use a repository coding standard
for recurring judgement, an ADR for a hard-to-reverse trade-off, and the tracker for deferred work.
Keep one-off findings in the pull request history rather than creating a review ledger. Apply the
review-closure, architecture-fitness, and pruning rules in `WORKFLOW.md` before committing.

Commit only after the implementation, verification, durable learning, and review dispositions are
all complete.
