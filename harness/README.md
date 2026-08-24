# Sachkov Inside product harness

The Workspace is the canonical source of the shared product harness. Each repository receives a
committed, project-local distribution and remains usable without the Workspace being present.

## Runtime layout

- Codex, Kimi Code, and OpenCode discover the shared suite at `.agents/skills/`.
- Claude Code discovers the same release at `.claude/skills/`.
- `AGENTS.md` is the common instruction entrypoint. `CLAUDE.md` imports it for Claude Code.
- `WORKFLOW.md` and `docs/agents/triage-labels.md` are shared managed documents.
- Repository-specific skills stay in the shared snapshot under unique names and are preserved.

The two runtime directories are repository-relative discovery links to one committed snapshot at
`.inside-harness/skills/`. Discovery stays project-local and uses no machine-local link targets,
user-level installation, or custom prompt routing.

The harness assumes no user-level skills, MCP, plugins or hooks. A repository that needs an
integration owns its native project config and health check; credentials remain outside Git.

The current `inside-engineering 0.3.4` package contains the Developer Pipeline, triage labels, and
32 shared skills: Matt Pocock's complete stable suite of 25 plus 7 frontend and web-development
skills. Their exact sources and licensing notes are recorded in
`packages/inside-engineering/SOURCE.md`.

## Commands

Run commands from the Workspace root:

```bash
harness/bin/inside-harness install .
harness/bin/inside-harness install repositories/platform
harness/bin/inside-harness install repositories/landing --adopt-existing

harness/bin/inside-harness diff repositories/platform
harness/bin/inside-harness health repositories/platform
harness/bin/inside-harness update repositories/platform
harness/bin/inside-harness rollback repositories/platform --to <workspace-git-ref>
```

`--adopt-existing` is only for the first install when a repository already contains skills with
managed names and those directories are deliberately being brought under product-harness ownership.
Unknown skills are never removed.

`update` refuses to overwrite changed managed files. A package release that only adds new managed
content can be adopted safely before the initial installation diff is committed. A no-op update is
safe and idempotent.

`rollback --to` reads the package and adapters from a previous Workspace Git ref. It requires that
the chosen ref already contains this harness layout.

## Releasing an update

1. Change the canonical package in the Workspace.
2. Bump its version in `manifest.json` and update provenance when upstream changes.
3. Run unit tests and install/update a pilot repository.
4. Run `diff` and `health`; test native discovery on the pilot.
5. Commit and tag the Workspace release only after owner approval.
6. Update other repositories one at a time and review their Git diffs.

The version tag is required: it binds the package version to an exact Workspace commit and gives
`rollback --to` a stable Git ref. A GitHub Release is optional and is useful only for separate
release notes or downloadable assets. The current installer does not download GitHub Releases;
`update` reads the canonical Workspace package and `rollback --to` reads the selected Workspace
Git ref.

There are no automatic upstream updates, machine-local links, profiles, or complex lock files.
