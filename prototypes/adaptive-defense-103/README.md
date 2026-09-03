# Throwaway prototype: adaptive AI defense (#103)

> **Не production-код.** Каталог существует только в ветке
> `prototype/103-adaptive-ai-defense`, не предназначен для merge в `main` и удаляется без
> миграции данных или runtime dependencies.

## Вопрос эксперимента

Даёт ли bounded adaptive defense полезный mastery signal для Production Case `Partner Webhooks`,
когда использование AI разрешено, если модель видит только versioned CaseSpec/rubric, bounded
source evidence, technical report/telemetry, Decision Record и ответы участника? Одновременно
эксперимент проверяет, можно ли отделить такой signal от недоказуемого вывода о происхождении кода
и от окончательного решения Platform о `Verified`.

## Owner decision

**DEFER / NO-GO для первой версии.** 2026-09-03 владелец решил, что V1 проверяет решение через
executable local tests, связанные с exact source revision, а обучение поддерживают Materials и
авторский разбор/точное решение. Adaptive AI defense, AI feedback и AI provider integration не
являются gate для `Verified` и не входят в первую Platform Specification.

Сам prototype показал, что bounded adaptive defense технически может быть полезным advisory mastery
layer позднее. Это не доказывает, что он нужен для первого slice. Вернуться к решению стоит только
после human beta, если тесты и материалы оставят измеримый feedback gap, либо ручной разбор станет
плохо масштабироваться.

На 5 намеренно различающихся fixture attempts полный adaptive loop дал ожидаемый calibration signal
во всех 15 независимых прогонах. Question generation была blind: model input содержал только opaque
attempt ID и разрешённый context, без fixture name/archetype, ожидаемого результата или ответов.
Первый call генерировал вопросы, второй оценивал ответы, а bounded третий call запускался только при
follow-up. Вопросы, follow-ups и rubric assessments ссылались только на canonical evidence IDs.

Два fixture с одним и тем же exact synthetic diff, source snapshot identity и passing technical
report получили разные сигналы исключительно из-за Decision Record и ответов:
`mastery_supported` против `mastery_not_yet_shown`. Ни один output не сделал provenance claim и не
попытался переписать technical result.

Это proof полезности механизма, а не production calibration. Fixtures синтетические, ответы
заранее покрывают известные риски, а настоящий C#/.NET или Python starter repository ещё не
проверялся. До автоматического влияния defense на `Verified` нужны pilot attempts людей, manual
author calibration и appeal/manual path.

## Запуск

Для shareable logic/state walkthrough откройте [`defense-lab.html`](defense-lab.html) двойным
кликом. Установка и server не нужны.

Чтобы повторить model experiment, нужен авторизованный Codex CLI и Node 22+:

```bash
node experiment/run.mjs 3
```

Runner выполняет три независимых прогона каждого fixture с concurrency 3, моделью `gpt-5.4` и
`reasoning_effort=low`. Он передаёт phase input через stdin в ephemeral read-only Codex session со
strict structured output и пустым shell environment. Результаты перезаписываются в
[`evidence/model-runs.json`](evidence/model-runs.json) и
[`evidence/summary.json`](evidence/summary.json). Failure paths отдельно воспроизводятся командой:

```bash
node experiment/record-failure-scenarios.mjs
```

Её записанный результат —
[`evidence/failure-scenarios.json`](evidence/failure-scenarios.json). Recorder сохраняет
наблюдения из logic demo, но намеренно не содержит test assertions: по правилам throwaway logic
prototype тесты здесь не добавляются.

Codex с ChatGPT account не разрешил immutable model ID `gpt-5.4-2026-03-05`, поэтому prototype
зафиксировал alias, CLI version и дату прогона. Production обязан хранить immutable provider/model
snapshot либо явно versioned alias policy вместе с prompt и rubric versions.

После review contract был дополнительно усилен version fields, dynamic evidence validation и
запретом результата без полного набора ответов. Финальная provider-серия для этих hardening changes
не запускалась: владелец исключил AI defense из V1 и остановил дальнейшие затраты. Ниже сохранены
результаты последней завершённой blinded серии до этого решения.

## Fixture set

| Fixture | Технический результат | Проверяемая граница | Calibration |
|---|---|---|---|
| `dotnet-deliberate` | passed | outbox consistency, lease, diagnosis | `mastery_supported` |
| `python-surface-pass` | public pass, crash not run | in-process task ошибочно считается durable | `mastery_not_yet_shown` |
| `dotnet-critical-misunderstanding` | failed | synchronous partner call, terminal retry, tenant/secret violations | `mastery_not_yet_shown` |
| `python-reference-strong` | passed | reference-like/AI-assisted source с пониманием guarantees | `mastery_supported` |
| `python-reference-weak` | тот же source/report | exactly-once и security claims не объяснены | `mastery_not_yet_shown` |

