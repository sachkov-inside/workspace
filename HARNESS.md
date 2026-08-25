# Harness Sachkov Inside

Текущая package-версия — `inside-engineering 0.3.8`; её canonical release boundary — tag
`inside-engineering-v0.3.8`. Package распространяется в Workspace, Landing и Platform через
явный rollout lifecycle ниже.

## Итоговая модель

У harness три независимых уровня:

```text
Устройство
  └─ native runtime + минимальный personal profile; project capabilities не предполагаются

Inside Workspace
  └─ canonical source общего product harness
       ├─ installer и проверки
       ├─ inside-engineering 0.3.8
       └─ adapters общих instructions
            │
            ├─ install/update → Workspace repository
            ├─ install/update → platform repository
            └─ install/update → landing repository

Каждый repository
  ├─ управляемая копия общего product harness
  └─ собственные instructions, skills, MCP/hooks при необходимости, build/test/run/deploy
```

Workspace является единственным местом, где редактируется общий набор. Установленный snapshot и
его repository-relative discovery links коммитятся в каждый repository, поэтому repository
работает автономно: без соседнего Workspace, абсолютных machine-local путей и предположений о
user-level skills/MCP/plugins/hooks.

## Что реализовано

Canonical source находится в [`harness/`](harness/):

```text
harness/
├── adapters/
│   ├── AGENTS.product.md
│   └── CLAUDE.product.md
├── bin/
│   └── inside-harness
├── packages/
│   └── inside-engineering/
│       ├── manifest.json
│       ├── WORKFLOW.md
│       ├── docs/agents/triage-labels.md
│       ├── SOURCE.md
│       ├── LICENSE
│       └── skills/
└── tests/
```

`inside-engineering 0.3.8` содержит общий Developer Pipeline с review closure, architecture fitness
и pruning, triage labels, lifecycle script для автоматического закрытия completed parent issues и
32 skills: полный
stable-набор Matt Pocock из 25 skills и 7 общих frontend/web skills (`frontend-design`,
`impeccable`, `karpathy-guidelines`,
`modern-web-guidance`, `playwright-cli`, `vercel-react-best-practices`,
`web-design-guidelines`). `in-progress` и `misc` Matt Pocock не импортированы. Источники и условия
лицензирования зафиксированы в package metadata и `SOURCE.md`.

В каждом repository installer создаёт:

```text
.inside-harness/skills/                 # единственный physical snapshot + REGISTRY.md
.agents/skills -> ../.inside-harness/skills
.claude/skills -> ../.inside-harness/skills
.inside-harness/product-harness.json    # package, версия и managed skill names
AGENTS.md                               # общий entrypoint + repo-specific правила
CLAUDE.md                               # импорт AGENTS.md
WORKFLOW.md                             # общий Developer Pipeline
docs/agents/triage-labels.md            # общие readiness-роли
```

Обе runtime-директории ведут в один committed snapshot. Это устраняет двойные копии и неоднозначный
OpenCode discovery. Repo-specific skills можно добавлять в snapshot под уникальными именами; они
не входят в `managedSkills` package state. После переноса frontend-набора у Landing остаётся один
локальный skill: `add-reference`.

## Рабочий цикл

Команды запускаются из корня Workspace:

```bash
harness/bin/inside-harness install <repository>
harness/bin/inside-harness update <repository>
harness/bin/inside-harness diff <repository>
harness/bin/inside-harness health <repository>
harness/bin/inside-harness rollback <repository> --to <workspace-git-ref>
```

Первичная миграция существующих одноимённых skills требует явного `--adopt-existing`. Installer:

- управляет только skills и files из package manifest и собственными blocks в entrypoints;
- сохраняет неизвестные repo-specific skills и unrelated settings;
- останавливается при конфликте или изменённом managed-файле; незакоммиченная установка принимает
  только новые skill-имена из следующей версии package;
- оставляет обычный reviewable Git diff;
- повторяет no-op установку идемпотентно;
- не изменяет user-level settings.

Rollback читает package и adapters из выбранного Git ref Workspace. Он станет доступен после
первого commit/release, содержащего текущую структуру harness.

## Как обновлять общий product harness

1. Изменить canonical package в Workspace.
2. Обновить `manifest.json` и provenance, если изменился upstream.
3. Запустить unit tests.
4. Обновить один pilot repository, проверить `diff`, `health` и native discovery.
5. После подтверждения владельца закоммитить Workspace и создать release tag.
6. Обновить остальные repositories отдельными reviewable changes.

Version tag обязателен: он связывает package-версию с точным Workspace commit и служит стабильным
Git ref для rollback. GitHub Release необязателен и создаётся только когда нужны отдельные release
notes или downloadable assets. Текущий installer не скачивает GitHub Release: `update` читает
canonical package из Workspace, а `rollback --to` — из указанного Workspace Git ref.

Upstream не обновляется автоматически. User-level profiles, MCP, hooks и автоматические runtime
changes в product harness не входят. Если integration становится recurring, она добавляется в
конкретный repository через native project config и проверяется его `health`; credentials остаются
в native auth или environment.

Общий delivery lifecycle называется Developer Pipeline и описан в [`WORKFLOW.md`](WORKFLOW.md).
Product harness поставляет composable skills для него, но не владеет GitHub settings, branches,
Project fields или owner-controlled merge policy.
