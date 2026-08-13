# Suggested commands

- Tracker queue: `gh issue list --repo KirillSachkov/sachkov-inside --limit 20`.
- Inspect issue: `gh issue view <number> --repo KirillSachkov/sachkov-inside` plus REST read-back per `docs/agents/issue-tracker.md`.
- Full local evidence: `bash scripts/verify-workspace.sh`.
- Whitespace/conflict lint: `git diff --check`.
- Harness health uses the canonical brain package; resolve it through its `harness/bin/brain-root` tool rather than copying package files.