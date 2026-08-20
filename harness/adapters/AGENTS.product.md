<!-- inside-product-harness:start -->
## Inside product harness

This repository uses the versioned Sachkov Inside product harness.

- For shared issue routing, branches, pull requests, readiness, Project status, and
  owner-controlled merge, read the repository-local `WORKFLOW.md`.
- Shared skills live once in `.inside-harness/skills/`; runtime discovery paths are relative links
  to that snapshot. Shared skills, `WORKFLOW.md`, triage labels, state, and the registry are managed
  artifacts: change their canonical package source and distribute it through the harness lifecycle.
- Repository-specific instructions and skills remain local. Give local skills unique names in the
  shared snapshot; do not shadow a managed skill.
- Invoke skills only when their descriptions match the task. Installing the suite does not make
  every workflow mandatory for every request.
- Runtimes without native project discovery search `.inside-harness/skills/REGISTRY.md` by intent
  and open only the matching `SKILL.md`.
- Keep this repository autonomous: build, test, run, deploy, and agent work must not depend on
  another repository, machine-local paths, or user-level skills, MCP, plugins, or hooks.
<!-- inside-product-harness:end -->
