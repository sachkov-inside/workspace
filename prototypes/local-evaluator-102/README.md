# Throwaway prototype: local evaluator and source handoff (#102)

> **Не production-код.** Этот каталог существует только в ветке
> `prototype/102-local-evaluator`, не предназначен для merge в `main` и удаляется без миграции
> данных или контрактов.

## Вопрос эксперимента

Можно ли одной локальной командой проверить Docker-compatible public scenario кейса Partner
Webhooks, выпустить versioned report для exact local commit и передать его в Platform ingress так,
чтобы GitHub оставался независимым source authority, а evaluator не мог сам назначить результат
`Verified`? Если да, какой язык лучше для распространяемого evaluator/CLI: Go или TypeScript?

## Verdict

**Local-first путь технически осуществим. Для evaluator/CLI рекомендуется Go.** Один и тот же
Docker scenario прошёл через реализации на Go и TypeScript, а один ingress contract принял оба
report. Go при этом даёт нативный dependency-free artifact около 2.3 MB и median cold startup
2.669 ms. TypeScript archive занимает лишь 2,974 bytes, но требует установленный Node; использованный
Node executable занимает 112,928,848 bytes, а median startup равен 54.409 ms.

Язык не создаёт новый service или repository. Начальный owner — Platform; Go evaluator может жить
как отдельно собираемый Platform-owned Module. Выделение repository возвращается на owner decision
только после доказанного independent release, trust или ownership lifecycle.

Один blocker остаётся перед production ADR: `linux/amd64` binary успешно cross-built как static
ELF, но не был исполнен — arm64 Docker host не имеет x86_64 emulation и возвращает
`exec format error` даже для official `alpine/amd64`. Нужен smoke на настоящем Linux amd64 runner.

## Запуск

Prerequisites: Git checkout с `origin`, Go 1.24+, Node 22.18+ и работающие Docker + Compose.

Полный рекомендуемый flow выполняется одной командой:

```bash
./prototype
```

Она запускает Go evaluator: preflight → public scenario → report → source snapshot adapter fixture
→ ingress. Эквивалентный TypeScript flow:

```bash
./prototype typescript
```

Все focused checks и воспроизводимые measurements:

```bash
./prototype verify
./prototype measure
```

Результаты команд пишутся только в ignored `.prototype-out/` или временный каталог. Никакой
external repository/GitHub App не создаётся.

Для walkthrough trust/state model без toolchain откройте
[`walkthrough.html`](walkthrough.html) двойным кликом.

## Проверенный flow

```text
Assignment checkout
  │ CaseSpec + local git HEAD
  ▼
LocalEvaluator Module ── Docker public scenario ──► EvaluationReport
                                                        │
Platform SourceSnapshotProvider ── SourceSnapshot ──────┤
                                                        ▼
                                                Ingress Module
                                         accept evidence / reject input
```

### Modules и seams

- `LocalEvaluator` имеет один CLI Interface: CaseSpec, Assignment и checkout на входе;
  `EvaluationReport` на выходе. Docker orchestration, cancellation, tool discovery и diagnostic
  mapping скрыты в его implementation.
- Wire seam между local machine и Platform — strict `inside.evaluation-report.v1`. Он не содержит
  Platform status, access decision или GitHub credential.
- GitHub seam живёт на стороне Platform как `SourceSnapshotProvider`. В prototype есть только
  `FixtureSourceSnapshotProvider`; production GitHub App adapter должен выдать тот же
  `inside.source-snapshot.v1` после скачивания exact SHA. Один fixture adapter делает seam пока
  provisional, но уже не позволяет протащить GitHub dependency в evaluator runtime.
- `Ingress` имеет узкий Interface: report + independently obtained snapshot + expected CaseSpec +
  Assignment. Его implementation локализует schema, version, assignment и SHA checks.

Контракты находятся в [`contracts/`](contracts/). Prototype validators намеренно малы и не являются
полной production JSON Schema library; production repositories должны сделать эти schemas общей
conformance corpus и сгенерировать/проверять типы в обоих owners.

## Public scenario и CaseSpec calibration

Versioned CaseSpec: [`case-spec.json`](case-spec.json).

Один public scenario `temporary-partner-failure` использует три ephemeral Docker fixtures:

1. candidate order endpoint принимает burst из 100 order events не дольше пяти секунд и каждый
   request отвечает не дольше 250 ms;
2. delivery выполняется максимум восьмью concurrent partner calls;
3. partner возвращает `503` на первый корректно подписанный call, затем `204`;
4. все 100 событий должны быть доставлены, а backlog — опустеть не дольше пяти секунд;
5. `bad-signature` fixture получает terminal `401` и создаёт диагностируемый
   `signature_rejected`, а не generic timeout.

Wire signature для authoring baseline:

- `X-Inside-Webhook-Timestamp: <unix seconds>`;
- `X-Inside-Webhook-Signature: v1=<lowercase hex HMAC-SHA256>`;
- signed bytes: `<timestamp>.<raw HTTP body bytes>`.

Scenario доказал только representative `503 → retry → 204` и terminal `401`. Полный candidate
retry envelope (`429`, selected `5xx`, connect/read timeout; terminal selected `4xx`) записан в
CaseSpec, но каждый статус должен получить conformance fixture при создании starter repositories.
Algorithm/backoff намеренно не предписан: observable deadline и bounded concurrency важнее pattern.

