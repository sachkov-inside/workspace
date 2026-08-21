# Repositories Sachkov Inside

Проверено: 2026-08-21.

| Repository | Owner | Local path | Visibility | Назначение |
|---|---|---|---|---|
| [`sachkov-inside/workspace`](https://github.com/sachkov-inside/workspace) | `sachkov-inside` | `.` | private | Общий product context, Developer Pipeline и cross-repo решения |
| [`sachkov-inside/inside-landing`](https://github.com/sachkov-inside/inside-landing) | `sachkov-inside` | `repositories/landing` | public | Публичный landing Inside |
| [`sachkov-inside/platform`](https://github.com/sachkov-inside/platform) | `sachkov-inside` | `repositories/platform` | private | Membership-платформа и её product/technical docs |

Owner decision от 2026-08-21 добавляет в target topology отдельный private repository и deployable
для Telegram-бота. Рабочее имя — `sachkov-inside/inside-telegram`; repository ещё не создан и
должен пройти отдельный bootstrap с собственным harness, ADR, build, tests, migrations, secrets и
deployment. Текущая техническая рекомендация и proof gates описаны в
[`platform-telegram-tribute-membership.md`](docs/research/platform-telegram-tribute-membership.md);
её application-specific часть должна стать ADR уже в новом repository. До bootstrap имя остаётся
открытым, а runtime-зависимость от несуществующего checkout не допускается.

## Правила границ

- Новые repositories создаются в организации `sachkov-inside` и по умолчанию имеют private
  visibility.
- Участники организации получают базовый read-доступ к private repositories через organization
  base permission.
- `repositories/` является только локальным размещением checkout. Root Git его игнорирует.
- Каждый repository собирается, тестируется и деплоится самостоятельно.
- Repository-specific product brief хранится один раз в repository, который владеет этой product
  surface; Workspace индексирует его ссылкой.
- Machine-local пути, symlinks на workspace и runtime imports из соседних repositories не являются
  допустимыми зависимостями.
- Общий product harness устанавливается из canonical source Workspace как versioned project-local
  copy; lifecycle описан в [`HARNESS.md`](HARNESS.md).
- Общий harness не меняет user-level settings. Repo-specific harness развивается внутри своего
  repository независимо.
