# inside

## Repository role

Workspace owns shared product documents, cross-repository decisions, and the canonical source of
the shared product harness, including the Developer Pipeline. Repository-specific product briefs,
application code, application ADRs, build and deploy remain in the repository that owns the
product surface or application.

## Working agreements

- For GitHub issue routing, Project fields, or Wayfinder operations, read
  `docs/agents/issue-tracker.md`.
- For readiness-label triage, read `docs/agents/triage-labels.md`.
- For product terminology, repository ownership or ADR placement, read `docs/agents/domain.md`.
- For coding and review rules, read `CODING_STANDARDS.md`.

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

- For shared delivery rules and owner gates, read the repository-local `WORKFLOW.md` when the task
  touches issues, branches, pull requests, review, readiness, or merge.
- Native runtimes discover the selected skill profile through `.agents/skills` or `.claude/skills`.
  Fallback runtimes use `.inside-harness/skills/REGISTRY.md`: route by intent only to `Model` rows;
  open a `User` row only when the user names that skill.
- Managed skills and workflow files change in the canonical package and arrive through the harness
  lifecycle. Repository-specific skills stay local under unique names.
- Keep build, test, run, deploy, and agent work repository-local. Project-owned integrations may
  use native config; record them in `.inside-harness/integrations.json` without credentials.
<!-- inside-product-harness:end -->
