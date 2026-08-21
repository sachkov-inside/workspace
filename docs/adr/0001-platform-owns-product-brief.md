---
status: accepted
---

# Platform владеет своим продуктовым brief

Workspace владеет общей продуктовой картиной и cross-repository решениями, а Platform владеет
единственным каноническим `docs/product/platform-mvp-brief.md`. Git history и Platform pull requests
дают versioning, provenance и review в том же repository, где brief используется; Workspace хранит
ссылку вместо копии.

## Рассмотренные варианты

Git snapshot с manifest, checksums и exporter был реализован первым, но оказался shallow module
для одного документа и одного consumer: большая часть сложности исчезает при переносе authority в
Platform. Wiki или центральный portal могут индексировать документацию, но не становятся второй
authority. Symlink, submodule и runtime-чтение соседнего checkout по-прежнему нарушают автономность.

## Последствия

Platform-specific product scope меняется через Platform issue и PR. Если изменение затрагивает
несколько repositories, решение сначала принимается в Workspace, после чего owning repository
обновляет свой канонический документ. Distribution contract появится только при нескольких реальных
consumer или требовании независимых versioned releases.
