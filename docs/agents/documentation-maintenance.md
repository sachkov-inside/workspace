# Documentation maintenance

Use this table for the `Documentation impact` step in `WORKFLOW.md`. Every durable fact has one
owning document. For product terms, access, the content model, positioning, repository ownership,
ADR placement, and shared specifications, follow the routing in [domain.md](domain.md); this table
adds the owners that routing does not cover.

| Changed fact | Owning document |
|---|---|
| Issue routing, Project fields, Wayfinder | [issue-tracker.md](issue-tracker.md) |
| Delivery workflow, review, readiness, shared skills, tracker automation | The canonical package under `harness/packages/inside-engineering/`, released through the harness lifecycle |
| Harness lifecycle, release, and rollout procedure | [HARNESS.md](../../HARNESS.md); command details stay in [harness/README.md](../../harness/README.md) |
| Consumers that receive a harness release | `harness/rollout-targets.json` |
| Harness code rules | [CODING_STANDARDS.md](../../CODING_STANDARDS.md) |
| Workspace agent routing and verification | [AGENTS.md](../../AGENTS.md) outside the managed block |
