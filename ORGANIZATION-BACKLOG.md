# Backlog организации работы Sachkov Inside

Статус: следующий исполнимый план после merge Workspace PR #16, 2026-08-19.

Задачи выполняются по порядку. До завершения блоков P0–P2 не выбираем stack Platform и не создаём
application scaffold.

## Точка старта

- `inside-engineering 0.2.0` выпущен tag `inside-engineering-v0.2.0`.
- Workspace, Landing и Platform содержат release boundary в `main` и проходят `health`/`diff` без
  drift.
- Общий GitHub Project для организации `sachkov-inside` ещё не создан.
- Активные product repositories: `workspace`, `inside-landing`, `platform`.
- `telegram-bot` не входит в текущую topology и backlog.

## P0 — завершить rollout базового harness — выполнено 2026-08-19

Выполнено через Workspace PR #17, Landing PR #2 и Platform PR #2. Release опубликован в
`sachkov-inside/workspace`.

### ORG-01. Создать и проверить PR для Landing

- Repository: `inside-landing`.
- Branch: `chore/install-inside-product-harness` → `main`.
- Проверить diff, `inside-harness health` и отсутствие изменений application source.
- Готово, когда PR одобрен владельцем и смержен.

### ORG-02. Создать и проверить PR для Platform

- Repository: `platform`.
- Branch: `chore/install-inside-product-harness` → `main`.
- Проверить diff и `inside-harness health`.
- Готово, когда PR одобрен владельцем и смержен.

### ORG-03. Выпустить первую версию product harness

- Repository: `workspace`.
- Создать annotated tag `inside-engineering-v0.2.0` на merge commit, содержащем canonical package.
- Коротко описать в GitHub Release: состав package, поддерживаемые runtimes и команды lifecycle.
- Готово, когда tag и release доступны в origin.

### ORG-04. Проверить harness из состояния всех `main`

- Обновить локальные `main` во всех трёх repositories.
- Запустить unit tests Workspace harness.
- Запустить `inside-harness health` и `inside-harness diff` для Workspace, Landing и Platform.
- Удалить локальные и remote feature branches только после подтверждённого merge.
- Готово, когда все проверки проходят, а working trees чистые.

## P1 — зафиксировать правила repositories

### ORG-05. Зафиксировать активную repository topology

- Repository: `workspace`.
- Проверить `REPOSITORIES.md`: назначение, visibility, local path и owner каждого repository.
- Для `telegram-bot` отдельно решить: оставить private inactive или архивировать. Не добавлять его в
  активный Workspace до появления отдельного подтверждённого направления.
- Готово, когда у каждого активного repository одна ясная ответственность.

### ORG-06. Настроить единые repository settings

- Repositories: все активные.
- Default branch: `main`.
- Issues: включены.
- После merge автоматически удалять head branch.
- Оставить один основной merge method для обычной работы: squash merge.
- Проверить доступные на текущем бесплатном плане branch/rules protections и включить только те,
  которые не требуют платного тарифа.
- Готово, когда настройки не отличаются без явной причины.

### ORG-07. Записать Developer Pipeline

- Repository: `workspace`.
- Создать короткий `WORKFLOW.md` со следующими правилами:
  - где создавать product, cross-repo и repo-local issues;
  - одна содержательная задача → одна branch → один PR;
  - branch naming;
  - когда PR требует issue, а trivial docs/chore может идти без него;
  - Definition of Ready и Definition of Done;
  - owner-controlled merge.
- Invocation и steps отдельных skills остаются в самих skills и не пересказываются здесь.
- Готово, когда новый агент может выбрать правильный repository и следующий шаг без догадок.

### ORG-08. Добавить минимальный PR template

- Repositories: все активные.
- Поля: результат, связанный issue when applicable, что проверено, `Not tested`, отдельные owner
  decisions; Landing также запрашивает screenshots для UI changes.
- Не добавлять большой checklist, пока реальные ошибки не покажут его необходимость.
- Готово, когда новые PR используют одинаковый минимальный contract.

### ORG-09. Дополнить repo-specific harness

- `workspace`: команды unit tests, `inside-harness health`, граница product/cross-repo docs.
- `inside-landing`: реальные install/build/test/deploy команды и UI Definition of Done.
- `platform`: зафиксировать отсутствие application toolchain одной фразой; добавить реальные
  команды только после выбора stack.
- Не копировать общие skills повторно и не добавлять MCP или hooks без повторяющейся потребности.
- Готово, когда `AGENTS.md` каждого repository описывает только его собственную работу поверх
  общего product harness.

### ORG-10. Проверить локальный multi-repository workflow

- Открыть `inside.code-workspace`.
- Проверить, что Workspace, Landing и Platform отображаются отдельными Git roots.
- Проверить, что команды и Git operations выполняются в выбранном repository.
- Зафиксировать только необходимые VS Code workspace settings; не коммитить личные editor settings.
- Готово, когда из одного окна можно безопасно работать с тремя независимыми repositories.

## P2 — настроить task tracker

### TRK-01. Создать organization-level GitHub Project

- Owner: `sachkov-inside`.
- Name: `Inside`.
- Project агрегирует issues и PR из `workspace`, `inside-landing` и `platform`.
- Готово, когда общий обзор работает без переноса всех issues в Workspace.

