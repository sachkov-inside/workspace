# Developer Pipeline

Это project-specific engineering agreement Sachkov Inside. Installed skills сами определяют свои
invocation и steps; этот файл задаёт только общие правила repositories, branches, pull requests и
owner gates.

## Routing

Issue создаётся в repository, которому принадлежит результат:

| Результат | Repository |
|---|---|
| Product discovery, owner decision, общий документ или cross-repo initiative | `workspace` |
| Изменение или bug публичного landing | `inside-landing` |
| Изменение или bug Membership-платформы | `platform` |

Cross-repo initiative имеет parent issue в Workspace и repo-local child issues. Issue хранит
обсуждение и исполнение; подтверждённое устойчивое знание записывается один раз в versioned
document. GitHub Project, когда он подключён, остаётся projection над issues и PR.

## Issue, branch и PR

Product work, bugs, architecture и нетривиальные изменения документации начинаются с одного
primary repo-local issue. Trivial docs/chore может идти напрямую в короткий PR, если не требует
обсуждения, tracking или owner decision.

Branch создаётся от актуального `main`. Для tracked work имя имеет вид
`<type>/<issue>-<slug>`; для trivial untracked work — `<type>/<slug>`. Используются types `feat`,
`fix`, `docs`, `chore`, `research` и `prototype`.

Одна содержательная задача использует одну branch и один PR. Для tracked work PR содержит
`Closes #<issue>`. Каждый PR описывает результат, проверки, `Not tested` и открытые owner
decisions; UI evidence добавляется только при изменении интерфейса. После merge GitHub удаляет
head branch автоматически.

### Long-lived branches и deployment

`main` — единственная long-lived integration branch. Preview, staging и production являются
deployment environments, а не branches.

Временная `release/<version>` появляется только при реальной maintenance boundary: одновременно
поддерживаются несколько production versions, release candidate требует freeze или внешний
calendar/certification требует release train. Для неё сразу записываются срок поддержки и условие
удаления. Обычный hotfix идёт через `fix/<issue>-<slug>` в `main`; backport PR нужен только для
активной release branch.

## Ready и Done

Tracked work готов к implementation, когда известны result, scope, acceptance criteria, blockers
и owner decisions. Для multi-session delivery также согласованы decomposition и dependencies.
Readiness roles берутся из repo-local `docs/agents/triage-labels.md`; Wayfinder structure — из
`docs/agents/issue-tracker.md`.

Работа готова к owner merge, когда:

- acceptance criteria выполнены, а out-of-scope не расширен молча;
- relevant focused checks и полная repository verification проходят;
- durable docs и ADR обновлены, если изменилось подтверждённое решение;
- PR заполнен по template, связан с issue when applicable и явно перечисляет `Not tested`;
- UI change содержит mobile и desktop evidence и прошёл repo-specific UI DoD;
- owner дал явный GO на merge.

Implementation, spec и architecture changes проходят Standards + Spec `code-review` от
согласованного fixed point. Для trivial docs/chore достаточно bounded diff review и relevant
verification.

## Owner gates

Явный owner GO обязателен для:

- product и visual decisions;
- трудно обратимых ADR с реальным trade-off;
- testing seams и ticket breakdown, когда выбранный skill требует согласования;
- публикации, платежей, credentials, внешних сообщений и других рискованных external writes;
- merge любого PR.

Готовую `ready-for-agent` задачу агент реализует автономно внутри этих границ. Merge выполняется
только владельцем или после его явного разрешения, методом squash; готовность PR сама по себе не
является разрешением.
