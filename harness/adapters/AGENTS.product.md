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
