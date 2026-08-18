# AGENTS.md — sachkov-inside

Канон этого репозитория. Источник правды для **всех** агентов (Claude Code, Codex, Kimi Code, Hermes).
Рантайм-мосты (`CLAUDE.md`) содержательных правил не несут, только указывают сюда.

`.harness/skills` содержит один pinned clean public suite и project-only skills. Один snapshot
открыт всем coding runtime через `.agents/skills` и `.claude/skills`.

Этот файл не раздувается: только самое главное и указатели. Подробности складывай в `docs/` и
per-module `AGENTS.md`, а здесь оставляй ссылку на них.

## Что это за проект

Приватный control plane проекта Sachkov Inside: здесь живут продуктовая стратегия Membership,
Telegram-first запуск, community operations, content portfolio, исследования, решения и roadmap.
Production-артефакты контента остаются в `sachkov-content`, а будущее Membership-приложение
получит отдельный репозиторий, созданный с нуля внутри закрытой серии.

- **Стек:** content
- **Стадия:** discovery и подготовка Telegram-first запуска
- **Трекер:** github (`KirillSachkov/sachkov-inside`)
- **Базовая ветка:** `main`

Provider и точные native-команды трекера: [`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md).
Проверки и review-контракт проекта: [`docs/agents/testing-profile.md`](docs/agents/testing-profile.md)
и [`docs/agents/review-profile.md`](docs/agents/review-profile.md). Workflow выбирается из clean
project skills по смыслу задачи, без отдельного private lifecycle.

## Команды

Каждая из них проверена при развёртывании харнеса. Если команда перестала работать, чини её
или помечай сломанной здесь же, не оставляй молча.

```bash
: # setup не требуется: внешних зависимостей нет
gh issue list --repo KirillSachkov/sachkov-inside --limit 20  # рабочая очередь
bash scripts/verify-workspace.sh                              # полная проверка
git diff --check                                              # lint изменений
: # build отсутствует: проект не создаёт runtime-артефакт
```

## Структура

- `product/` — аудитория, обещание, коммерческие и продуктовые решения Membership.
- `operations/` — Telegram/Tribute, community policy, launch и operational evidence.
- `portfolio/` — content pillars, portfolio/backlog и ссылки на authority в `sachkov-content`.
- `research/` — source-backed исследования; изменчивые факты всегда имеют дату проверки.
- `docs/agents/` — tracker, testing и review contracts проекта.
- `.out-of-scope/` — отклонённые решения с аргументацией и ссылкой на native issue.

## Границы

- **Можно всегда:** читать проект и связанные публичные источники; вести research и проектные
  документы в worktree активной задачи; выполнять read-only проверки; работать с GitHub Issues
  в границе подтверждённого workflow.
- **Спросить сначала:** merge в `main`; публикация или отправка сообщений; приглашение или
  исключение участников; активация платежей/подписок; изменение GitHub repository settings;
  любая внешняя или production-мутация.
- **Не трогать:** секреты, платёжные данные и персональные данные участников; production-артефакты
  `sachkov-content`; код `education-platform`; будущий app до отдельного созданного владельцем
  проекта и подтверждённых решений.

## Definition of Done

Задача считается сделанной, когда выполнено всё перечисленное:

- Acceptance активного GitHub Issue выполнен без расширения scope.
- Факты отделены от гипотез и owner decisions; изменчивые внешние факты датированы и имеют source.
- Обновлён существующий канонический документ, а не создан конкурирующий дубль.
- `bash scripts/verify-workspace.sh` и `git diff --check` проходят.
- Issue и все затронутые связи прочитаны обратно после записи.
- Внешние действия имеют отдельный owner GO и сохранённое безопасное evidence.
- Полный итог записан один раз в канонической GitHub Issue или PR.

## Политика мержа

Агент доводит task-ветку и pull request до merge-ready и останавливается. Merge в `main` делает
владелец после просмотра. Публикация, платежи, приглашения и другие внешние действия требуют
отдельного owner GO.

По умолчанию для проектов с кодом: агент доводит ветку до merge-ready (зелёный CI на
последнем коммите, ревью закрыто, конфликтов нет) и **останавливается**. Мерж в
интеграционную ветку делает владелец после прочтения отчёта. В контентных репозиториях
независимое code review не требуется, если работа не меняет продуктовый код. Агент проверяет
артефакт и останавливается перед owner merge.

Checkout, branch и необходимость linked worktree выбираются по задаче или явной команде владельца.

После owner merge или отказа агент сам проверяет merged/clean state, удаляет task worktree и
локальную/remote ветку и сообщает о выполненном cleanup. Чужой или живой worktree не трогает.

## Agent harness

- `.harness/harness.lock` управляет только public skill snapshot. Public-managed skill files не
  правятся локально; project-only skill names принадлежат этому репозиторию.
- Project hooks, hidden rule injection и user-level development suite не используются. Safety,
  external-action gates и verification находятся в этом `AGENTS.md` и project docs.
- Upstream explicit-only skills остаются explicit-only. Остальные skills могут вызываться моделью
  по их native description.

## Связь с мозгом

- Задачи от Hermes с `project: sachkov-inside` промоутятся в github project `KirillSachkov/sachkov-inside`.
- Durable кросс-проектные факты и решения идут в мозг (`memory/`, `wiki/`), не в этот
  репозиторий. Расположение мозга разрешается через `harness/bin/brain-root`.
- Итог проектной задачи записывается один раз в канонической GitHub Issue или PR.

## Известные грабли

- `Inside` пока рабочее направление названия, не утверждённый публичный бренд.
- Tribute — кандидат, а не подтверждённый billing/access authority; условия проверяются перед
  launch-решением.
- App MVP, billing, architecture, design и repository намеренно решаются внутри будущей серии,
  а не достраиваются предположениями в этом control plane.
- Telegram хранит community conversation и короткие анонсы; долгосрочный дом материалов —
  будущее отдельное приложение.
- Не копировать scripts, видео, уроки и публикационные файлы из `sachkov-content`: здесь остаются
  portfolio-level brief, статус и ссылка на authority.
