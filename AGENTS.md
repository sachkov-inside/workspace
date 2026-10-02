# inside

## Repository role

Workspace holds the shared product and legal documents of Sachkov Inside. It has no issues, no
application code and no development process of its own. Development of Inside runs in the
repository that owns the outcome; `platform` owns the developer process.

## Working agreements

- For product terminology, Series/content decisions, editorial handoff, repository ownership or
  ADR placement, read `docs/agents/domain.md`.
- Create issues in the repository that owns the outcome: `platform` or `inside-telegram`. Do not
  create issues here.
- Every durable fact has one owning document; `docs/agents/domain.md` routes to it. Update the
  owner and link to it instead of repeating the fact.
- Start a development session in the owning repository so its rules and skills load. This
  directory only holds documents and the local checkouts under `repositories/`.

## Verification

A document change needs a check of its content: read the changed text against its sources and
make sure every local link resolves.

## Human communication

- Speak to the user in their language. In Russian, prefer ordinary Russian words over optional
  English terms. Keep code, commands, exact product or API names, and established project terms
  unchanged. Do not invent abbreviations.
- Lead with what happened or what must be decided and why it matters. Use short, natural sentences
  with one idea each. Remove filler, but keep normal grammar.
- Use an unfamiliar specialist term only when it is needed for the current decision. Explain it in
  plain words on first use.
- When offering a choice, name the decision directly. Give each option a short everyday label and
  one sentence explaining what it changes. Mark the recommendation and explain its reason plainly.
- When a choice depends on facts not yet measured, state the criterion that decides it and what
  each outcome of the measurement means, so whoever measures can apply it without a new decision.
