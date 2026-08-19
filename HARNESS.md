# Harness Sachkov Inside

Текущая версия: `inside-engineering 0.2.0`. Canonical source выпускается tag
`inside-engineering-v0.2.0` и устанавливается в Workspace, Landing и Platform.

## Итоговая модель

У harness три независимых уровня:

```text
Устройство
  └─ native runtime + минимальный personal profile; project capabilities не предполагаются

Inside Workspace
  └─ canonical source общего product harness
       ├─ installer и проверки
       ├─ inside-engineering 0.2.0
       └─ adapters общих instructions
            │
            ├─ install/update → Workspace repository
            ├─ install/update → platform repository
            └─ install/update → landing repository

Каждый repository
  ├─ управляемая копия общего product harness
  └─ собственные instructions, skills, MCP/hooks при необходимости, build/test/run/deploy
```

Workspace является единственным местом, где редактируется общий набор. Установленные копии
коммитятся в каждый repository, поэтому repository работает автономно: без соседнего Workspace,
абсолютных machine-local путей, symlinks и предположений о user-level skills/MCP/plugins/hooks.

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
│       ├── SOURCE.md
│       ├── LICENSE
│       └── skills/
└── tests/
```

`inside-engineering 0.2.0` содержит 32 skills: полный stable-набор Matt Pocock из 25 skills и 7
общих frontend/web skills (`frontend-design`, `impeccable`, `karpathy-guidelines`,
`modern-web-guidance`, `playwright-cli`, `vercel-react-best-practices`,
`web-design-guidelines`). `in-progress` и `misc` Matt Pocock не импортированы. Источники и условия
лицензирования зафиксированы в package metadata и `SOURCE.md`.

В каждом repository installer создаёт:

```text
.agents/skills/                         # Codex, Kimi Code, OpenCode
.claude/skills/                         # Claude Code
.inside-harness/product-harness.json    # package и установленная версия
AGENTS.md                               # общий entrypoint + repo-specific правила
CLAUDE.md                               # импорт AGENTS.md
```

Обе runtime-директории являются управляемыми копиями одного package. Repo-specific skills можно
добавлять рядом с ними под уникальными именами. После переноса frontend-набора у Landing остаётся
один локальный skill: `add-reference`.

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

- управляет только именами из package manifest и собственными blocks в entrypoints;
- сохраняет неизвестные repo-specific skills и unrelated settings;
- останавливается при конфликте или изменённом managed-файле; незакоммиченная установка принимает
  только новые skill-имена из следующей версии package;
- оставляет обычный reviewable Git diff;
- повторяет no-op установку идемпотентно;
- не изменяет user-level settings.

Rollback читает package и adapters из выбранного Git ref Workspace. Он станет доступен после
первого commit/release, содержащего текущую структуру harness.

## Как обновлять общий pipeline

1. Изменить canonical package в Workspace.
2. Обновить `manifest.json` и provenance, если изменился upstream.
3. Запустить unit tests.
4. Обновить один pilot repository, проверить `diff`, `health` и native discovery.
5. После подтверждения владельца закоммитить Workspace и создать release tag.
6. Обновить остальные repositories отдельными reviewable changes.

Upstream не обновляется автоматически. User-level profiles, MCP, hooks и автоматические runtime
changes в product harness не входят. Если integration становится recurring, она добавляется в
конкретный repository через native project config и проверяется его `health`; credentials остаются
в native auth или environment.
