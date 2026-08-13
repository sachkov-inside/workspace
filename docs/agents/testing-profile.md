# Testing profile

This repository is a content/product-operations control plane. It has no application runtime,
build artifact or product-code test suite. Verification is direct evidence over documents,
tracker state and authorized external operations.

## Required local checks

```bash
bash scripts/verify-workspace.sh
git diff --check
```

`verify-workspace.sh` checks the required harness/project skeleton, unresolved template markers,
tracker frontmatter and drift from the installed harness package. It does not validate that a
commercial provider, payment or Telegram operation succeeded.

## Task-selected evidence

- Documents: internal links and authority boundaries are inspected in the affected scope.
- GitHub Issues: every write and both ends of every relation are read back through `gh`.
- Research: source URL, retrieval date and the boundary between verified fact and inference are
  present; volatile provider terms are refreshed for the decision revision.
- Telegram/Tribute: dry-run or sandbox evidence precedes activation where supported; real payment,
  access, cancellation and removal evidence is required before declaring launch readiness.
- Content portfolio: the linked unit is read back from `sachkov-content`; a local status claim is
  not accepted as production evidence.

## Candidate identity

Evidence belongs to the exact commit and GitHub Issue revision under review. A later content,
provider-policy or repository change invalidates only the affected evidence and must be refreshed.