Archetypes и owner calibration были записаны до model runs в
[`experiment/fixtures.json`](experiment/fixtures.json). Blinded pilot обнаружил неполное покрытие
сгенерированных вопросов prepared answers; response coverage и exact diff fixtures были уточнены до
финальной серии. `calibrationExpectation`, fixture metadata и answer-selection metadata runner
модели не передаёт.

## Measurements

Environment: macOS arm64, Node v22.23.1, `codex-cli 0.153.0`, GPT-5.4 alias, low reasoning. Каждый
attempt прогнан трижды; одновременно выполнялось не больше трёх calls. Финальная серия сделала 41
provider call: 2 на обычный defense и третий только при follow-up.

| Measure | Result |
|---|---:|
| Expected signal | 15 / 15 |
| Unanimous fixtures | 5 / 5 |
| Question canonical grounding | 100% |
| Follow-up canonical grounding | 100% |
| Rubric canonical grounding | 100% |
| Provenance claims | 0 |
| Technical override attempts | 0 |
| Provider-call latency p50 / p95 | 23.5 s / 34.6 s |
| Completed-defense latency p50 / p95 | 73.4 s / 82.4 s |
| Provider-reported input / cached input | 613,521 / 383,232 tokens |
| Provider-reported output | 33,787 tokens |
| Average explicit prompts per defense | 28,260 UTF-8 bytes across phases |

