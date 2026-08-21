# Передача продуктового контекста в Platform

Workspace поставляет Platform один явный contract: Git-tracked snapshot в стабильном каталоге
`docs/product-context/`. Snapshot создаётся из перечисленных в `contract.json` канонических
Workspace-файлов, попадает в Platform только через отдельный reviewable PR и не требует Workspace
для build, test, run или deploy.

## Почему snapshot

Это небольшой interface с высокой locality: Platform знает один каталог и одну проверку, а выбор
источников, provenance, versioning и обнаружение drift остаются внутри Workspace exporter.

Не выбраны:

- symlink, submodule и runtime-чтение соседнего checkout — нарушают автономность и делают
  machine-local topology частью interface;
- package или GitHub Release artifact — добавляют registry, credentials и download lifecycle для
  двух Markdown-файлов, не улучшая review;
- ручная копия без manifest — не фиксирует provenance и не отличает upstream update от локального
  редактирования;
- Git subtree — переносит лишнюю историю и усложняет обновление без дополнительной ценности для
  маленького read-only контракта.

## Минимальный состав v1

Product payload `1.0.0` содержит только consumer guide и `product/platform-mvp-brief.md`; рядом
поставляется локальный verifier. Brief уже самодостаточно фиксирует подтверждённую продуктовую
границу Platform. Research reports и working decisions карты #38 не поставляются: до owner
acceptance они не являются контрактом, а после принятия технические решения должны жить в Platform
specification/application ADR либо, если решение действительно cross-repository, добавляться в
source manifest отдельным осознанным изменением.

Workspace хранит authority один раз:

```text
workspace/
├── product/
│   ├── platform-mvp-brief.md              # canonical product scope
│   └── platform-context/
│       ├── README.md                      # source-side contract and rationale
│       ├── consumer.md                    # source for delivered README
│       ├── contract.json                  # version and explicit source allowlist
│       ├── manage.py                      # render and upstream drift check
│       └── verify_snapshot.py             # delivered local integrity check
└── docs/adr/
    └── 0001-versioned-platform-product-context.md
```

Первый Platform bootstrap PR создаст только локальный consumer snapshot:

```text
platform/
├── AGENTS.md                              # links to docs/product-context/README.md
├── docs/product-context/
│   ├── README.md
│   ├── manifest.json
│   ├── checksums.sha256
│   ├── verify.py
│   └── platform-mvp-brief.md
└── ...                                    # autonomous application and toolchain
```

`manifest.json` содержит `schemaVersion`, SemVer `version`, source repository, полный source commit
и для каждого файла source path, target path и SHA-256. Время генерации намеренно не включается,
поэтому один source commit даёт воспроизводимый snapshot.

## Operation

[`consumer.md`](consumer.md) — единственный operator runbook для render, local verification,
upstream drift check, version bump и явного Platform update. Он входит в snapshot как `README.md`,
поэтому source и consumer читают одни инструкции, а изменение процесса делается в одном месте.

## Platform handoff

Application layout, toolchain, commands, CI и local environment принадлежат Platform repository.
Они заданы в готовой Platform task
[`sachkov-inside/platform#10`](https://github.com/sachkov-inside/platform/issues/10), а
hard-to-reverse application choices после owner GO фиксируются в Platform ADR. Workspace contract
определяет только способ доставки подтверждённого product context и не становится источником
application architecture.
