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

For implementation, specification, or architecture changes, read and follow `Review closure`,
`Pull request CI closure`, `Implementation report`, `Architecture fitness`, and `Pruning` in the
repository-root `WORKFLOW.md`. Those sections are the authority for finding dispositions,
current-head CI ownership, learning promotion, and completion.

Invoke `/code-review` from the original fixed point. When review changes code or durable documents,
re-run the relevant verification and invoke `/code-review` from that same fixed point again. Commit
only after the `WORKFLOW.md` readiness gate is satisfied.

## Owner handoff

After final review closure and current-head pull request CI closure, update the pull request body
using the repository template's Implementation Report. Derive it from the final diff, issue or
specification, verification evidence, and review outcomes. If code or durable documents change
afterward, repeat the relevant verification and review closure, then refresh the report for the new
head. Finish only when every changed surface is accounted for and the report records the current
remote head.