Codex CLI не сообщает invoice cost. Для сравнимого proxy к recorded usage применены официальные
GPT-5.4 API rates на 2026-09-03: $2.50 / 1M uncached input, $0.25 / 1M cached input и $15 / 1M
output ([OpenAI model page](https://developers.openai.com/api/docs/models/gpt-5.4)). Derived estimate:
$1.1783 за 41 call, $0.0287 за call, около $0.0575 за двух-call defense и не больше $0.0862 за три
calls при таком же usage/caching. Это **не фактический счёт**: usage включает большой
Codex agent runtime context, а prototype использовал ChatGPT-authenticated CLI, не Responses API.

В beta нужно писать фактические provider usage/cost и latency на один completed defense, отдельно
считая question generation, assessment и optional follow-up.

## Минимальный Platform contract

### Inputs: `inside.adaptive-defense-input.v1`

Один immutable defense привязан к `attemptId`, exact `caseVersion`, `sourceRevision`,
`evaluationReportVersion`, `promptVersion`, `rubricVersion` и `modelVersion`. В prompt допускаются:

1. CaseSpec facts и четыре rubric dimensions: `correctness`, `reliability`, `operability`,
   `decision_quality`;
2. exact cumulative diff и bounded relevant files только assignment repository;
3. accepted local report, scenario outcomes, bounded diagnostics и telemetry;
4. двухчастный Decision Record: initial constraints/approach и after-code changes/trade-offs;
5. ответы только текущей defense.

Каждый факт получает canonical evidence ID. Source, Decision Record и answers считаются untrusted
data: provider не получает tools, credentials или network actions; structured output не может
исполнять инструкции из participant content. До prompt удаляются known secret formats, binary,
generated/vendor files и unrelated repository content. Другие repositories, GitHub profile,
Platform secrets и Account content запрещены.

Initial beta budgets для последующей калибровки:

- не больше 32k input и 2k output tokens на semantic call;
- три initial questions и не больше двух follow-ups;
- обычный путь — question generation + assessment, максимум один final assessment после follow-up;
- target learner interaction 6–10 минут; истечение времени само по себе не означает fail;
- один active defense на Attempt и пятиминутный cooldown до provider-backed defense новой Attempt
  того же Assignment.

### Output: `inside.adaptive-defense-result.v1`

Question artifact, assessment artifact и собранный result имеют отдельные standalone strict schemas:
[`question-output.schema.json`](experiment/question-output.schema.json),
[`assessment-output.schema.json`](experiment/assessment-output.schema.json) и
[`defense-output.schema.json`](experiment/defense-output.schema.json). Standalone definitions
намеренно повторяются: Codex CLI принимает один self-contained `--output-schema`, а generator/build
step для throwaway prototype не добавляется. Assessment не может переписать immutable initial
questions. Итоговый output содержит:

- immutable `artifactContext` с case/source/report/prompt/rubric/model versions и объединённые
  canonical `evidenceRefs`;
- 2–3 grounded initial questions и 0–2 grounded follow-ups;
- advisory `defenseSignal`: `mastery_supported`, `mastery_not_yet_shown` или `inconclusive`;
- confidence и четыре dimension signals с evidence refs/rationale;
- explicit contradictions и короткий feedback: strengths + next steps;
- `provenanceClaim=none` и `technicalEvidenceOverrideAttempted=false`.

Platform, а не модель, композирует `MasteryResult`. `mastery_supported` не превращает failed local
report в pass. `mastery_not_yet_shown` не маскируется passing checks. `Verified` возможен только
когда отдельные technical и defense policies выполнены; raw numeric model score в UI не нужен.

### Retry, low confidence и conflict

- Provider error: Attempt остаётся `defense_pending`, immutable technical evidence сохраняется,
  retry продолжает ту же defense version. Максимум два automatic retries одного semantic call с
  30 s / 120 s backoff; затем support/manual path без отрицательного mastery signal.
- Confidence ниже initial calibration threshold `0.75`: сохранить `inconclusive`, не выдавать
  `Verified` и предложить manual calibration или новую Attempt. Threshold является beta knob, не
  скрытым passing score.
- Invalid evidence ref, повторяющаяся/пропущенная rubric dimension, несовпадающий
  `artifactContext`, schema violation или попытка изменить technical result: output отклоняется;
  один retry с тем же versioned input, затем manual path. Experiment runner выполняет эти dynamic
  checks до сохранения результата; JSON Schema покрывает статическую shape.
- Семантический конфликт AI с report/source: technical evidence остаётся authority для observable
  checks, defense становится `inconclusive`, а конфликт хранится для author review.

Эти переходы можно прожать в `defense-lab.html`; после каждого action demo показывает полный
relevant state. Recorder воспроизводит и сохраняет четыре наблюдения: provider-unavailable,
low-confidence, technical-conflict и illegal-transition paths.

## Experimental staged flow (superseded for V1)

Decision Record действительно добавил сигнал: он помог отличить осознанное изменение guarantee от
поверхностного «best practices». Однако prototype не доказывает, что текст был написан до кода.
Если после human beta сработает trigger возврата к AI, проверенная здесь гипотеза flow выглядит так:

1. сохранить короткий initial plan до запуска финальной evaluation;
2. при submit требовать after-code addendum с расхождениями, обнаруженными failure scenarios;
3. не использовать timestamp или стилистику plan как anti-cheating signal;
4. после technical report запускать одну короткую adaptive defense, а не отдельный длинный oral
   exam.

Так сохраняется flow `понять → реализовать/проверить → защитить`, но Platform не обещает доказать
chronology или авторство текста.

## Known false positives / false negatives

- Fixtures намеренно контрастны; 15/15 может завышать качество на пограничных human attempts.
- Промежуточный assessment без ответов на follow-up дал 12/15 и три false negatives на strong
  fixtures. Только bounded final assessment после follow-up восстановил 15/15. Поэтому Platform не
  должна финализировать отрицательный signal, пока сама модель запросила уточнение.
- Убедительный, но неверный ответ способен получить false positive, если relevant counter-evidence
  не попало в bounded context.
- Краткий ответ, неродной язык или слабое письменное выражение могут дать false negative при
  реальном инженерном понимании. Rubric не должен оценивать стиль; `inconclusive` и manual path
  обязательны.
- Grounded question может подсказать missing solution. Это допустимо как learning feedback, но
  снижает ценность повторного identical question; следующая Attempt должна получать новый
  counterfactual из тех же выданных facts.
- Prototype использует exact synthetic cumulative diffs и evidence summaries, а не полный реальный
  starter repository. Prompt injection, context selection recall и C#↔Python parity требуют
  отдельного conformance corpus в Platform.
- Model variance проверена только на одном alias, одном prompt и low reasoning. До beta нужны
  immutable model/prompt comparison и periodic author recalibration.

## Trigger для возврата

Не переносить этот contract в V1. Открыть новое решение после human beta только при одном из
наблюдаемых сигналов:

1. public tests систематически дают `Verified` решениям с критическим непониманием;
2. Materials и author solution не дают участнику достаточно конкретного feedback для следующей
   попытки;
3. ручной author review становится измеримым bottleneck;
4. появляется отдельный learning outcome, где объяснение trade-offs нельзя проверить executable
   scenario.

Тогда этот branch служит input для нового bounded decision, но не готовой production
specification. Provider selection, retention, cost limits и AI integration должны решаться заново
на актуальных human attempts.

## Verification

- Final blinded adaptive experiment: 15/15 expected signals, 100% question/follow-up/rubric
  grounding, 0 provenance claims, 0 technical overrides.
- Failure-mode recorder: сохранены наблюдения provider-unavailable, low-confidence,
  evidence-conflict и illegal-action scenarios; это не automated test suite.
- Privacy/context audit: question call не содержит fixture calibration metadata или prepared
  answers; модель получает только synthetic Assignment context; credential-shaped values и
  external references в HTML отсутствуют.
- Inline script parse и reducer walkthroughs: pass.
- Workspace verification: 38 unit tests pass, harness `health` healthy, harness `diff` clean.
- **Not tested:** visual desktop/mobile render и manual browser clicking — in-app browser backend в
  сессии был недоступен. HTML остаётся self-contained и прошёл static/logic checks.

## Deletion test

Удаление каталога и ветки удаляет весь prototype. В `main` не добавлены code, schemas, provider
dependencies, credentials или product decisions.
