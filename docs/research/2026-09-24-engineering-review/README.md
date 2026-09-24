# Инженерное ревью Sachkov Inside — 2026-09-24

Сводка семи независимых проверок, выполненных только чтением: код, конфиги, история CI и
GitHub Projects. Код, issues и Project fields не менялись. Снимки: platform `6ce6b22f`,
telegram `9a2a4e5`, landing `f227684`; GitHub — 24.09 около 14:20 UTC.

Подробные отчёты лежат рядом. Отчёт по безопасности не публикуется: repositories открыты, а часть
находок ещё не исправлена. Он хранится локально у владельца и будет добавлен после исправлений.

| Направление | Файл |
|---|---|
| Архитектура backend и packages platform (по `improve-codebase-architecture`) | [backend.md](backend.md), [architecture-backend.html](architecture-backend.html) |
| Frontend platform и landing | [web.md](web.md) |
| Версии зависимостей, строгость TypeScript, линтинг | [deps-typescript.md](deps-typescript.md) |
| Тесты и CI | [tests-ci.md](tests-ci.md) |
| Telegram целиком | [telegram.md](telegram.md) |
| Доски и Developer Pipeline | [board-pipeline.md](board-pipeline.md) |

## Итог

Основа сильная. В рабочем коде platform ноль `any`, `!` и `ts-ignore`. Слои FSD в web не
нарушены. Авторизация проверяется на всех controllers backend, подписи платежей T-Bank и
идемпотентность корректны. Telegram хранит updates надёжно и использует transactional outbox.
Critical- и High-находок по безопасности нет.

Слабые места в другом: надёжность под нагрузкой, наблюдаемость сбоев, скорость CI и порядок
в очереди задач. Стек почти актуален, но разошёлся между repositories: NestJS 11 и 12,
TypeScript 7 и 6, Node 24 и 22, pnpm и npm.

## Решения владельца 2026-09-24

- Публичность `workspace`, `platform` и `inside-telegram` задумана; `REPOSITORIES.md` исправлен.
- Подтверждение входа в боте остаётся без кода сверки; принятый риск записывается ADR в inside-telegram.
- Merge PR задач программы разрешён заранее после `Ready and Done`; деплой и релиз — отдельно.
- Приоритеты на досках агент расставляет по плану ревью.
- Merge queue в platform, Prettier во всех repositories с кодом, обязательные проверки в inside-telegram.
- Landing устарел с 2026-09-15 и в программу не входит. Выбор шрифта Manrope записан на будущее.

## Задачи

