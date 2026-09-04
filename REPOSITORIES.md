# Repositories Sachkov Inside

Проверено: 2026-09-03.

| Repository | Owner | Local path | Visibility | Назначение |
|---|---|---|---|---|
| [`sachkov-inside/workspace`](https://github.com/sachkov-inside/workspace) | `sachkov-inside` | `.` | private | Общий product context, Developer Pipeline и cross-repo решения |
| [`sachkov-inside/inside-landing`](https://github.com/sachkov-inside/inside-landing) | `sachkov-inside` | `repositories/landing` | public | Публичный landing Inside |
| [`sachkov-inside/platform`](https://github.com/sachkov-inside/platform) | `sachkov-inside` | `repositories/platform` | private | Membership-платформа и её product/technical docs |
| [`sachkov-inside/workshop-cases`](https://github.com/sachkov-inside/workshop-cases) | `sachkov-inside` | `repositories/workshop-cases` | private | Закрытый authoring source для versioned Production Cases |
| [`sachkov-inside/inside-telegram`](https://github.com/sachkov-inside/inside-telegram) | `sachkov-inside` | `repositories/telegram` | private | Telegram BotContact, identity linking и Membership Evidence provider |

Owner decision от 2026-09-03 зафиксировал отдельный private repository
`sachkov-inside/workshop-cases`. Он хранит CaseSpec, starter baselines, author solutions и evaluator
bundles. Platform импортирует только точный commit и выпускает участнику выбранный starter;
участники не получают доступ к authoring repository или защищённому solution content. Repository
не является deployable application или runtime backend. Граница и поставка первого кейса описаны
в [Production Workshop V1](https://github.com/sachkov-inside/platform/blob/main/docs/specifications/production-workshop-v1.md)
и [Platform #261](https://github.com/sachkov-inside/platform/issues/261).

Owner decision от 2026-08-30 зафиксировал отдельный private repository и dedicated bot direction
`Sachkov Inside`. Repository создан и владеет собственными product brief, root Specification,
application decisions, build/tests/migrations и будущим deploy. Его подтверждённая граница описана
в [Telegram application brief](https://github.com/sachkov-inside/inside-telegram/blob/main/docs/product/telegram-application-brief.md),
а delivery — в [Telegram Specification #1](https://github.com/sachkov-inside/inside-telegram/issues/1).
Workspace не становится runtime или build dependency нового application.

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
