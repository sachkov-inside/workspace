# Repositories Sachkov Inside

Проверено: 2026-08-19.

| Repository | Local path | Visibility | Назначение |
|---|---|---|---|
| [`sachkov-inside/workspace`](https://github.com/sachkov-inside/workspace) | `.` | private | Product docs, исследования и cross-repo решения |
| [`sachkov-inside/inside-landing`](https://github.com/sachkov-inside/inside-landing) | `repositories/landing` | public | Публичный landing Inside |
| [`sachkov-inside/platform`](https://github.com/sachkov-inside/platform) | `repositories/platform` | private | Membership-платформа |
| [`sachkov-inside/telegram-bot`](https://github.com/sachkov-inside/telegram-bot) | `repositories/telegram-bot` | private | Telegram-интеграция |

## Правила границ

- Новые repositories создаются в организации `sachkov-inside` и по умолчанию имеют private
  visibility.
- Участники организации получают базовый read-доступ к private repositories через organization
  base permission.
- `repositories/` является только локальным размещением checkout. Root Git его игнорирует.
- Каждый repository собирается, тестируется и деплоится самостоятельно.
- Machine-local пути, symlinks на workspace и runtime imports из соседних repositories не являются
  допустимыми зависимостями.
- Общий контекст можно переносить отдельным versioned snapshot или получать через GitHub; точный
  sync contract будет спроектирован позже.
- Harness и agent automation проектируются отдельно после утверждения repository topology.
