# Sachkov Inside: как устроена разработка

## Репозитории

| Repository | Назначение |
|---|---|
| `workspace` | Product-документы, общие решения, Developer Pipeline и canonical harness |
| `inside-landing` | Публичный landing |
| `platform` | Membership-продукт |

Каждый repository автономен. Его agent instructions, skills, workflow, build и deploy не зависят
от наличия Workspace рядом на диске.

## Harness

Canonical source находится в `workspace/harness/`. Команда `harness/bin/inside-harness` копирует
версию package в каждый repository и проверяет её.

Внутри repository:

```text
.inside-harness/skills/                  одна физическая копия skills
.agents/skills -> ../.inside-harness/skills
.claude/skills -> ../.inside-harness/skills
AGENTS.md                                 входные правила для агентов
CLAUDE.md                                 подключает AGENTS.md для Claude
WORKFLOW.md                               общий Developer Pipeline
docs/agents/                              tracker, labels и domain routing
```

Codex, Kimi и OpenCode используют `.agents/skills`; Claude использует `.claude/skills`. Обе ссылки
ведут в один repository-local snapshot. macOS проверен локально, Linux проверяется Harness CI;
Native Windows пока не проверен.

Основные команды запускаются из Workspace:

```bash
harness/bin/inside-harness health <repository>
harness/bin/inside-harness diff <repository>
harness/bin/inside-harness update <repository>
harness/bin/inside-harness rollback <repository> --to <workspace-git-ref>
```

## Какие файлы используют агенты

Агент не должен загружать все документы сразу. Сначала runtime читает свой entrypoint, а затем
открывает только те файлы и skills, на которые указывает задача.

| Файл | Для чего нужен | Кто использует | Кто обновляет |
|---|---|---|---|
| `AGENTS.md` | Главный entrypoint: роль repository, локальные команды, Definition of Done и ссылки на остальные правила | Codex и runtimes с поддержкой `AGENTS.md`; Claude получает его через `CLAUDE.md` | Repository владеет локальной частью; harness — managed block |
| `CLAUDE.md` | Минимальный adapter, подключающий `AGENTS.md` | Claude Code | Harness |
| `WORKFLOW.md` | Общие правила routing, tracker, branches, PR, Ready/Done, review и owner merge gate | Все агенты и люди, когда начинается engineering work | Canonical harness package |
| `docs/agents/issue-tracker.md` | Какой GitHub repository владеет issues, как связывать issue и PR, как работать с Wayfinder maps, sub-issues и blockers | `triage`, `wayfinder`, `to-spec`, `to-tickets`, `code-review` и любой агент, изменяющий tracker | Конкретный repository |
| `docs/agents/domain.md` | Маршрутизатор к product context, terminology, repository boundaries, `CONTEXT.md` и ADR | Агенты, работающие с product, spec, architecture, copy или domain model | Конкретный repository |
| `docs/agents/triage-labels.md` | Единое соответствие readiness roles и GitHub labels | `triage` и агенты, подготавливающие issue к работе | Canonical harness package |
| `CONTEXT.md` | Подтверждённая domain terminology и модель конкретного context | `domain-modeling`, spec и implementation agents | Repository; создаётся только при реальной необходимости |
| `docs/adr/*.md` | Причины и trade-offs труднообратимых решений | Architecture и implementation agents, reviewers и владелец | Repository; создаётся только после подтверждённого решения |
| `.inside-harness/skills/<name>/SKILL.md` | Пошаговая процедура для конкретного типа задачи | Агент открывает только skill, чьё description совпало с задачей | Shared skills — harness; unique local skills — repository |
| `.inside-harness/skills/REGISTRY.md` | Сгенерированный индекс имён, descriptions и путей skills | Runtimes без полноценного native skill discovery | Installer генерирует автоматически |
| `.github/PULL_REQUEST_TEMPLATE.md` | Обязательная структура результата, issue link, verification, `Not tested` и owner decisions | Человек или агент, открывающий PR | Repository |
| `.github/workflows/*.yml` | CI и синхронизация GitHub Project | GitHub Actions; агенты только изменяют и проверяют config | Repository |

