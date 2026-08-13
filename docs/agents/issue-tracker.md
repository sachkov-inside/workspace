---
provider: github
project: KirillSachkov/sachkov-inside
---

# Issue tracker

## Native operations

Use `gh` directly for project `KirillSachkov/sachkov-inside`. Create/update issues, labels, assignees,
relations, notes, MRs/PRs, and native close state through that CLI/API. Read the affected issue and
both ends of every relation back after each write. Keep Test Plan in the issue and delivery report
in the MR/PR description.

Read before and after every write:

```bash
gh issue view <number> --repo KirillSachkov/sachkov-inside
gh api repos/KirillSachkov/sachkov-inside/issues/<number>
```

Native commands:

```bash
gh issue create --repo KirillSachkov/sachkov-inside --title "..." --body-file <file> --label "..."
gh issue edit <number> --repo KirillSachkov/sachkov-inside --add-assignee @me --add-label "workflow::in-progress"
gh issue comment <number> --repo KirillSachkov/sachkov-inside --body-file <file>
gh issue close <number> --repo KirillSachkov/sachkov-inside
gh pr view <number> --repo KirillSachkov/sachkov-inside
```

GitHub Issues is the only writable tracker. Parent/sub-issue and blocker support must be checked
against the current GitHub API before use. If the available API cannot create the required native
relation, put exactly one unambiguous `Part of #<number>` or `Blocked by #<number>` line in the
child body and read both issues back. Do not simulate relations with labels.

## Metadata

Types: `type::map`, `type::epic`, `type::task`, `type::bug`, `type::research`, `type::prototype`.
Open workflow: exactly one of `workflow::backlog`, `workflow::ready`, `workflow::blocked`, `workflow::in-progress`, `workflow::review`.
Executable work: exactly one of `afk` or `hitl`. Wayfinder children add `scope::wayfinder`.
Closed issues have no `workflow::*`; rejected work adds `out-of-scope` before close.

## Project policy

- Issues and pull requests are private project records; never copy secrets, payment credentials or
  participant PII into them.
- Product/content decisions remain `hitl`. Source-backed provider, market and operational research
  can be `afk`; no research ticket authorizes payment activation, publication or invitations.
- A content unit is linked to its authority in `sachkov-content`; this tracker records the
  Membership portfolio decision and status, not a duplicate production workflow.
