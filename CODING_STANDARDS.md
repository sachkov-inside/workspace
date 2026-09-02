# Coding standards

These standards cover the Workspace-owned harness CLI, tests, and lifecycle shell script. Product
documents use their owning specifications and domain sources instead.

## Harness changes

- Change managed behavior only under `harness/`; installed snapshots are generated outputs.
- Keep installation conservative: preserve unknown repository files and local skills, reject dirty
  managed paths, and resolve every target inside the selected repository.
- Use Python's standard library for the lifecycle CLI. Add a dependency only when a demonstrated
  capability cannot remain small and portable without it.
- Represent a harness invariant in the closest executable check. Every new rejection path has a
  focused test that first proves the invalid repository shape.
- Keep generated state deterministic: sorted collections, stable JSON/Markdown rendering, relative
  discovery paths, and no machine-local values.

## Shell automation

- Start lifecycle scripts with `set -euo pipefail`, validate required inputs before external calls,
  and quote every expansion that may contain repository or issue data.
- Keep GitHub mutations idempotent. A repeated event must converge without duplicating state or
  rewriting an already completed result.
- Scope `shellcheck` suppressions to the exact command whose quoting is intentional and state the
  reason beside it.

## Documentation and review

- Keep one authority for each rule: executable guardrail first, then this file for recurring
  judgement, ADR for a hard-to-reverse trade-off, and Git history for one-off review findings.
- Agent-facing paths are repository-relative and every required Markdown pointer resolves.
- Completion means focused tests and the full Workspace verification in `AGENTS.md` pass, and each
  target repository selected for rollout passes `health` and `diff`.
