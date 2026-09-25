# Harness Sachkov Inside

Canonical package `inside-engineering` распространяется в Workspace, Platform, Telegram и Workshop
Cases через явный rollout lifecycle ниже. Landing устарел с 2026-09-15: его установленная копия
не обновляется, раскатка туда не ведётся. Точное содержимое и версия принадлежат package manifest,
а не этому описанию.

## Итоговая модель

У harness три независимых уровня:

```text
Устройство
  └─ native runtime + минимальный personal profile; project capabilities не предполагаются

Inside Workspace
  └─ canonical source общего product harness
       ├─ installer и проверки
       ├─ inside-engineering package
       └─ adapters общих instructions
            │
            ├─ install/update → Workspace repository
            ├─ install/update → platform repository
            ├─ install/update → telegram repository
            ├─ install/update → workshop-cases repository
            └─ landing repository (устарел, раскатка не ведётся)

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
│   ├── inside-harness
│   └── harness-rollout
├── rollout-targets.json
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

Package содержит общий Developer Pipeline с review closure, architecture fitness и pruning,
triage labels, lifecycle script для автоматического закрытия completed parent issues и два skill
profile. `core` содержит stable-набор Matt Pocock и `karpathy-guidelines`; `frontend` добавляет
`impeccable`, `modern-web-guidance`, `playwright-cli` и `vercel-react-best-practices`.
`in-progress` и `misc` Matt Pocock не импортированы. Точный состав и provenance зафиксированы в
package metadata и `SOURCE.md`.

В каждом repository installer создаёт:

```text
.inside-harness/skills/                 # единственный physical snapshot + REGISTRY.md
.agents/skills -> ../.inside-harness/skills
.claude/skills -> ../.inside-harness/skills
.inside-harness/product-harness.json    # package, версия и managed skill names
.inside-harness/integrations.json       # repository-owned native integration inventory, если нужен
AGENTS.md                               # общий entrypoint + repo-specific правила
CLAUDE.md                               # импорт AGENTS.md
WORKFLOW.md                             # общий Developer Pipeline
docs/agents/triage-labels.md            # общие readiness-роли
.github/workflows/inside-harness-health.yml  # health в CI по тегу установленной версии
```

Остальные managed-файлы (трекер, шаблон PR, `.github/scripts/.gitignore`) перечислены в package
manifest. Сторонние actions в managed workflows закреплены полным SHA коммита с комментарием
версии; проверка пакета в `health` отклоняет плавающий тег.

Обе runtime-директории ведут в один committed snapshot. Это устраняет двойные копии и неоднозначный
OpenCode discovery. Repo-specific skills можно добавлять в snapshot под уникальными именами; они
не входят в `managedSkills` package state. Workspace, Telegram и Workshop Cases используют `core`;
Platform и устаревший Landing — `frontend`. У Landing дополнительно остаётся локальный skill
`add-reference`.

## Рабочий цикл

Команды запускаются из корня Workspace:

```bash
harness/bin/inside-harness install <repository> --profile core|frontend
harness/bin/inside-harness update <repository> [--profile core|frontend]
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

После первой установки profile хранится в state; `update`, `diff` и `rollback` используют его без
повторного флага. Если repository содержит native Codex/Claude/Cursor/MCP config, `health` требует
`.inside-harness/integrations.json` с точным path, SHA-256, runtime ownership, verification command
и именами secret environment variables. Inventory не хранит credentials и не запускает внешнюю
интеграцию автоматически.

Rollback читает package и adapters из выбранного Git ref Workspace. Он станет доступен после
первого commit/release, содержащего текущую структуру harness.

## Как обновлять общий product harness

1. Изменить canonical package в Workspace.
2. Обновить `manifest.json` и provenance, если изменился upstream.
3. Запустить unit tests.
4. Обновить один pilot repository локально, проверить `diff`, `health` и native discovery.
5. После подтверждения владельца закоммитить Workspace и создать release tag
   `inside-engineering-v<version>` на merge-коммите.
6. Раскатать версию. Тег запускает workflow `Harness rollout`: для каждого repository из
   `harness/rollout-targets.json` он выполняет `update` и открывает один PR
   `chore/harness-<version>` или отмечает repository как актуальный. PR проходит CI repository и ждёт
   merge владельца. Без секрета `HARNESS_ROLLOUT_TOKEN` workflow сообщает, что раскатка
   заблокирована, и PR раскатки открываются вручную отдельными reviewable changes.

Version tag обязателен: он связывает package-версию с точным Workspace commit и служит стабильным
Git ref для rollback. CI каждого repository кроме Workspace проверяет `health` по тегу своей
установленной версии, поэтому PR раскатки открывается только после публикации тега. GitHub Release
необязателен и создаётся только когда нужны отдельные release notes или downloadable assets. Текущий
installer не скачивает GitHub Release: `update` читает canonical package из Workspace, а
`rollback --to` — из указанного Workspace Git ref.

Upstream не обновляется автоматически; автоматизирована только раскатка выпуска. User-level profiles, MCP, hooks и автоматические runtime
changes в product harness не входят. Если integration становится recurring, она добавляется в
конкретный repository через native project config и проверяется его `health`; credentials остаются
в native auth или environment.

Общий delivery lifecycle называется Developer Pipeline и описан в [`WORKFLOW.md`](WORKFLOW.md).
Product harness поставляет composable skills для него, но не владеет GitHub settings, branches,
Project fields или owner-controlled merge policy.
