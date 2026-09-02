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
