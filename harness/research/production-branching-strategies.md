# Branching, releases и deployment для production-платформ

Дата проверки: 2026-08-19.

## Короткий вывод

Современный default для новой online-платформы — **trunk-based integration**: один `main`,
короткоживущие task branches, pull request, быстрые обязательные CI checks и частое слияние.
GitHub Flow является практической PR-формой этого подхода: GitHub называет его lightweight
branch-based workflow, а Google DORA связывает частую интеграцию малых изменений в общий trunk с
высокой delivery performance. Microsoft применяет тот же базовый flow даже в repositories с
сотнями разработчиков: short-lived topic branch → PR checks/review → `main`.

Источники:

- [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow);
- [Google Cloud State of DevOps: trunk-based development](https://cloud.google.com/resources/state-of-devops);
- [How Microsoft develops with DevOps](https://learn.microsoft.com/en-us/devops/develop/how-microsoft-develops-devops).

`develop`, постоянные `release/*`, `hotfix/*` и environment branches не нужны заранее. Они решают
другие задачи: параллельную поддержку нескольких выпущенных версий, длительную стабилизацию
пакетного релиза, формальные release trains или независимые от команды deployment windows. Каждая
дополнительная long-lived branch — ещё одна линия, которую нужно тестировать, синхронизировать и
исправлять.

## Ветки и environments — разные оси

A branch отвечает на вопрос: **где интегрируется и поддерживается исходный код?** Environment
отвечает: **куда развернут конкретный build?** GitHub определяет environments как deployment
targets вроде `development`, `staging` и `production`; они могут иметь отдельные secrets,
approvals, protection rules и deployment history. GitLab аналогично различает static environments
(`staging`, `production`) и временные dynamic environments для review apps.

- [GitHub deployment environments](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments)
- [GitLab environments](https://docs.gitlab.com/ci/environments/)
- [GitLab review apps](https://docs.gitlab.com/ci/review_apps/)

Следствие: наличие `preview`, `staging` и `production` не требует веток с такими именами. Для
continuous delivery Microsoft прямо рекомендует продвигать builds из `main` между deployment
targets, а не использовать environment branches. Branch-per-environment остаётся допустимым
специальным вариантом для waterfall/V-model, сложных interdependent services или формальной
изоляции, но требует явного процесса синхронизации и повышает риск drift.

- [Microsoft Git branching guidance: deployments](https://learn.microsoft.com/en-us/azure/devops/repos/git/git-branching-guidance#manage-deployments)
- [GitLab branching strategies: branch per environment](https://docs.gitlab.com/user/project/repository/branches/strategies/#branch-per-environment)

## Сравнение моделей

| Модель | Что живёт долго | Когда подходит | Цена и риск |
| --- | --- | --- | --- |
| Trunk-based / GitHub Flow | Только `main`; task branches короткие | Online service, одна актуальная production-линия, частые поставки; default для нового продукта | Нужны быстрые CI и небольшие изменения; незавершённое поведение скрывается feature flags, а не долгой branch |
| `main` + `develop` / GitFlow | `main`, `develop`, обычно `release/*`; временные feature/hotfix branches | Versioned software с редкими пакетными релизами и несколькими версиями у пользователей | Повторные merges, поздняя интеграция, сложнее понять canonical state; избыточен для continuously delivered web app |
| Release branches поверх trunk | `main` плюс только реально поддерживаемые `release/<version>` | Нужно заморозить состав релиза, пока `main` идёт дальше, или поддерживать несколько production versions | Каждый активный release увеличивает test/backport matrix; fixes должны попасть и в `main`, и в нужные releases |
| Environment branches | `test`, `UAT`, `production` или аналоги | Отдельные формальные promotion windows и процессы, где artifact promotion невозможен | Branch drift и cherry-pick/merge coordination; не default для CD |
| Release train | Trunk и несколько cadence/channel branches | Desktop/mobile/distributed software, каналы Nightly/Beta/Stable, внешний certification/release calendar | Постоянная release engineering функция, uplift/backport rules и несколько одновременно живых каналов |

Оригинальная модель GitFlow задаёт отдельные `develop`, release и hotfix линии. В добавленной в
2020 году заметке автор рекомендует для continuous delivery более простой workflow вроде GitHub
Flow: [A successful Git branching model](https://nvie.com/posts/a-successful-git-branching-model/).
GitLab также советует не вводить стратегию сложнее нужд продукта и избегать long-lived branches без
контрактной необходимости: [Branching strategies](https://docs.gitlab.com/user/project/repository/branches/strategies/).

Release train — не синоним CI/CD. Это предсказуемая cadence и promotion между каналами. Например,
Firefox двигает изменения через `firefox-main`, `firefox-beta` и `firefox-release` по расписанию;
critical fixes выходят отдельными dot releases. Такой процесс оправдан особенностями массово
распространяемого клиента, но не является базовым требованием для единственного online service:
[Pocket Guide: Shipping Firefox](https://firefox-source-docs.mozilla.org/contributing/pocket-guide-shipping-firefox.html).

## CI gates и promotion

Минимальная production-схема не зависит от выбранного stack:

1. **PR gate.** Branch создана от актуального `main`. До merge проходят быстрые build/static
   checks, focused tests и review. GitHub branch protection может требовать PR, approvals,
   successful status checks, resolved conversations, запрет force-push/delete и отсутствие
   bypass: [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
2. **Main gate.** После merge выполняется более полный acceptance suite. Microsoft намеренно
   разделяет быстрый PR pass и более глубокие post-merge tests, сохраняя `main` buildable:
   [Microsoft release flow](https://learn.microsoft.com/en-us/devops/develop/how-microsoft-develops-devops#pull-request).
3. **Build once.** Успешный commit `main` создаёт идентифицируемый immutable artifact. Environments
   получают тот же release/artifact, а не независимо пересобранные состояния разных branches.
   Модель promotion как продвижение одного release по последовательности targets описана в
   [Google Cloud Deploy overview](https://cloud.google.com/deploy/docs/overview); GitHub artifacts
   сохраняют output между jobs и связываются с commit SHA и provenance в
   [Workflow artifacts](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts).
4. **Preview — optional.** Для UI или integration changes полезен временный environment на PR;
   после закрытия PR он удаляется. Preview подтверждает изменение, но не заменяет CI.
5. **Staging — reusable target.** Тот же artifact проходит smoke/integration/migration checks в
   production-like конфигурации. Добавлять staging нужно, когда появится реально проверяемая
   system boundary, а не как пустой ритуал.
6. **Production gate.** Promotion выполняется только после успешных checks и owner GO. Deployment
   должен быть сериализован, чтобы два релиза не меняли production одновременно. GitHub
   environments поддерживают branch/tag restrictions, approvals, secrets после gate и deployment
   history, а Actions — concurrency groups:
   [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments),
   [Deploying with GitHub Actions](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments).
7. **Verify and progress.** После deploy выполняются health/smoke checks и наблюдение. При росте
   риска используется canary/rings: сначала часть infrastructure/users, затем 100%. Canary
   уменьшает blast radius и является deployment strategy, а не branching strategy:
   [Google Cloud deployment strategies](https://cloud.google.com/deploy/docs/deployment-strategies).

На бесплатном плане GitHub доступность enforcement для private repositories и environment
approvals зависит от plan. Поэтому owner-controlled merge/deploy должен оставаться явным правилом
процесса даже там, где GitHub не может бесплатно принудительно его enforce. Не следует заменять
отсутствующий платный gate custom bot-ом «на будущее». Ограничения по plan перечислены в
[GitHub Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments#deployment-protection-rules).

## Tags, releases, hotfix и rollback

GitHub Release основан на Git tag, который отмечает конкретную точку истории:
[About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).
Практическое разделение:

- любой deployment обязан иметь точный commit SHA и artifact/version identifier;
- version tag и GitHub Release создаются для внешне значимого, повторно устанавливаемого или
  поддерживаемого release, а не автоматически для каждой task branch;
- выбор SemVer, calendar versioning или другой схемы откладывается до появления release contract;
- tag не заменяет deployment record и не требует отдельной release branch.

Hotfix по умолчанию проходит тот же flow, но с приоритетом: короткая `fix/*` branch, CI, review,
merge в `main`, затем ускоренное promotion. Если production развёрнут из отдельной release branch,
fix сначала должен гарантированно попасть в `main`, после чего backport/cherry-pick проходит
отдельным PR в поддерживаемую release branch. Так Microsoft не допускает возврата bug в следующем
релизе: [Release hotfixes](https://learn.microsoft.com/en-us/devops/develop/how-microsoft-develops-devops#release-hotfixes).
Постоянная `hotfix` branch для этого не нужна.

Application rollback и data rollback нельзя считать одной операцией. Runtime может вернуть
предыдущий artifact, но schema/data уже могли необратимо измениться. Зрелый безопасный contract:

- migration changes совместимы одновременно с предыдущей и новой application versions;
- destructive changes выполняются через expand/migrate/contract и при необходимости через
  несколько releases;
- до production проверены forward recovery, backup/restore и observability;
- предпочтителен roll-forward fix; rollback приложения допускается только пока data contract с ним
  совместим.

GitLab требует online migrations, описывает multi-release удаление schema objects и в production
предпочитает roll-forward вместо слепого `db:rollback`:
[Avoiding downtime in migrations](https://docs.gitlab.com/development/database/avoiding_downtime_in_migrations/),
[Migration Style Guide](https://docs.gitlab.com/development/migration_style_guide/#reversibility).
Конкретные migration tools должны быть выбраны только после выбора data stack.

## Размер команды и repository topology

Branching model не определяется автоматически выбором monorepo или multi-repo. Microsoft описывает
оба варианта внутри одного trunk-based release flow; GitLab предупреждает, что cross-repository
release coordination требует отдельного engineering effort:
[Microsoft mono repo or multi-repo](https://learn.microsoft.com/en-us/devops/develop/how-microsoft-develops-devops#mono-repo-or-multi-repo),
[GitLab: when to split a project](https://docs.gitlab.com/user/project/repository/branches/strategies/#when-to-split-a-project-into-multiple-repositories).

- **Один владелец или малая команда:** один protected `main`, short-lived branches, один PR на
  issue, минимальные fast checks. `develop` и release train увеличивают coordination без пользы.
- **Растущая команда:** те же branches; добавляются CODEOWNERS/review ownership, parallel CI и при
  высокой merge concurrency — merge queue. Большое число людей само по себе не требует GitFlow:
  Microsoft использует trunk-based flow при 200+ PR в день.
- **Несколько поддерживаемых версий или внешние release windows:** добавить только необходимые
  `release/<version>` и задокументировать срок поддержки/backport policy.
- **Multi-repo продукт:** каждый repository имеет собственный `main`, CI и release identity.
  Cross-repo change координируется issues/spec и совместимыми contracts, но не общей branch и не
  зависимостью от соседнего checkout.

## Decision rules

Дополнительная long-lived branch появляется только при положительном ответе на конкретный вопрос:

1. Нужно одновременно исправлять две уже выпущенные и поддерживаемые версии? Тогда release
   branches допустимы.
2. Нужно заморозить release candidate, пока следующая версия развивается в `main`? Допустима
   временная release branch с датой закрытия.
3. Есть внешний certification/calendar и несколько пользовательских channels? Рассмотреть release
   train.
4. Требуется формальная branch-based promotion, и immutable artifact promotion невозможен? Только
   тогда рассматривать environment branches.
5. Ни одно условие не выполнено? Оставить один `main`.

## Решение для Sachkov Inside Platform

Подтверждён следующий минимальный contract:

- стратегия: trunk-based GitHub Flow — `main` + короткие `<type>/<issue>-<slug>` branches;
- каждая branch создаётся от актуального `main`, имеет один primary Platform issue и один PR;
- merge только в `main`, squash, после CI/review и явного owner GO;
- не создавать `develop`, постоянные `release/*`, `hotfix/*`, `staging` или `production` branches;
- `main` означает canonical integrated and releasable state, но не автоматически «уже открыт всем
  пользователям»;
- preview/staging/production позже оформить как deployment environments и продвигать один artifact;
- production promotion сериализовать и оставить owner-controlled; progressive delivery и feature
  flags вводить только по реальному risk/rollout case;
- tags/releases добавить после определения внешнего release/versioning contract;
- если появится persistent data, до первого production migration утвердить backward-compatible
  expand/contract, restore test и roll-forward/rollback runbook;
- сохранить текущую multi-repo topology: Platform deploy/release автономны, Landing продолжает
  собственный уже принятый `main → production` flow без изменений.

Пересмотр нужен при первом из трёх событий: появилась вторая одновременно поддерживаемая version,
появился обязательный release calendar/certification либо объём deployments потребовал staged
promotion. До этого дополнительные long-lived branches не дают Platform проверяемой пользы.
