# Repositories Sachkov Inside

Проверено: 2026-08-19.

| Repository | Owner | Local path | Visibility | Назначение |
|---|---|---|---|---|
| [`sachkov-inside/workspace`](https://github.com/sachkov-inside/workspace) | `sachkov-inside` | `.` | private | Product docs, Developer Pipeline и cross-repo решения |
| [`sachkov-inside/inside-landing`](https://github.com/sachkov-inside/inside-landing) | `sachkov-inside` | `repositories/landing` | public | Публичный landing Inside |
| [`sachkov-inside/platform`](https://github.com/sachkov-inside/platform) | `sachkov-inside` | `repositories/platform` | private | Membership-платформа |

В организации нет repository `telegram-bot`. Это направление не входит в активную topology;
repository для него не создаётся и не резервируется до отдельного owner decision.

## Правила границ

- Новые repositories создаются в организации `sachkov-inside` и по умолчанию имеют private
  visibility.
- Участники организации получают базовый read-доступ к private repositories через organization
  base permission.
- `repositories/` является только локальным размещением checkout. Root Git его игнорирует.
- Каждый repository собирается, тестируется и деплоится самостоятельно.
- Machine-local пути, symlinks на workspace и runtime imports из соседних repositories не являются
  допустимыми зависимостями.
- Общий product harness устанавливается из canonical source Workspace как versioned project-local
  copy; lifecycle описан в [`HARNESS.md`](HARNESS.md).
- Общий harness не меняет user-level settings. Repo-specific harness развивается внутри своего
  repository независимо.