`.inside-harness/product-harness.json` — служебное состояние installer: версия package, managed
skills, managed files и discovery paths. Обычный agent workflow его не читает. `HARNESS.md` и этот
`OWNER-GUIDE.md` предназначены прежде всего владельцу и maintainer, а не являются обязательным
prompt context для каждой задачи.

Managed block в `AGENTS.md`, `CLAUDE.md`, `WORKFLOW.md`, triage mapping и shared skills изменяются
в canonical harness package и распространяются через `update`. `domain.md`, `issue-tracker.md`,
локальная часть `AGENTS.md`, `CONTEXT.md`, ADR, PR template и GitHub workflows изменяются внутри
repository, которому они принадлежат.

## Работа с ветками

### Модель веток

- `main` — единственная постоянная integration branch и всегда представляет принятый результат.
- Прямые рабочие commits в `main` не делаются: каждая change проходит через отдельную короткую
  branch и PR.
- Одна branch решает одну связанную задачу в том repository, который владеет результатом.
- Каждый пишущий agent работает в отдельном Git worktree своей task branch. Даже один agent не
  изменяет основной checkout; при параллельной работе у каждого agent собственные worktree и branch.
- Read-only agent может проверять существующий worktree, если не меняет файлы и не переключает его
  branch.
- `develop`, постоянные release, staging и production branches заранее не создаются. Environments
  относятся к deployment, а не к Git branch model.

Branch name для tracked work: `<type>/<issue>-<slug>`. Для небольшой docs/chore без issue:
`<type>/<slug>`.

| Тип | Когда использовать |
|---|---|
| `feat` | Новая product capability |
| `fix` | Исправление дефекта |
| `docs` | Документация без product implementation |
| `chore` | Repository, CI, dependency или tooling maintenance |
| `research` | Исследование, которое должно остаться отдельным artifact или решением |
| `prototype` | Throwaway experiment вне production path |

### Жизненный цикл ветки

1. **Начало.** Выбрать owning repository, переключиться на `main`, получить его актуальное
   состояние и убедиться, что чужие незакоммиченные изменения не затрагиваются.
2. **Work item.** Product work, bug, architecture и существенная документация имеют issue с
   результатом, scope и acceptance criteria. Небольшая очевидная docs/chore может идти сразу в PR.
3. **Worktree и branch.** Для пишущего agent создать отдельный Git worktree с новой branch от
   актуального `main`. Один worktree принадлежит одному активному пишущему agent и одной задаче.
   Когда реализация реально началась, перевести Project item из `Ready` в `In progress`; создание
   worktree или branch само по себе не меняет status.
4. **Работа.** Делать только изменения текущего scope, сохранять понятные commits и регулярно
   выполнять focused checks. Не складывать несвязанные исправления в ту же branch.
5. **Синхронизация.** Если `main` ушёл вперёд, перед финальным review обновить branch из `main` и
   разрешить conflicts внутри branch. Не переписывать опубликованную branch без необходимости.
6. **Pull request.** Запушить branch и открыть один PR. Для tracked work указать `Closes #<issue>`;
   заполнить result, verification, `Not tested`, owner decisions и UI evidence, когда оно требуется.
7. **Review.** Открытый PR автоматически получает Project status `Review`. Дождаться CI, устранить
   conflicts и findings; для нетривиальной работы провести отдельные Standards и Spec review.
8. **Merge.** Только после явного разрешения владельца выполнить squash merge. В `main` попадает
   один итоговый commit, issue закрывается, а Project item переходит в `Done`.
9. **Cleanup.** GitHub удаляет remote branch. Убедиться, что в task worktree нет незакоммиченной или
   незапушенной работы, затем удалить worktree и local branch. Основной worktree обновить до merged
   `main`; следующая задача всегда начинается от нового актуального `main`.

Обычный hotfix проходит тем же путём через `fix/<issue>-<slug>` и PR в `main`. Временная
`release/<version>` появляется только при реальной необходимости поддерживать несколько production
versions или отдельный release freeze; при создании сразу фиксируются срок жизни и условие удаления.

## GitHub Project

