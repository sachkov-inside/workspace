# Domain docs

Workspace owns shared product language, cross-repository boundaries and shared decisions.

For product terminology or cross-repository ownership, read the relevant local sources:

- `product/README.md` for shared product language and the human-facing repository index;
- `REPOSITORIES.md` for repository ownership;
- `CONTEXT.md` and relevant `docs/adr/` entries when they exist.

External links in `product/README.md` are navigation for people, not Workspace agent dependencies.
Route repository-specific product work to the owning repository and its issue; Workspace work must
remain executable from the local shared context and cross-repository decisions.

Use one `CONTEXT.md` and root `docs/adr/` unless real code or package boundaries later justify a
multi-context map. Missing context or ADR files are not setup failures; `domain-modeling` creates
them lazily when durable terminology or a hard-to-reverse trade-off is actually resolved.

Shared product and cross-repository decisions live in Workspace. A repository-specific product
brief and application ADRs live in the repository that owns the product surface. Temporary
discussion stays in the issue; the confirmed decision is recorded once in a versioned document.
