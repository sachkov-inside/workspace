# План организации разработки Sachkov Inside

Статус: рабочий план, 2026-08-19. Решения из следующих этапов подтверждаются владельцем перед
реализацией.

Конкретные задачи, порядок и критерии готовности вынесены в
[`ORGANIZATION-BACKLOG.md`](ORGANIZATION-BACKLOG.md).

## Цель

Сначала привести в порядок repositories и управление работой, затем последовательно определить
продуктовые и технические границы Platform. Не выбирать stack и не создавать application scaffold,
пока не понятны задачи первой версии.

## Текущее состояние

- Активная topology: `workspace`, `inside-landing`, `platform`. Существующий `telegram-bot` не
  входит в текущий план и не показывается в Workspace.
- Общий product harness `inside-engineering 0.2.0` установлен во все три активных repositories.
- В Workspace уже используются GitHub Issues и есть product map
  [`workspace#1`](https://github.com/sachkov-inside/workspace/issues/1).
- У Landing и Platform пока нет issues. Organization-level GitHub Project ещё не создан.
- Базовый harness опубликован в отдельных branches; merge и release tag ещё не выполнены.

## Целевая модель

```text
GitHub Project: Inside
  ├─ общий обзор всех текущих issues и pull requests
  │
  ├─ workspace issues
  │    └─ продукт, исследования, решения и cross-repo initiatives
  │
  ├─ inside-landing issues
  │    └─ работа, результат которой принадлежит Landing
  │
  └─ platform issues
       └─ работа, результат которой принадлежит Platform

Каждый repository
  ├─ собственные branches, pull requests, CI и releases
  ├─ общая управляемая копия product harness
  └─ собственные AGENTS.md, команды и repo-specific skills
```

Issue хранится в repository, который владеет результатом. GitHub Project только агрегирует работу
и не становится новым источником требований. Workspace не превращается в центральный backlog для
всех code changes.

## Этап 0. Завершить rollout базового harness

1. Проверить и merge Workspace PR
   [`#16`](https://github.com/sachkov-inside/workspace/pull/16).
2. Создать и проверить PR из `chore/install-inside-product-harness` в Landing.
3. Создать и проверить PR из `chore/install-inside-product-harness` в Platform.
4. После merge Workspace создать первый release tag общего harness.
5. Ещё раз выполнить `inside-harness health` для всех repositories из состояния их `main`.

Готово, когда все три `main` содержат согласованную версию harness, рабочие деревья чистые, а
повторный `update` не создаёт diff.

## Этап 1. Зафиксировать правила repositories

1. Подтвердить назначение, visibility и владельца каждого активного repository.
2. Зафиксировать простое правило branches: одна содержательная задача — одна branch — один PR.
3. Зафиксировать, где живут документы:
   - продуктовые и cross-repo решения — в Workspace;
   - ADR и технические решения конкретного приложения — в его repository;
   - временное обсуждение — в issue, подтверждённое решение — в versioned document.
4. Определить минимальный PR contract: ссылка на issue, понятный результат, выполненные проверки,
   явно перечисленное `Not tested`.
5. Добавлять repo-specific команды и инструкции в harness конкретного repository только после
   появления реальных build, test, run и deploy workflows.

Готово, когда для любой новой работы однозначно понятно, в каком repository создать issue и где
сохранить итоговое решение.

## Этап 2. Настроить task tracker

Рекомендация: использовать GitHub Issues и один organization-level GitHub Project `Inside`. Новый
платный сервис или отдельный tracker repository не нужны.

Минимальные поля Project:

- `Status`: Inbox, Ready, In progress, Review, Blocked, Done;
- `Priority`: Now, Next, Later;
- `Area`: Product, Platform, Landing, Operations.

Минимальные views:

- `Current` — board активной работы;
- `Roadmap` — Now / Next / Later;
- `By repository` — проверка распределения работы.

Правила tracker:

1. Product discovery, owner decisions и cross-repo initiatives создаются в Workspace.
2. Implementation, bugs и технический долг создаются в repository, где меняется продукт.
3. Cross-repo initiative имеет parent issue в Workspace и repo-local sub-issues.
4. `Status` хранится в Project, а не одновременно в Project и workflow labels.
5. Labels описывают тип работы и режим исполнения: decision, research, feature, task, bug, HITL или
   agent-ready. Набор labels должен быть одинаковым и небольшим во всех repositories.
6. Документ и issue не дублируют друг друга: issue управляет работой, документ хранит устойчивое
   знание и принятое решение.
7. В Project попадает только сформулированная работа. Сырые идеи остаются в Inbox без детализации
   до момента, когда они действительно нужны.

Первый rollout tracker:

1. Создать Project и три views.
2. Добавить существующие Workspace issues `#1`, `#4`, `#5`, `#6`, `#7`.
3. Перенести их текущий workflow в поле `Status`.
4. Проверить один cross-repo пример через parent issue и sub-issue, не создавая большой backlog.
5. После недельного использования удалить поля, labels или views, которые не помогают принимать
   решения.

Готово, когда каждая активная задача существует ровно один раз, видна в общем обзоре и при этом
принадлежит правильному repository.

## Этап 3. Зафиксировать рабочий lifecycle задачи

Для содержательной разработки использовать одну последовательность:

```text
idea / problem
  → issue или questionnaire
  → подтверждённая граница
  → spec при необходимости
  → repo-local implementation issue
  → branch и PR
  → review и проверки
  → merge по решению владельца
  → обновление durable docs, если изменилось решение
```

До начала implementation у задачи должны быть понятны результат, границы, acceptance criteria и
необходимость owner decision. Не каждая небольшая правка требует отдельного большого spec.

## Этап 4. Провести product discovery Platform

Вопросы разбираются последовательно, по одному блоку, без преждевременного выбора технологий:

1. Какой контент переносим из Telegram в первую очередь и в каких форматах он существует.
2. Какие роли есть в первой версии: anonymous visitor, free user, member, author/admin.
3. Что видит каждая роль и как выглядит граница бесплатного и закрытого контента.
4. Какова минимальная content model: материал, серия, тема, уровень, автор, вложение, visibility.
5. Какие сценарии обязательны: каталог, чтение, поиск, фильтры, прогресс и авторское управление.
6. Как проходит постепенная миграция из Telegram и какой manual workflow допустим на старте.
7. Какие ограничения важны: объём контента, медиа, SEO, privacy, backup, стоимость и нагрузка.

Результат этапа — подтверждённый Platform MVP brief, словарь домена, список user flows и открытых
вопросов. Будущие активности, задания и community-функции остаются за границей MVP, но модель не
должна делать их невозможными.

## Этап 5. Принять технические решения

Только после product discovery сравнить варианты и записать ADR для решений, которые дорого
менять:

1. application architecture и границы модулей;
2. frontend/backend stack и repository layout;
3. authentication, membership access и роли;
4. content storage, editing и импорт из Telegram;
5. search и индексация;
6. файлы и media storage;
7. hosting, database, CI/CD, observability и backups;
8. privacy и security boundaries.

Неясные или рискованные варианты сначала проверяются маленьким throwaway prototype. Все решения
должны укладываться в бесплатный стартовый режим; платный компонент требует отдельного решения
владельца.

Готово, когда выбранный stack объясняется требованиями MVP, основные риски проверены и можно
сформировать первый implementation milestone.

## Этап 6. Начать Platform с вертикального среза

1. Обновить repo-specific `AGENTS.md` реальными командами и Definition of Done.
2. Создать минимальный application skeleton и CI.
3. Реализовать один end-to-end сценарий, который проверяет основные границы системы.
4. После вертикального среза разложить следующий milestone на небольшие repo-local issues.
5. Не переносить весь Telegram-контент, пока import и content model не подтверждены на небольшой
   выборке.

Предпочтительный первый срез определяется после discovery. Предварительный кандидат: публичная
карточка материала → закрытый материал участника → поиск по доступному контенту → минимальное
авторское создание или импорт.

## Ближайшая последовательность

1. Завершить PR и release базового harness.
2. Подтвердить модель GitHub Project и настроить tracker.
3. Зафиксировать repository и task lifecycle в коротких project instructions.
4. Начать product discovery Platform вопросами по контенту и ролям.
5. После подтверждённого MVP перейти к stack и архитектуре.
