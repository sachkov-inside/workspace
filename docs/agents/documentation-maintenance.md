# Documentation maintenance

Use this table for the `Documentation impact` step in `WORKFLOW.md`. Every durable fact has one
owning document in the Workspace; repository-specific facts belong to the repository that owns the
product surface, as `docs/agents/domain.md` explains.

| Changed fact | Owning document |
|---|---|
| Shared product term, meaning, or relationship | [CONTEXT.md](../../CONTEXT.md) |
| What content is open to whom, tiers, sale states, access transitions | [product/access-model.md](../../product/access-model.md) |
| Content model, formats, editorial and publication ownership | [product/content-series-authoring-brief.md](../../product/content-series-authoring-brief.md) |
| Audience, positioning, subscription promise | [product/README.md](../../product/README.md) |
| Repository ownership, visibility, local paths | [REPOSITORIES.md](../../REPOSITORIES.md) |
| Cross-repository architecture decision | A new or superseding ADR in [docs/adr](../adr/) |
| Shared contract across repositories | The owning specification in [docs/specifications](../specifications/) |
| Issue routing, Project fields, Wayfinder | [issue-tracker.md](issue-tracker.md) |
| Delivery workflow, review, readiness, shared skills, tracker automation | The canonical package under `harness/packages/inside-engineering/`, released through the harness lifecycle |
| Harness commands, release, rollout targets | [harness/README.md](../../harness/README.md) and `harness/rollout-targets.json` |
| Harness code rules | [CODING_STANDARDS.md](../../CODING_STANDARDS.md) |
| Workspace agent routing and verification | [AGENTS.md](../../AGENTS.md) outside the managed block |

Research notes under `docs/research/` record evidence at a date; they are not authorities. When a
research conclusion becomes a decision, record it in the owning document above.
