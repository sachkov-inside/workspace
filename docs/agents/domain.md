# Domain docs

Workspace owns product language, cross-repository boundaries and shared decisions.

For product terminology or cross-repository ownership, read the relevant local sources:

- `product/README.md` and the relevant brief under `product/`;
- `REPOSITORIES.md` for repository ownership;
- `CONTEXT.md` and relevant `docs/adr/` entries when they exist.

Use one `CONTEXT.md` and root `docs/adr/` unless real code or package boundaries later justify a
multi-context map. Missing context or ADR files are not setup failures; `domain-modeling` creates
them lazily when durable terminology or a hard-to-reverse trade-off is actually resolved.

Product and cross-repository decisions live in Workspace. Application-specific ADRs live in the
repository that implements them. Temporary discussion stays in the issue; the confirmed decision
is recorded once in a versioned document.
