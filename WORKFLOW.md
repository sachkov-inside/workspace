# Developer Pipeline

Developer Pipeline — общий lifecycle Sachkov Inside от идеи или входящего issue до
owner-controlled merge. Он оборачивает composable workflows из `mattpocock/skills`, но не
переименовывает их и не превращает каждый skill в обязательную стадию.

Фактическая upstream-модель и границы skills зафиксированы в
[`harness/research/matt-pocock-developer-pipeline.md`](harness/research/matt-pocock-developer-pipeline.md).
Production branch/release models исследованы в
[`harness/research/production-branching-strategies.md`](harness/research/production-branching-strategies.md).

## Source of truth и routing

Issue создаётся в repository, которому принадлежит результат:

| Результат | Repository |
|---|---|
| Product discovery, owner decision, общий документ или cross-repo initiative | `workspace` |
| Изменение или bug публичного landing | `inside-landing` |
| Изменение или bug Membership-платформы | `platform` |

Cross-repo initiative имеет parent issue в Workspace и repo-local child issues. GitHub Project
агрегирует issues и PR, но issue остаётся source of truth. Подтверждённое устойчивое знание живёт
в versioned document; issue хранит обсуждение и исполнение.

## Выбор маршрута

```text
idea / raw request
  ├─ raw incoming issue or external PR → triage
  ├─ hard bug → diagnosing-bugs
  └─ idea in a working repository → grill-with-docs
       ├─ missing external facts → research
       ├─ knowledge held by another person → to-questionnaire
       ├─ uncertain UI or state model → prototype
       └─ huge multi-session fog → wayfinder

clear small issue → implement
clear multi-session work → to-spec → to-tickets → implement each frontier ticket
implement → TDD where possible → checks → code-review → PR → owner GO → squash merge
```

- `wayfinder` проясняет решения; после него multi-session delivery проходит через `to-spec` и
  `to-tickets`.
- `to-spec` синтезирует уже принятые решения и согласует testing seams; он не начинает новое
  интервью.
- `to-tickets` создаёт demoable vertical slices и публикует их только после owner approval их
  granularity и blocking edges.
- `prototype` отвечает на один вопрос и остаётся throwaway artifact; подтверждённое решение
  переносится в production work.
- `handoff` используется на границе repository, harness, исполнителя или side task, а не как
  обязательный итог каждой session.

## Issue, branch и PR

Каждый PR имеет один primary repo-local issue. Маленькая правка может идти из короткого готового
issue сразу в implementation без spec и decomposition.

Branch создаётся от актуального `main` и называется `<type>/<issue>-<slug>`:

- `feat/123-content-library`;
- `fix/45-login-redirect`;
- `docs/19-developer-pipeline`;
- `chore/27-update-tooling`;
- `research/31-kinescope-api`;
- `prototype/32-library-navigation`.

Одна содержательная задача использует одну branch и один PR. PR содержит `Closes #<issue>`,
результат, проверки, `Not tested`, UI evidence при изменении интерфейса и отдельные owner
decisions. После merge GitHub удаляет head branch автоматически.

### Long-lived branches и deployment

`main` — единственная long-lived integration branch. Workspace хранит в ней принятые документы;
Landing сохраняет существующий `main → production` flow; Platform считает `main` canonical
integrated и releasable state, но не признаком того, что release уже доступен пользователям.

Preview, staging и production являются deployment environments, а не branches. Когда у Platform
появится delivery pipeline, один идентифицируемый artifact продвигается между environments с
checks и owner-controlled production gate.

Не создавать постоянные `develop`, `hotfix/*`, `staging` или `production` branches. Временная
`release/<version>` допустима только если выполнено хотя бы одно условие:

- одновременно поддерживаются несколько production versions;
- release candidate нужно заморозить, пока `main` развивается дальше;
- внешний release calendar, certification или несколько delivery channels требуют release train.

Hotfix по умолчанию проходит `fix/<issue>-<slug>` в `main` и ускоренное promotion. При наличии
живой release branch исправление после merge в `main` переносится отдельным backport PR. Каждая
release branch имеет явно записанный срок поддержки и условия удаления.

## Definition of Ready

Issue готов к implementation, когда:

- выбран repository-владелец результата;
- описаны результат, scope, acceptance criteria и известные blockers;
- определено, какие решения требуют owner GO;
- item имеет одну triage category (`bug` или `enhancement`) и одну readiness role;
- для multi-session работы утверждены spec, vertical tickets и blocking edges;
- testing seams согласованы, если работа использует `to-spec` или TDD.

Канонические readiness labels: `needs-triage`, `needs-info`, `ready-for-agent`,
`ready-for-human`, `wontfix`. Labels Wayfinder: `wayfinder:map` и
`wayfinder:research|prototype|grilling|task`.

## Definition of Done

Работа готова к owner merge, когда:

- acceptance criteria выполнены, а out-of-scope не расширен молча;
- relevant focused checks и полная repository verification проходят;
- `code-review` проверил Standards и Spec от согласованного fixed point;
- durable docs и ADR обновлены, если изменилось подтверждённое решение;
- PR заполнен по template, связан с issue и явно перечисляет `Not tested`;
- UI change содержит mobile и desktop evidence и прошёл repo-specific UI DoD;
- owner дал явный GO на merge.

Merge выполняется только владельцем или после его явного разрешения, методом squash. Agent не
считает готовность PR разрешением на merge.

## Owner gates

Явный owner GO обязателен для:

- product и visual decisions;
- трудно обратимых ADR с реальным trade-off;
- testing seams и ticket breakdown в местах, где этого требует upstream workflow;
- публикации, платежей, credentials, внешних сообщений и других рискованных external writes;
- merge любого PR.

Готовую `ready-for-agent` задачу агент реализует автономно внутри этих границ.

## Repository-local setup

Каждый repository автономно хранит:

- `docs/agents/issue-tracker.md` — операции с его GitHub Issues;
- `docs/agents/triage-labels.md` — mapping канонических readiness roles;
- `docs/agents/domain.md` — правила чтения domain docs и ADR;
- собственные build, test, run, deploy commands и Definition of Done в `AGENTS.md`.

Organization Project является только общей projection. Build, test, deploy и agent workflows не
зависят от локального checkout Workspace.
