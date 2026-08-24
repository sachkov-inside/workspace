# inside-engineering 0.3.6

This package contains 32 shared skills:

- the complete stable suite from [`mattpocock/skills`](https://github.com/mattpocock/skills):
  18 engineering skills and 7 productivity skills;
- 7 frontend and web-development skills promoted from the Inside landing repository.

Experimental `in-progress` and `misc` directories from Matt Pocock's repository are intentionally
excluded.

## Sources

| Skills | Source | Imported snapshot | License |
| --- | --- | --- | --- |
| Matt Pocock stable suite (25) | [`mattpocock/skills`](https://github.com/mattpocock/skills), release `v1.2.3`, commit `885e2ca4d842d139e9aef4e48d366c63cb1b8013` | Direct import on 2026-08-19 | MIT; package `LICENSE` |
| `frontend-design` | [`anthropics/skills`](https://github.com/anthropics/skills) | Landing `cfa90027f5450dc3fcd05de13415168c1354044d` | Apache-2.0; skill `LICENSE.txt` |
| `impeccable` | [`pbakaus/impeccable`](https://github.com/pbakaus/impeccable) | Landing `cfa90027f5450dc3fcd05de13415168c1354044d` | Apache-2.0 upstream |
| `karpathy-guidelines` | [Andrej Karpathy's original guidance](https://x.com/karpathy/status/2015883857489522876) | Landing `bdd0177905df723ca4e4e2fb9288a4d8dc95701b` | MIT declared in skill metadata |
| `modern-web-guidance` | [`GoogleChrome/modern-web-guidance-src`](https://github.com/GoogleChrome/modern-web-guidance-src) | Landing `cfa90027f5450dc3fcd05de13415168c1354044d` | Apache-2.0 software; CC-BY-4.0 guides |
| `playwright-cli` | [`microsoft/playwright-cli`](https://github.com/microsoft/playwright-cli) | Landing `cfa90027f5450dc3fcd05de13415168c1354044d` | Apache-2.0 upstream |
| `vercel-react-best-practices` | [`vercel-labs/agent-skills`](https://github.com/vercel-labs/agent-skills) | Landing `cfa90027f5450dc3fcd05de13415168c1354044d` | MIT declared in skill metadata |
| `web-design-guidelines` | [`vercel-labs/agent-skills`](https://github.com/vercel-labs/agent-skills) | Landing `cfa90027f5450dc3fcd05de13415168c1354044d` | Not declared in the imported snapshot |

The package-level `LICENSE` applies to the Matt Pocock suite only. Each additional skill remains
subject to its own upstream terms.

Upstream updates are never pulled automatically. Review the upstream diff, import a deliberate
revision here, bump `manifest.json`, test a pilot repository, and only then update other
repositories.
