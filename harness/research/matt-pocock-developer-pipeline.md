# Фактический engineering lifecycle в `mattpocock/skills`

Дата проверки: 2026-08-19.

## Источники и версия

Исследование опирается только на исходники автора и vendored source Inside. На момент проверки
`main` upstream указывает на commit
[`885e2ca`](https://github.com/mattpocock/skills/commit/885e2ca4d842d139e9aef4e48d366c63cb1b8013),
а [`package.json`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/package.json)
содержит версию `1.2.3`. Manifest Inside фиксирует именно этот repository, version и commit:
[`harness/packages/inside-engineering/manifest.json`](https://github.com/sachkov-inside/workspace/blob/08ae1ef/harness/packages/inside-engineering/manifest.json).
Все рассмотренные ниже vendored skill-директории побайтово совпадают с upstream на `885e2ca`.

Есть тонкость воспроизводимости: annotated tag `v1.2.3` у upstream указывает на tag object
`835450e`, который разрешается в commit `6acc160`, тогда как `885e2ca` является более поздним
состоянием `main` на 31 commit, всё ещё с package version `1.2.3`. Поэтому точным идентификатором
установленного Inside snapshot следует считать commit `885e2ca`, а не только строку release/tag.

## Что автор называет pipeline

Это не монолитный обязательный процесс и не отдельный продуктовый task tracker. Автор прямо
описывает skills как маленькие, адаптируемые и composable, в противовес системам, «владеющим» всем
процессом в
[`README.md`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/README.md).
Канонический router —
[`ask-matt`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/engineering/ask-matt/SKILL.md) —
называет основной путь **`idea → ship`**, два on-ramp и отдельные вспомогательные workflows.

Фактический основной путь:

```text
setup (один раз на repository)
  ↓
grill-with-docs = grilling + domain-modeling
  ├─ optional research / questionnaire input
  ├─ optional handoff → prototype → handoff back
  └─ huge/foggy only: wayfinder → to-spec
  ↓
small work: implement
multi-session work: to-spec → to-tickets → implement per ticket
  ↓
implement: TDD where possible → code-review → commit current branch
```

### 1. Setup и repository-local configuration

[`setup-matt-pocock-skills`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/engineering/setup-matt-pocock-skills/SKILL.md)
запускается один раз на каждый repository до первого engineering flow. Он исследует repository,
показывает найденное, спрашивает решения и только после подтверждения создаёт repository-local
contract:

- `docs/agents/issue-tracker.md` — GitHub по умолчанию для GitHub remote; также предусмотрены
  GitLab, local Markdown и произвольный tracker;
- `docs/agents/triage-labels.md` — mapping пяти triage state roles, если установлен `triage`;
- `docs/agents/domain.md` — single-context по умолчанию или multi-context для реального monorepo;
- блок `## Agent skills` в уже существующем `CLAUDE.md` или `AGENTS.md`.

Setup **записывает соглашения**, но его исходник не требует создать labels в GitHub и не настраивает
GitHub Project. GitHub operations, включая sub-issues, dependencies и claims для wayfinder,
описаны в
[`issue-tracker-github.md`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/engineering/setup-matt-pocock-skills/issue-tracker-github.md).

### 2. Discovery и принятие решений

- В working directory основной вход — `grill-with-docs`, который запускает
  [`grilling`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/productivity/grilling/SKILL.md)
  и
  [`domain-modeling`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/engineering/domain-modeling/SKILL.md).
  Решения задаются человеку frontier-раундами; факты агент должен исследовать сам. Термины
  фиксируются в `CONTEXT.md` по мере разрешения, ADR предлагается только для трудно обратимого,
  неочевидного решения с реальным trade-off.
- [`research`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/engineering/research/SKILL.md)
  — AFK reading legwork по primary sources с одним cited Markdown artifact. Это вход в размышление,
  а не замена `grill-with-docs`.
- [`to-questionnaire`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/productivity/to-questionnaire/SKILL.md)
  нужен, когда знание находится у другого человека. Результат возвращается в `grill-with-docs`
  либо сразу в `to-spec`.
- [`prototype`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/engineering/prototype/SKILL.md)
  — throwaway artifact для одного вопроса о logic/state или UI. Валидированное решение идёт в
  production work, а сам prototype остаётся primary source на отдельной `prototype/<name>` branch.
  Router проводит этот detour через `handoff` в обе стороны.
- [`wayfinder`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/engineering/wayfinder/SKILL.md)
  применяется только к огромной, туманной работе, не помещающейся в одну session. Он планирует, а
  не реализует: map issue и child **decision tickets** постепенно убирают fog. После очистки map
  нормальный выход — `to-spec`, затем `to-tickets`, а не прямой `implement`.

### 3. Spec, delivery tickets и implementation

[`to-spec`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/engineering/to-spec/SKILL.md)
не проводит новое интервью: он синтезирует уже состоявшуюся беседу, согласует testing seams,
публикует spec как issue и ставит `ready-for-agent`.

[`to-tickets`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/engineering/to-tickets/SKILL.md)
разбивает утверждённую работу на demoable vertical tracer bullets размером в одну свежую context
window. Пользователь утверждает granularity и blocking graph; после этого tickets создаются в
dependency order, получают native blocking edges где они доступны и label `ready-for-agent`.
Созданные таким способом tickets не проходят повторный `triage`.

[`implement`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/engineering/implement/SKILL.md)
берёт spec/ticket, использует
[`tdd`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/engineering/tdd/SKILL.md)
«where possible» на заранее согласованных seams, регулярно запускает focused checks и завершает
полной проверкой. Затем он обязательно запускает
[`code-review`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/engineering/code-review/SKILL.md)
по двум независимым осям — Standards и Spec — и коммитит результат в **текущую branch**.

На этом upstream contract заканчивается. Он не определяет создание рабочей branch, naming обычных
branches, открытие PR, reviewers/checks, перевод delivery ticket после реализации, закрытие issue,
owner-controlled merge или удаление branch.

### 4. On-ramps и handoff

- [`triage`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/engineering/triage/SKILL.md)
  предназначен для **сырых входящих** issues/внешних PR, а не для tickets, созданных `to-tickets`.
  После проверки и, при необходимости, grilling он создаёт durable agent brief и выводит item в
  `ready-for-agent`; дальше item входит в основной flow на `implement`.
- Hard bug может войти через `diagnosing-bugs`, а затем продолжиться как implementation work.
- [`handoff`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/productivity/handoff/SKILL.md)
  не является обязательным завершением каждой session. По router он нужен только при переходе в
  другой harness, directory/repository, к коллеге или при ответвлении side task mid-phase. В
  остальных случаях сначала рассматриваются continue, clear, subagent и compact; порядок задан в
  [`PHASE-BOUNDARIES.md`](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/skills/engineering/ask-matt/PHASE-BOUNDARIES.md).

## Что обязательно, а что условно

| Workflow | Фактическая обязательность upstream |
| --- | --- |
| `setup-matt-pocock-skills` | Один раз на repository до engineering flows |
| `grill-with-docs` | Канонический старт idea work в working directory; автор рекомендует для каждого изменения |
| `domain-modeling` | Встроен в `grill-with-docs`; новые glossary/ADR artifacts создаются только по реальной необходимости |
| `to-spec` + `to-tickets` | Для multi-session build; для малой работы разрешён прямой `implement` |
| `implement` | Delivery stage; внутри него `code-review` обязателен, TDD — where possible |
| `research`, `questionnaire`, `prototype` | Опциональные detours по характеру неизвестности |
| `wayfinder` | Только huge/foggy effort; избыточен для well-scoped feature |
| `triage` | Только raw incoming work; authored tickets уже готовы агенту |
| `handoff` | Только на portability boundary, не общий session summary |

Разделение на user-invoked и model-invoked skills определяет, **кто может запустить workflow**, а
не превращает workflow в обязательную стадию; это отдельно зафиксировано в
[upstream invocation rules](https://github.com/mattpocock/skills/blob/885e2ca4d842d139e9aef4e48d366c63cb1b8013/.agents/invocation.md).

## Human gates

Upstream явно оставляет человеку решения и irreversible process choices:

1. setup показывает findings и draft, затем ждёт подтверждения до записи файлов;
2. grilling не действует по плану, пока человек не подтвердит shared understanding;
3. `to-spec` согласует testing seams;
4. `to-tickets` ждёт утверждения granularity, split/merge и blocking edges;
5. TDD запрещает писать тест на несогласованном seam;
6. triage сначала рекомендует category/state и ждёт maintainer direction; быстрый override также
   подтверждает будущие изменения до действия;
7. wayfinder `prototype` и `grilling` tickets — HITL, `research` — AFK, `task` зависит от природы
   работы; prototype должен получить human reaction;
8. merge gate upstream отсутствует: `implement` только коммитит текущую branch.

## Tracker, labels и states

В upstream tracker является repository-local source of truth, а не organization board.

Triage использует две category roles (`bug`, `enhancement`) и ровно одну из пяти state roles:

```text
unlabeled → needs-triage → needs-info → needs-triage
                         ├→ ready-for-agent
                         ├→ ready-for-human
                         └→ wontfix (closed)
```

Каждый triaged item должен иметь ровно одну category и одну state role. Maintainer может override
переход. Setup mapping покрывает пять state labels; `bug` и `enhancement` в исходнике triage заданы
как literal category labels, но setup не предлагает их mapping.

Wayfinder использует **другую ось**: `wayfinder:map` и ticket type labels
`wayfinder:research|prototype|grilling|task`, sub-issue relation, native dependencies и assignee как
claim. Закрытие decision ticket означает, что ответ записан comment, а pointer добавлен в map.

Delivery tickets от `to-tickets` получают `ready-for-agent` и blocking edges. Но upstream не вводит
состояния `in-progress`/`in-review`, не связывает обычный delivery claim с assignee, не переводит
готовый код в отдельное состояние и не синхронизирует labels с GitHub Project fields. GitHub Project,
board columns, cross-repository routing, priority/milestone model и automation вообще не входят в
этот contract.

## Рекомендация для Inside

1. Назвать **наш** end-to-end overlay `Developer Pipeline`. Не переименовывать vendored
   upstream skills и не скрывать их provenance: `ask-matt` остаётся router/reference, а
   `WORKFLOW.md` Inside объясняет выбранный маршрут обычным языком.
2. Сохранить upstream flow без лишних обязательных церемоний:
   `grill-with-docs → (to-spec → to-tickets для multi-session) → implement → PR → owner merge`;
   research/questionnaire/prototype/wayfinder подключать только по trigger conditions выше.
3. Добавить в Inside contract отсутствующий delivery envelope:
   `issue → <type>/<issue-number>-<slug> → PR → checks + two-axis review → owner-controlled merge`.
   Для research и prototype использовать соответствующие type prefixes с номером issue.
4. Оставить issue в repository, которому принадлежит deliverable; organization Project может быть
   cross-repository представлением, но не новым source of truth. Его бесплатность и доступные поля
   нужно подтвердить отдельным GitHub settings audit: upstream skills этого не устанавливают. Так
   Landing и Platform остаются автономными, а Workspace получает общий обзор.
5. Не перегружать upstream triage labels delivery-стадиями. Оставить category/type labels для
   природы work item и пять canonical triage states для readiness/decision routing. Если board
   нужен для исполнения, завести отдельное Project field `Status`, минимум:
   `Inbox`, `Ready`, `In progress`, `In review`, `Done`, `Won't do`. Repository использовать как
   отдельное поле/встроенный атрибут, а dependencies — как issue relations, не как status.
6. Перед автоматизацией вручную зафиксировать mapping:
   `ready-for-agent` ↔ Project `Ready`; начало branch/claim ↔ `In progress`; открытый PR ↔
   `In review`; merge/close ↔ `Done`. `ready-for-human` не использовать как синоним review для
   обычных issues: в upstream у него уже есть смысл «нужна human implementation», хотя для PR он
   также означает готовность к human merge.
7. Сначала выполнить P1: repository settings, `WORKFLOW.md`, PR templates, repository-specific
   `AGENTS.md`, multi-root workspace. После этого отдельным P2-решением создать Project и labels;
   иначе board преждевременно зафиксирует ещё не утверждённый workflow.

Итого: upstream даёт сильную decision-to-implementation середину, но сознательно не владеет всей
delivery system. Branch policy, PR lifecycle, owner merge и organization board должны быть тонким,
явным и repository-autonomous слоем Inside поверх неизменённого `mattpocock/skills`.