Родительская задача: [workspace#209](https://github.com/sachkov-inside/workspace/issues/209).

| Задача | Приоритет | Зависит от |
|---|---|---|
| [workspace#210](https://github.com/sachkov-inside/workspace/issues/210) Порядок на досках и в документах | Now | — |
| [workspace#211](https://github.com/sachkov-inside/workspace/issues/211) Harness 0.4.8: приёмка, actions по SHA, health в CI | Now | — |
| [platform#688](https://github.com/sachkov-inside/platform/issues/688) Укрепление защиты platform | Now | — |
| [platform#689](https://github.com/sachkov-inside/platform/issues/689) Атомарное сохранение материала | Now | — |
| [platform#691](https://github.com/sachkov-inside/platform/issues/691) CI за 6 минут, merge queue | Now | — |
| [platform#692](https://github.com/sachkov-inside/platform/issues/692) Web: мигание, LCP, страницы ошибок | Now | — |
| [platform#690](https://github.com/sachkov-inside/platform/issues/690) Сбои зависимостей видны в логе | Next | лучше после #689 |
| [platform#693](https://github.com/sachkov-inside/platform/issues/693) Актуальный стек, строгий tsconfig, Prettier | Next | #691 |
| [platform#694](https://github.com/sachkov-inside/platform/issues/694) Строгие правила линта | Later | #693 |
| [platform#695](https://github.com/sachkov-inside/platform/issues/695) Interface Materials и сборка Guide | Later | #689, #690 |
| [inside-telegram#80](https://github.com/sachkov-inside/inside-telegram/issues/80) Конфигурация бота и ADR о входе | Now | — |
| [inside-telegram#81](https://github.com/sachkov-inside/inside-telegram/issues/81) Воронки не блокируют `/start` | Now | — |
| [inside-telegram#82](https://github.com/sachkov-inside/inside-telegram/issues/82) Надёжность при деплое и сбоях | Next | #81 |
| [inside-telegram#83](https://github.com/sachkov-inside/inside-telegram/issues/83) Модули-владельцы и state machine автора | Later | #82 |
| [inside-telegram#84](https://github.com/sachkov-inside/inside-telegram/issues/84) Актуальный стек и гейт CI | Later | #83 |

## Приоритеты

### Сейчас: риски для людей и денег, небольшие правки

| # | Что | Repository | Источник | Трудоёмкость |
|---|---|---|---|---|
| 1 | Укрепить конфигурацию бота | telegram | security | S |
| 2 | Закрепить сторонние actions по SHA | все | security | S |
| 3 | Обновить зависимости с предупреждениями audit, заголовки защиты | platform | security | S |
| 4 | Исправить дубль ADR 0026 и добавить `inside-harness health` в CI platform | platform | board H3 | S |
| 5 | Транзакция `save-material`: `markUnreferenced` открывает свою транзакцию и не откатывается вместе с save | platform | backend H2 | M |
| 6 | Не сбрасывать статус входа при возврате во вкладку: личные блоки мигают | platform web | web H1 | S |
| 7 | Разобрать очередь: Priority и Area у 23 открытых issue, хотя бы одна `Now` | доски | board H1 | S |

### Далее: надёжность, скорость CI, наблюдаемость

- **Наблюдаемость сбоев.** В backend platform 176 пустых `catch`, в telegram 53. Нет logger
  и request id, а причина ошибки теряется. Нужен один module для сбоя зависимости, который записывает
  причину и возвращает вариант union (кандидат 1 в HTML-отчёте).
- **Планировщик воронок telegram.** Под глобальной блокировкой он пересчитывает всех
  получателей через N+1 запросы. Первая большая рассылка остановит `/start`, вход и привязку.
  Нужно исправить до включения маркетинговых рассылок.
- **Именованные ключи блокировок** вместо совпадения строки `hashtextextended(materialId)`
  в трёх модулях (backend H3).
- **CI platform.** Разбить `pnpm check` на параллельные jobs. Для integration-тестов один раз
  мигрировать шаблон базы. Вынести тесты брокера в последовательный набор, это лечит
  flake `notification-transport`. Выключить rebase у Dependabot. Цель — около 5–6 минут вместо 10.
- **Гейт в telegram.** Сейчас там нет ни branch protection, ни обязательных проверок.
- **Web.** Приоритет загрузки обложки первого экрана, `not-found`/`global-error`, сбор
  Core Web Vitals с реальных посещений.

### Потом: единый современный стек и максимальная строгость

Порядок взят из [deps-typescript.md](deps-typescript.md#5-план-обновлений-по-порядку):

1. Все patch/minor, Node 24.21.0 и pnpm 11.27.1 в platform и telegram.
2. Общий `tsconfig.base.json` с бесплатными флагами. `verbatimModuleSyntax`, `isolatedModules`
   и `noUnusedLocals/Parameters` дают всего 1 ошибку. `packages/legal` и
   `packages/access-capabilities` добавить под type-aware lint.
3. NestJS 12 в platform. `@nestjs/swagger` 12 требует TS ≤ 6, а в platform TS 7 и strict peers.
   Нужен `peerDependencyRules`, swagger обновляется только вместе с core. Отдельно amqplib 2.
4. Telegram: сначала линт на oxlint + tsgolint (typescript-eslint не пускает TS 7),
   потом убрать 146 `!` в `communications`, затем TS 7 и `exactOptionalPropertyTypes`.
5. Landing устарел: находки по нему в [web.md](web.md) сохраняются на случай возврата.
6. Строгие правила линта по одному на PR: `no-unsafe-type-assertion` в web (72),
   `no-unnecessary-condition` (68), `strict-boolean-expressions` (277), затем
   `noPropertyAccessFromIndexSignature` (743, механически).
7. vitest 5 во всех repositories сразу, затем pnpm 12; Node 26 LTS после выхода в конце октября.

Архитектурные углубления (подробно в HTML-отчёте и [telegram.md](telegram.md)):
- **platform:** единый interface изменения ссылок Material. Оно берёт транзакцию вызывающего
  и именованный ключ блокировки. Сузить экспорт Materials: 106 из 188 символов не
  используются снаружи. Разбить `assembleGuideArtifacts` на 847 строк.
- **telegram:** один module для durable-очередей в PostgreSQL (сейчас 7 копий); модули-владельцы
  для reply outbox и PlatformLink; типизированная state machine автора.
