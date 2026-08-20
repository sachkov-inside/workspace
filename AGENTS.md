# inside

## Repository role

Workspace owns product documents, cross-repository decisions, and the canonical source of the
shared product harness, including the Developer Pipeline. Application code, application ADRs,
build and deploy remain in the repository that owns the application.

## Working agreements

- For GitHub triage or Wayfinder operations, read `docs/agents/issue-tracker.md` and
  `docs/agents/triage-labels.md`.
- For product terminology, repository ownership or ADR placement, read `docs/agents/domain.md`.

## Verification

Run from the Workspace root:

```bash
python3 -m unittest discover -s harness/tests -v
harness/bin/inside-harness health .
harness/bin/inside-harness diff .
```

For a harness release or rollout, also run `health` and `diff` against each target repository.
Keep product/cross-repo documents outside managed harness directories. Change managed workflow or
skills only in `harness/packages/inside-engineering/` and distribute them through the harness
lifecycle.

<!-- inside-product-harness:start -->
## Inside product harness

This repository uses the versioned Sachkov Inside product harness.

- For shared issue routing, branches, pull requests, readiness, Project status, and
  owner-controlled merge, read the repository-local `WORKFLOW.md`.
- Shared skills, `WORKFLOW.md`, triage labels, and `.inside-harness/` are managed distribution
  artifacts. Change their canonical package source and distribute them through the harness
  lifecycle; do not hand-edit installed copies.
- Repository-specific instructions and skills remain local. Give local skills unique names; do not
  shadow a managed skill.
- Invoke skills only when their descriptions match the task. Installing the suite does not make
  every workflow mandatory for every request.
- Keep this repository autonomous: build, test, run, deploy, and agent work must not depend on
  another repository, machine-local paths, or user-level skills, MCP, plugins, or hooks.
<!-- inside-product-harness:end -->
