# inside-engineering 0.3.13

This package contains 30 skills selected through repository profiles:

- the complete stable suite from [`mattpocock/skills`](https://github.com/mattpocock/skills):
  18 engineering skills and 7 productivity skills;
- `karpathy-guidelines` in every profile;
- 4 frontend and web-development skills in the `frontend` profile.

Experimental `in-progress` and `misc` directories from Matt Pocock's repository are intentionally
excluded.

## Sources

| Skills | Source | Imported snapshot | License |
| --- | --- | --- | --- |
| Matt Pocock stable suite (25) | [`mattpocock/skills`](https://github.com/mattpocock/skills), release `v1.2.3`, commit `885e2ca4d842d139e9aef4e48d366c63cb1b8013` | Base import on 2026-08-19; Inside adaptations below | MIT; package `LICENSE` |
| `impeccable` | [`pbakaus/impeccable`](https://github.com/pbakaus/impeccable) | Landing `cfa90027f5450dc3fcd05de13415168c1354044d` | Apache-2.0 upstream |
| `karpathy-guidelines` | [Andrej Karpathy's original guidance](https://x.com/karpathy/status/2015883857489522876) | Landing `bdd0177905df723ca4e4e2fb9288a4d8dc95701b` | MIT declared in skill metadata |
| `modern-web-guidance` | [`GoogleChrome/modern-web-guidance-src`](https://github.com/GoogleChrome/modern-web-guidance-src) | Landing `cfa90027f5450dc3fcd05de13415168c1354044d` | Apache-2.0 software; CC-BY-4.0 guides |
| `playwright-cli` | [`microsoft/playwright-cli`](https://github.com/microsoft/playwright-cli) | Landing `cfa90027f5450dc3fcd05de13415168c1354044d` | Apache-2.0 upstream |
| `vercel-react-best-practices` | [`vercel-labs/agent-skills`](https://github.com/vercel-labs/agent-skills) | Landing `cfa90027f5450dc3fcd05de13415168c1354044d` | MIT declared in skill metadata |

The package-level `LICENSE` applies to the Matt Pocock suite only. Each additional skill remains
subject to its own upstream terms.

The `core` profile contains the Matt Pocock suite plus `karpathy-guidelines`. The `frontend`
profile adds `impeccable`, `modern-web-guidance`, `playwright-cli`, and
`vercel-react-best-practices`. `frontend-design` and `web-design-guidelines` were removed because
their recurring branches are already covered by this smaller set.

## Inside adaptations to the Matt base

- `implement` closes every review finding, repeats review after fixes, owns current-head pull
  request CI through a terminal result, publishes a final Implementation Report for owner review,
  and promotes only reusable learning to a durable authority.
- `domain-modeling` requires ADR lifecycle status and preserves accepted decisions through
  deprecation or supersession.
- Shared delivery routing includes the autonomous `inside-telegram` application repository.

Upstream updates are never pulled automatically. Review the upstream diff, import a deliberate
revision here, bump `manifest.json`, test a pilot repository, and only then update other
repositories.