### TRK-02. Настроить минимальные поля и views

Поля:

- `Status`: Inbox, Ready, In progress, Review, Blocked, Done;
- `Priority`: Now, Next, Later;
- `Area`: Product, Platform, Landing, Operations.

Views:

- `Current`: board по Status;
- `Roadmap`: группировка Now / Next / Later;
- `By repository`: группировка по repository.

Готово, когда любой активный item виден без дополнительных таблиц и документов.

### TRK-03. Нормализовать labels во всех repositories

Минимальный каталог:

- optional category: `bug`, `enhancement`;
- triage readiness: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`;
- Wayfinder: `wayfinder:map`, `wayfinder:research`, `wayfinder:prototype`,
  `wayfinder:grilling`, `wayfinder:task`;
- дополнительные labels добавляются только при повторяющейся необходимости.

Старые `workflow::*`, `type::*`, `hitl` и `afk` мигрировать после переноса текущих issues. Project
`Status` хранит delivery stage, triage labels — readiness role; это разные оси.

Канонические triage и Wayfinder labels установлены во всех трёх repositories 2026-08-20. До
завершения TRK-03 остаются миграция legacy Workspace labels и проверка optional categories.

Готово, когда одинаковые labels имеют одинаковый смысл во всех repositories.

### TRK-04. Перенести текущую работу в Project

- Добавить Workspace issues `#1`, `#4`, `#5`, `#6`, `#7`.
- Для каждого указать Status, Priority и Area.
- Закрытые issues не переносить, если они не нужны для текущего обзора.
- Готово, когда Project отражает реальную текущую работу, а не искусственно созданный backlog.

### TRK-05. Зафиксировать routing новых issues

- Product discovery, owner decisions и cross-repo initiatives → `workspace`.
- Landing implementation и bugs → `inside-landing`.
- Platform implementation и bugs → `platform`.
- Cross-repo initiative → parent issue в Workspace и repo-local sub-issues.
- Готово, когда одна задача существует ровно в одном repository.

### TRK-06. Настроить минимальную автоматизацию Project

- Автоматически добавлять новые issues и PR из трёх активных repositories.
- Закрытый issue или merged PR переводить в Done.
- Не добавлять custom bots, Actions или внешние платные сервисы.
- Готово, когда типовые изменения статуса не требуют ручного дублирования.

### TRK-07. Проверить tracker на одной реальной задаче

- Создать одну небольшую repo-local task.
- Провести её через Inbox → Ready → In progress → Review → Done.
- Связать issue, branch и PR.
- После выполнения убрать лишние поля, labels или правила, которые не помогли.
- Готово, когда workflow проверен практикой, а не только описан документом.

## P3 — подготовить product discovery Platform

Следующие задачи создаются в tracker после завершения P2. Они ещё не выбирают технологии.

### DISC-01. Инвентаризировать контент Telegram

- Определить виды материалов, объём, вложения, связи и качество исходных данных.
- Выбрать небольшую representative sample для будущего импорта.
- Результат: content inventory и список migration risks.

### DISC-02. Зафиксировать роли и access matrix

- Anonymous visitor, free user, member, author/admin.
- Для каждой роли определить доступные материалы и действия.
- Результат: подтверждённая граница public/free/paid.

### DISC-03. Спроектировать минимальную content model

- Материал, серия, тема, уровень, автор, вложение, visibility и progress.
- Не проектировать будущие задания и community глубже необходимых extension points.
- Результат: domain glossary и первая схема сущностей без привязки к database.

### DISC-04. Зафиксировать обязательные user flows MVP

- Просмотр публичного каталога.
- Чтение доступного материала.
- Поиск и фильтрация.
- Отслеживание прогресса.
- Авторское создание или импорт материала.
- Результат: приоритизированный список flows и acceptance criteria.

### DISC-05. Спроектировать постепенную миграцию из Telegram

- Что импортируется автоматически, что переносится вручную, что остаётся только в Telegram.
- Как проверяется корректность и как избежать повторной публикации.
- Результат: migration workflow для representative sample.

### DISC-06. Зафиксировать non-functional constraints

- Полностью бесплатный стартовый режим.
- Ожидаемые объёмы, media, SEO, privacy, backup, analytics и operational effort.
- Результат: список ограничений и критериев сравнения технических вариантов.

### DISC-07. Обновить и утвердить Platform MVP brief

- Свести решения DISC-01–DISC-06 в одну подтверждённую границу MVP.
- Явно перечислить out of scope и открытые решения.
- Готово, когда можно перейти к сравнению stack без домыслов о продукте.

## P4 — переход к технической части

Только после DISC-07:

1. Сравнить варианты stack по подтверждённым критериям.
2. Проверить рискованные места маленькими throwaway prototypes.
3. Записать ADR по architecture, auth/access, content storage, search, media и hosting.
4. Дополнить repo-specific harness Platform реальными командами.
5. Создать первый implementation milestone и вертикальный end-to-end slice.

## Что сейчас не делать

- Не разрабатывать Telegram bot.
- Не добавлять новые repositories без подтверждённой отдельной ответственности.
- Не выбирать framework, database, auth provider или search engine до DISC-07.
- Не добавлять MCP, hooks, profiles и автоматизацию «на будущее».
- Не создавать полный backlog будущей большой платформы до проверки первого MVP flow.
