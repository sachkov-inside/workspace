# Sachkov Inside: как устроена разработка

## Репозитории

| Repository | Назначение |
|---|---|
| `workspace` | Product-документы, общие решения, Developer Pipeline и canonical harness |
| `inside-landing` | Публичный landing |
| `platform` | Membership-продукт |

Каждый repository автономен. Его agent instructions, skills, workflow, build и deploy не зависят
от наличия Workspace рядом на диске.

## Harness

Canonical source находится в `workspace/harness/`. Команда `harness/bin/inside-harness` копирует
версию package в каждый repository и проверяет её.

Внутри repository:

```text
.inside-harness/skills/                  одна физическая копия skills
.agents/skills -> ../.inside-harness/skills
.claude/skills -> ../.inside-harness/skills
AGENTS.md                                 входные правила для агентов
CLAUDE.md                                 подключает AGENTS.md для Claude
WORKFLOW.md                               общий Developer Pipeline
docs/agents/                              tracker, labels и domain routing
```

Codex, Kimi и OpenCode используют `.agents/skills`; Claude использует `.claude/skills`. Обе ссылки
ведут в один repository-local snapshot. macOS проверен локально, Linux проверяется Harness CI;
Native Windows пока не проверен.

Основные команды запускаются из Workspace:

```bash
harness/bin/inside-harness health <repository>
harness/bin/inside-harness diff <repository>
harness/bin/inside-harness update <repository>
harness/bin/inside-harness rollback <repository> --to <workspace-git-ref>
```

## Как начинается и проходит работа

1. Создать issue в repository, который владеет результатом.
2. Уточнить результат, scope, acceptance criteria, blockers и решения владельца.
3. Поставить `ready-for-agent`, когда задача готова к реализации.
4. Создать ветку от актуального `main`: `<type>/<issue>-<slug>`.
5. Реализовать, выполнить проверки и открыть PR с `Closes #<issue>`.
6. Провести Standards и Spec review для нетривиальных изменений.
7. Владелец явно разрешает squash merge. После merge ветка удаляется.

Типы веток: `feat`, `fix`, `docs`, `chore`, `research`, `prototype`. `main` — единственная постоянная
integration branch. Environment и release branches заранее не создаются.

## GitHub Project

[Inside Project](https://github.com/orgs/sachkov-inside/projects/1) — общая доска; source of truth
остаётся в repository issue или PR.

Status:

```text
Inbox → Ready → In progress → Review → Done
                    └──────→ Blocked
```

Автоматизация:

- новый, reopened или transferred issue → `Inbox`;
- открытый или reopened PR → `Review`;
- закрытый issue или merged PR → `Done`.

`Ready`, `In progress` и `Blocked` меняет владелец или агент по фактическому состоянию работы.
`Priority` — `Now`, `Next`, `Later`; `Area` — `Product`, `Platform`, `Landing`, `Operations`.

Readiness labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.
Category labels `bug` и `enhancement` не заменяют readiness status.

## CI

- Workspace: harness unit tests, `health` и `diff` на каждый PR и push в `main`.
- Landing: install, verify и production build.
- Platform: application CI появится после выбора stack и реальных команд.

Branch protection одинаково включить бесплатно нельзя, пока Workspace и Platform приватные.
Поэтому merge защищён процессом: только PR, проверки и явное разрешение владельца.

## Версии harness

Version tag вида `inside-engineering-vX.Y.Z` обязателен: он фиксирует точный Workspace commit и
используется для rollback. GitHub Release необязателен; текущий installer ничего из него не
скачивает.

Обновление:

1. Изменить canonical package в Workspace.
2. Обновить package version.
3. Запустить tests, `health` и `diff`.
4. После разрешения владельца смержить и создать tag.
5. Выполнить `update` для Landing и Platform отдельными reviewable изменениями.

## Роль владельца

Владелец принимает product и visual decisions, утверждает необратимые ADR, testing seams и ticket
breakdown, разрешает внешние рискованные действия и каждый merge. Агент самостоятельно выполняет
готовую задачу внутри подтверждённых границ.
