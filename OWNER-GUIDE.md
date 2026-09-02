# Sachkov Inside: как устроена разработка

Этот документ объясняет владельцу topology и точки управления. Исполнительные правила для
агентов находятся в repository-local `AGENTS.md`, а единый delivery contract — в `WORKFLOW.md`.

## Репозитории

| Repository | Владеет |
|---|---|
| `workspace` | Общие product-документы, cross-repository решения, Developer Pipeline и canonical harness |
| `inside-landing` | Публичный landing, его product/copy/visual contracts, код и deploy |
| `platform` | Membership Platform, application contracts, код, ADR и deploy |
| `inside-telegram` | Telegram application, linking, Membership observations/evidence, код и deploy |

Актуальные paths и visibility находятся в [`REPOSITORIES.md`](REPOSITORIES.md). Каждый repository
автономен: build, test, runtime и agent work используют только его versioned files и внешние
runtime interfaces.

## Product harness

Canonical source находится в `harness/`. Installer раскладывает выбранный skill profile и managed
workflow files в каждый repository:

```text
.inside-harness/skills/                  один physical snapshot
.agents/skills -> ../.inside-harness/skills
.claude/skills -> ../.inside-harness/skills
.inside-harness/product-harness.json    package state и profile
.inside-harness/integrations.json       repository-owned integration inventory, когда нужен
AGENTS.md                               общий managed block + local instructions
CLAUDE.md                               импорт AGENTS.md
WORKFLOW.md                             Developer Pipeline
docs/agents/triage-labels.md            readiness roles
```

Profiles:

- `core` — общий engineering workflow; используется Workspace и Telegram;
- `frontend` — `core` плюс UI/browser skills; используется Landing и Platform.

Repository-specific skill хранится в том же snapshot под уникальным именем и не входит в
`managedSkills`. Native MCP/hooks/settings принадлежат repository, а их paths, hashes, runtimes,
verification command и имена secret environment variables фиксируются в integration inventory.
Credentials в Git не попадают.

## Какие документы являются authority

| Файл | Authority |
|---|---|
| `AGENTS.md` | Repository role, task routing, commands и completion criteria |
| `CODING_STANDARDS.md` | Recurring engineering judgement, которое не выражено executable guardrail |
| `WORKFLOW.md` | Issues, worktrees, branches, PR, review closure и owner merge gate |
| `docs/agents/issue-tracker.md` | Repository-specific GitHub operations и Wayfinder mapping |
| `docs/agents/domain.md` | Pointer к product contract, `CONTEXT.md` и ADR owning rules |
| `CONTEXT.md` | Канонический domain glossary без implementation detail |
| `docs/adr/*.md` | Hard-to-reverse trade-offs и их lifecycle |
| `.inside-harness/skills/REGISTRY.md` | Fallback index с явным `Model`/`User` invocation |
| `.github/PULL_REQUEST_TEMPLATE.md` | Result, issue link, verification, Not tested и owner decisions |

Один durable факт живёт в одном authority. Code, schema, tests или config остаются полной authority
для локальной implementation detail; документация не кэширует то, что агент надёжно читает из
окружения.

## Изменение harness

1. Изменить canonical package, adapter или CLI в Workspace.
2. Запустить Workspace unit tests, `health .` и `diff .`.
3. Обновить один pilot repository с его сохранённым profile.
4. Проверить pilot `diff`, `health`, native discovery и repository-specific verification.
5. Обновить остальные repository отдельными reviewable changes.

Основные команды запускаются из Workspace:

```bash
harness/bin/inside-harness update <repository>
harness/bin/inside-harness diff <repository>
harness/bin/inside-harness health <repository>
```

При первой profile migration используется `update <repository> --profile core|frontend`; дальше
profile хранится в state. Installer останавливается на dirty managed path и сохраняет неизвестные
local files/skills.

## Delivery и GitHub

Human Backlog и Developer Pipeline имеют разные роли; точная routing/state model находится в
[`WORKFLOW.md`](WORKFLOW.md). Repository issue или PR остаётся source of truth, а Projects являются
проекциями.

Одна tracked задача имеет один owning repository, issue, task branch, writing worktree и pull
request. Supporting agents работают read-only. Merge выполняется только после явного owner GO;
review readiness не является merge permission.

## Роль владельца

Владелец подтверждает product/visual решения, hard-to-reverse ADR, testing seams и decomposition,
разрешает credentialed/external writes и каждый merge. Готовую `ready-for-agent` задачу агент
выполняет автономно внутри этих границ и возвращает outcome, caveats, verification и ссылки на
durable artifacts.