[Inside Project](https://github.com/orgs/sachkov-inside/projects/1) — общая доска; source of truth
остаётся в repository issue или PR.

Status:

```text
Inbox → Ready → In progress → Review → Done
                    └──────→ Blocked
```

Автоматизация:

- новый, reopened или transferred issue → `Inbox`;
- открытый или reopened PR → `Review`;
- закрытый issue или merged PR → `Done`.

`Ready`, `In progress` и `Blocked` меняет владелец или агент по фактическому состоянию работы.
`Priority` — `Now`, `Next`, `Later`; `Area` — `Product`, `Platform`, `Landing`, `Operations`.

Readiness labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.
Category labels `bug` и `enhancement` не заменяют readiness status.

## CI

- Workspace: harness unit tests, `health` и `diff` на каждый PR и push в `main`.
- Landing: install, verify и production build.
- Platform: application CI появится после выбора stack и реальных команд.

Branch protection одинаково включить бесплатно нельзя, пока Workspace и Platform приватные.
Поэтому merge защищён процессом: только PR, проверки и явное разрешение владельца.

## Версии harness

Version tag вида `inside-engineering-vX.Y.Z` обязателен: он фиксирует точный Workspace commit и
используется для rollback. GitHub Release необязателен; текущий installer ничего из него не
скачивает.

Обновление:

1. Изменить canonical package в Workspace.
2. Обновить package version.
3. Запустить tests, `health` и `diff`.
4. После разрешения владельца смержить и создать tag.
5. Выполнить `update` для Landing и Platform отдельными reviewable изменениями.

## Как повторить такой setup в другом проекте

1. **Определить topology.** Перечислить активные repositories, назначение каждого и владельца
   каждого результата. Удалить из процесса неактивные направления.
2. **Разделить общее и локальное.** Выбрать один Workspace как canonical source общих правил и
   оставить build, test, run, deploy и application decisions в соответствующих repositories.
3. **Создать versioned harness package.** Собрать в Workspace общий workflow, shared skills,
   managed agent instructions, manifest, provenance и license information.
4. **Отобрать skills.** Включать только реально используемые skills, фиксировать их источники и не
   допускать одинаковых имён у shared и repository-specific skills.
5. **Настроить runtime discovery.** Определить, где каждый agent runtime ищет skills, и направить
   эти entrypoints на один repository-local snapshot без абсолютных и machine-local путей.
6. **Сделать lifecycle tool.** Installer должен уметь устанавливать, обновлять, проверять drift,
   показывать health и возвращать предыдущую версию, не удаляя неизвестные локальные файлы.
7. **Установить harness в каждый repository.** Каждый repository получает собственный committed
   snapshot и остаётся работоспособным без Workspace и user-level plugins, MCP, hooks или skills.
8. **Добавить agent entrypoints.** В каждом repository должны быть короткие `AGENTS.md` и
   `CLAUDE.md`, общие managed правила и отдельные repository-specific команды и Definition of Done.
9. **Зафиксировать engineering workflow.** Описать routing issues, readiness, branch naming,
   issue → branch → PR, проверки, Definition of Ready, Definition of Done и owner-controlled merge.
10. **Унифицировать GitHub repositories.** Выбрать default branch, разрешённые merge methods,
    автоматическое удаление merged branches, PR template, labels и доступную branch protection.
11. **Создать общий tracker.** Настроить organization Project как проекцию repository issues и PR,
    определить минимальные Status, Priority и Area и не дублировать требования внутри карточек.
12. **Добавить минимальную автоматизацию.** Новые issues и PR попадают на доску, PR переходит в
    `Review`, закрытая работа — в `Done`; остальные смысловые переходы выполняет владелец или агент.
13. **Добавить CI.** Workspace проверяет harness tests, health и drift; application repositories
    запускают только реальные install, test, build и deploy checks своего проекта.
14. **Зафиксировать release lifecycle.** Версия harness связывается с Git tag, сначала проходит
    pilot rollout, затем устанавливается в остальные repositories отдельными reviewable changes.
15. **Провести финальный аудит.** Проверить autonomy, отсутствие drift, работу agent discovery,
    GitHub automation, чистые working trees и отсутствие незавершённых временных artifacts.

После этого infrastructure setup завершён. Product discovery и выбор технического stack идут через
обычные issues и решения проекта, а не через дальнейшее усложнение harness.

## Роль владельца

Владелец принимает product и visual decisions, утверждает необратимые ADR, testing seams и ticket
breakdown, разрешает внешние рискованные действия и каждый merge. Агент самостоятельно выполняет
готовую задачу внутри подтверждённых границ.
