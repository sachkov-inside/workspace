# inside

## Repository role

Workspace owns product documents, cross-repository decisions, Developer Pipeline and the canonical
source of the shared product harness. Application code, application ADRs, build and deploy remain
in the repository that owns the application.

## Developer Pipeline

For issue routing, discovery/spec boundaries, branch/PR lifecycle, readiness, completion and merge
gates, read `WORKFLOW.md`. Every PR starts from a repo-local issue. Merge remains owner-controlled.

Engineering skills read repository-local configuration from:

- `docs/agents/issue-tracker.md` for GitHub issue and Wayfinder operations;
- `docs/agents/triage-labels.md` for canonical triage roles;
- `docs/agents/domain.md` for product vocabulary and ADR boundaries.

## Verification

Run from the Workspace root:

```bash
python3 -m unittest discover -s harness/tests -v
harness/bin/inside-harness health .
harness/bin/inside-harness diff .
```

For a harness release or rollout, also run `health` and `diff` against each target repository.
Keep product/cross-repo documents outside managed harness directories; change shared skills only in
`harness/packages/inside-engineering/` and distribute them through the harness lifecycle.

<!-- inside-product-harness:start -->
## Inside product harness

This repository uses the versioned Sachkov Inside product harness.

- Shared skills installed in `.agents/skills/` are managed distribution artifacts. Change their
  canonical source in the Workspace harness, then run the explicit update command.
- Repository-specific instructions and skills remain owned by this repository. Give local skills
  unique names; do not shadow a managed skill.
- Invoke skills only when their descriptions match the task. Installing the suite does not make
  every workflow mandatory for every request.
- Keep this repository autonomous: build, test, run, and deploy must not depend on the Workspace
  repository or on machine-local paths.
- Treat user-level skills, MCP, plugins and hooks as unavailable. Declare every recurring
  capability in this repository's harness and keep credentials in native auth or environment.
- Do not edit `.inside-harness/` manually. Use the Workspace lifecycle commands and review the Git
  diff they produce.
<!-- inside-product-harness:end -->