Authoring baseline на 2026-09-03:

- C# variant — .NET 10 LTS + ASP.NET Core 10; Microsoft указывает поддержку .NET 10 до ноября 2028
  ([official support policy](https://learn.microsoft.com/en-us/dotnet/core/releases-and-support));
- Python variant — Python 3.14 + FastAPI 0.141; Python 3.14 находится в bugfix phase, latest patch
  на дату проверки — 3.14.7 ([Python releases](https://www.python.org/downloads/)), а current
  FastAPI release line подтверждена официальным
  [release log](https://fastapi.tiangolo.com/release-notes/).

Framework parity этим prototype не доказана: fixture написан на Python standard library и проверяет
только общий observable contract. Exact patch/package pins принадлежат будущим starter lockfiles.

## Contract checks

`./prototype verify` зафиксировал:

- Go report accepted;
- TypeScript report accepted;
- bad HMAC signature диагностирована как `signature_rejected`;
- report без required field отклонён как `malformed_report`;
- неизвестная report schema отклонена как `incompatible_report_version`;
- report для другого SHA отклонён как `stale_source_revision`;
- local field `platformStatus=verified` отклонён как `forbidden_report_field`;
- другая CaseSpec version отклонена как `incompatible_case_contract`.

Successful reports на одном warmed Docker cache:

| Candidate | Scenario duration | Full CLI wall time | Result |
|---|---:|---:|---|
| Go | 928 ms | 6.81 s | accepted |
| TypeScript | 923 ms | 7.04 s | accepted |

Full wall time в основном принадлежит Compose build/start/cleanup, поэтому разница языков там не
считается meaningful. Scenario durations показывают одинаковую semantics.

## Go vs TypeScript

Measurements выполнены на macOS arm64, Go 1.26.4, Node 22.23.1, Docker 29.1.3 и Compose 2.40.3.
Startup — 50 отдельных invocations команды `version` после одного warm-up.

| Criterion | Go | TypeScript |
|---|---|---|
| Distribution | Native binary, no runtime | Small source archive + Node runtime |
| macOS arm64 artifact | 2,300,162 bytes, executed | 2,974-byte archive, executed through 112,928,848-byte Node binary |
| Linux amd64 artifact | 2,429,090-byte static ELF, cross-built; execution unconfirmed | Architecture-neutral source; Node/amd64 execution unconfirmed |
| Cold startup p50 / p95 | 2.669 / 4.860 ms | 54.409 / 58.850 ms |
| Docker/Git fit | Standard library process control is sufficient | Node standard library is sufficient |
| Protocol testability | Same shared fixtures and ingress checks | Same shared fixtures and ingress checks |
| Platform ecosystem fit | Separate build toolchain inside Platform ownership | Same language as Platform, simpler contributor context |
| Learner portability | One artifact per OS/arch | Requires supported Node installation or much larger bundled runtime |

Go cross-compilation uses standard `GOOS`/`GOARCH` targets documented by the
[Go toolchain](https://go.dev/doc/install/source). TypeScript prototype uses Node native type
stripping: official Node docs say it is enabled by default from 22.18, while stable status arrives
in later Node lines ([Node TypeScript support](https://nodejs.org/api/typescript.html)). A
production TypeScript candidate should distribute compiled JavaScript, but that does not remove
the Node runtime prerequisite or its startup cost.

### Recommendation

Choose **Go** for the local evaluator/CLI, subject to a real Linux amd64 smoke before the ADR. Keep
the Platform ingress and GitHub adapter in the existing TypeScript Platform. Share only versioned
wire schemas/conformance fixtures—never runtime source packages, credentials or database access.

TypeScript remains a viable fallback if product discovery later proves that installing Node is an
accepted learner prerequisite and evaluator release/packaging must deliberately share the Platform
toolchain. Current evidence does not justify that trade.

## Bounded security review

- Local report is learner-controlled evidence. HMAC in the scenario authenticates the learner's
  webhook payload to the partner fixture; it does **not** authenticate the evaluator report.
- Local Git remote and `HEAD` checks prevent common mistakes, not fraud. Only Platform's GitHub App
  adapter can establish repository ownership and fetch the exact source snapshot.
- The fixture snapshot digest is synthetic and proves contract wiring only. Production must hash
  the fetched archive and retain its provenance.
- Evaluator receives no Platform/GitHub secret and never invokes GitHub. Participant code runs only
  in the participant's local Docker topology.
- Raw Compose logs are not inserted into the report. Structured diagnostic fields are bounded;
  production still needs explicit size limits and secret redaction before accepting diagnostics.
- Ingress accepts a structurally valid failed local report as Attempt evidence, but `Verified`
  remains a later Platform decision requiring all product layers.

## Known limits and deletion test

- Linux amd64 and Windows runtime execution are not confirmed.
- GitHub App permissions, archive download, device authentication and one-time attempt draft are
  represented only by contracts/fixtures.
- No C# or FastAPI starter solution is implemented; cross-variant conformance remains future
  authoring work.
- No cryptographic honesty claim, remote hidden scenario, persistence, production service or
  migration exists.
- Deleting this directory and branch removes every prototype artifact without touching production
  data or contracts.
