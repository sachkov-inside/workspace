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
integration owns its native project config and `.inside-harness/integrations.json`; `health`
verifies its path, SHA-256, runtime ownership, verification command, and secret-variable names.
Credentials remain outside Git and the verification command is run explicitly by the repository.

The package contains the Developer Pipeline, triage labels, the completed-parent lifecycle script,
and two skill profiles. `core` contains Matt Pocock's complete stable suite plus
`karpathy-guidelines`; `frontend` adds four browser/UI skills. Exact contents and sources are in
`packages/inside-engineering/manifest.json` and `SOURCE.md`.

## Commands

Run commands from the Workspace root:

```bash
harness/bin/inside-harness install . --profile core
harness/bin/inside-harness install repositories/platform --profile frontend
harness/bin/inside-harness install repositories/landing --profile frontend --adopt-existing

harness/bin/inside-harness diff repositories/platform
harness/bin/inside-harness health repositories/platform
harness/bin/inside-harness update repositories/platform
harness/bin/inside-harness rollback repositories/platform --to <workspace-git-ref>
```

After installation, `update`, `diff`, and `rollback` preserve the stored profile. Pass `--profile`
only for the initial profile migration or an intentional profile change.

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

There are no automatic upstream updates, machine-local links, user-level project profiles, or
complex lock files. Repository skill profiles are explicit, versioned package selections.
