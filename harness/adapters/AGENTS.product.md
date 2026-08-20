<!-- inside-product-harness:start -->
## Inside product harness

This repository uses the versioned Sachkov Inside product harness.

- Shared skills live once in `.inside-harness/skills/`; `.agents/skills` and `.claude/skills` are
  relative discovery links. Change managed packages in the Workspace harness, then run the explicit
  update command.
- Repository-specific instructions and skills remain owned by this repository. Give local skills
  unique names under the same snapshot; do not shadow a managed skill.
- Invoke skills only when their descriptions match the task. Installing the suite does not make
  every workflow mandatory for every request.
- Keep this repository autonomous: build, test, run, and deploy must not depend on the Workspace
  repository or on machine-local paths.
- Treat user-level skills, MCP, plugins and hooks as unavailable. Declare every recurring
  capability in this repository's harness and keep credentials in native auth or environment.
- Runtimes without native project discovery search `.inside-harness/skills/REGISTRY.md` by intent
  and open only the matching `SKILL.md`.
- Do not edit managed package directories, state, or generated registry manually. Use the Workspace
  lifecycle commands and review the Git diff they produce.
<!-- inside-product-harness:end -->
