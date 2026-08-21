---
status: proposed
---

# Передавать продуктовый контекст Platform как проверяемый Git snapshot

Workspace остаётся authority продуктовых и cross-repository решений, а Platform получает их
явным Git-tracked snapshot в `docs/product-context/` с SemVer, source commit и SHA-256. Snapshot
обновляется только отдельным Platform PR: такой seam оставляет build, test, run и deploy Platform
автономными, делает provenance и drift проверяемыми и не вводит registry, runtime import или
machine-local dependency ради небольшого read-only контракта.

## Рассмотренные варианты

Symlink, submodule и чтение соседнего checkout отвергнуты как зависимость от topology. Package или
release artifact отвергнуты как лишний distribution/credentials lifecycle. Git subtree переносит
лишнюю историю, а ручная копия без manifest теряет provenance. Snapshot намеренно дублирует
доставленное содержимое между repositories, но authority остаётся только в Workspace.

## Последствия

Platform может отставать от Workspace, и это допустимое видимое состояние: checksum/check команда
обнаруживает расхождение, но никогда не исправляет его скрыто. Каждое принятое upstream-изменение
требует повышения contract version, review impact и отдельного downstream merge.
