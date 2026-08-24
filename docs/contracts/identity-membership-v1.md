# Inside Identity and Membership contract v1

Статус: cross-repository contract для
[Workspace Specification #65](https://github.com/sachkov-inside/workspace/issues/65).

Этот документ задаёт общую authority boundary, wire envelope и conformance corpus между Platform
и будущей Telegram application. Он не задаёт application schema, HTTP framework, database tables,
deployment или secret distribution. Каждый repository хранит собственную implementation и
проверяет её против versioned snapshot этого контракта без runtime import соседнего checkout.

## Authority matrix

| Authority | Доказывает или решает | Не даёт |
|---|---|---|
| Email Identity Provider | Контроль External identity для Platform sign-in | Membership, Platform permission или content access |
| Platform | Principal, Platform session/account, permissions, Member Profile, Membership Entitlement и каждый ContentAccess decision | Telegram identity proof или raw chat status |
| Telegram application | Контроль одной Telegram identity, linking invariants и bounded Membership Evidence | Platform session, entitlement, role или final content access |
| Канонический закрытый Telegram chat | Membership Signal через фактическое присутствие linked identity | Platform identity или permanent entitlement |
| Tribute/payment provider | Может менять roster через отдельный operational lifecycle | Identity, evidence или entitlement напрямую |

Member Profile является member-visible presentation и не участвует ни в одной authority chain.
Email, Platform/Telegram internal identifiers, linking/evidence/security history и provider claims
не входят в profile projection. Anonymous visitor, non-member и crawler не получают этот profile.

## Contract identity and evolution

Contract identifier v1 — `inside.membership-evidence.v1`. Consumer принимает только явно
поддерживаемый major version; unknown/missing major version fails closed как
`unsupported_contract`. V1 schema закрыта для неизвестных fields: добавление field, изменение
meaning/required field или reason code требует нового major contract и одновременного bounded
migration plan в обоих owning repositories.

Workspace хранит normative contract и scenarios. Platform и Telegram repositories vendor-ят
versioned snapshot/schema/fixtures в свою test authority; они не читают Workspace во время build,
test или runtime.

Normative machine-readable artifacts:

- [`identity-membership-v1.schema.json`](identity-membership-v1.schema.json) — JSON Schema envelope;
- [`identity-membership-v1.fixtures.json`](identity-membership-v1.fixtures.json) — deterministic
  named consumer/provider corpus. Поле `expected` задаёт contract outcome, а fixture `clock` —
  время consumer validation.

## Normalized Membership Evidence envelope

Envelope переносит normalized application facts, а не provider model:

| Field | Contract |
|---|---|
| `contractVersion` | Ровно `inside.membership-evidence.v1` для этого major |
| `principalRef` | Opaque Platform-issued integration reference bound to one Principal; не email и не raw Principal ID |
| `decision` | `member`, `not_member`, `identity_not_linked`, `identity_conflict` или `unavailable` |
| `reasonCode` | Stable reason из таблицы ниже, согласованный с `decision` |
| `checkedAt` | UTC instant authoritative observation; отсутствует, если observation не состоялось |
| `validUntil` | UTC instant finite evidence validity; обязателен для `member`/`not_member` |
| `telegramIdentityRef` | Opaque Telegram-owned reference; обязателен только для linked identity |
| `evidenceRef` | Opaque audit/correlation reference; обязателен для состоявшегося observation |
| `evidenceVersion` | Monotonic version для одной linked identity; older/replayed version не заменяет newer evidence |

Positive `member` evidence удовлетворяет `validUntil > checkedAt` и
`validUntil <= checkedAt + 5 minutes`. `not_member` прекращает новые protected operations сразу;
его finite validity не превращает deny в permanent member flag. `identity_not_linked`,
`identity_conflict` и `unavailable` не создают Membership Entitlement. Expired, malformed,
cross-Principal или unsupported evidence fails closed.

Envelope никогда не содержит email, raw Platform Principal ID, Telegram user ID/username,
`ChatMember`, OIDC access/ID token, bot token, payment/subscription data или provider exception.

## Stable decision and reason codes

| Decision | Allowed `reasonCode` | Meaning |
|---|---|---|
| `member` | `chat_member` | Linked identity сейчас присутствует в каноническом chat |
| `not_member` | `chat_not_member` | Authoritative observation подтверждает отсутствие/removal |
| `identity_not_linked` | `identity_not_linked` | Principal ещё не имеет verified active Telegram link |
| `identity_conflict` | `identity_conflict` | Verified Telegram identity historically/actively связана иначе; silent transfer запрещён |
| `unavailable` | `provider_unavailable` | Authoritative observation сейчас нельзя получить |

Consumer-local validation failures используют `unsupported_contract`, `invalid_evidence`,
`principal_mismatch`, `expired_evidence` или `replayed_evidence` и не принимаются как provider
decision. Platform маппит accepted/failed evidence в собственные ContentAccess reason codes; IdP
или Telegram codes не становятся permissions.

## Linking and recovery invariants

- Link начинается только из recently authenticated Platform session. Single-use link transaction
  связывает её с opaque `principalRef`; email или Telegram ID от caller не принимается как proof.
- Durable Telegram identity определяется verified provider identity, а не username/display name,
  picture, phone или похожий email.
- Одна Telegram identity исторически принадлежит одному Principal; unlink сохраняет tombstone и не
  освобождает identity для silent transfer.
- Same Principal + same identity link идемпотентен. Conflict никогда не делает auto-merge.
- Exceptional transfer требует отдельного audited owner recovery; его operational procedure не
  определяется v1 wire contract.
- Membership removal не удаляет link/profile/history. Rejoin может дать newer positive evidence
  без нового Platform account или Telegram relink.

## Normative conformance corpus

Оба owning repositories реализуют эти scenarios одним и тем же именованным fixture corpus. Exact
transport setup и application assertions принадлежат repository, но input facts и expected
contract outcome не меняются.

| Fixture | Input fact | Expected contract outcome |
|---|---|---|
| `linked-member-fresh` | Linked identity, authoritative member observation | `member/chat_member`, finite evidence no longer than five minutes |
| `linked-non-member` | Linked identity, authoritative left/kicked/non-member observation | `not_member/chat_not_member`, immediate deny for new operations |
| `member-removed` | Newer negative follows positive evidence | Once observed, negative supersedes still-unexpired older positive evidence |
| `member-rejoined` | Newer positive follows confirmed removal | Access can return without relink; version increases |
| `identity-not-linked` | Principal has no verified Telegram link | `identity_not_linked/identity_not_linked`; no entitlement |
| `identity-conflict` | Telegram identity is bound to another Principal | `identity_conflict/identity_conflict`; no merge/transfer |
| `provider-unavailable` | No authoritative observation can be obtained | `unavailable/provider_unavailable`; stale/absent evidence fails closed |
| `positive-expired` | `validUntil` is not in the future | Consumer rejects as `expired_evidence` |
| `positive-over-five-minutes` | Positive validity exceeds five minutes | Consumer rejects as `invalid_evidence` |
| `principal-mismatch` | Evidence `principalRef` differs from requesting Principal binding | Consumer rejects as `principal_mismatch` |
| `replayed-version` | Evidence version is older/equal to an already consumed different effect | Consumer rejects as `replayed_evidence` |
| `unsupported-major` | Contract major is unknown/missing | Consumer rejects as `unsupported_contract` |
| `malformed-envelope` | Required field/decision/reason combination is invalid | Consumer rejects as `invalid_evidence` |

Provider-side tests prove normalized outcomes and monotonic evidence. Consumer-side tests prove
validation, bounded entitlement and fail-closed mapping. Cross-repository integration later joins
the independently passing implementations; production credentials and enablement remain separate
owner gates.

## Delivery ownership

- [Platform specification #48](https://github.com/sachkov-inside/platform/issues/48) owns
  sign-in/Principal/session, Platform Account, Member Profile, authorization, entitlement and the
  consumer/test adapters.
- [Platform #49](https://github.com/sachkov-inside/platform/issues/49) delivers IdP/Principal/session,
  [#50](https://github.com/sachkov-inside/platform/issues/50) ContentAccess/entitlement,
  [#51](https://github.com/sachkov-inside/platform/issues/51) Account/Member Profile и
  [#52](https://github.com/sachkov-inside/platform/issues/52) final convergence.
- [Workspace #60](https://github.com/sachkov-inside/workspace/issues/60) bootstraps the Telegram
  repository after contract acceptance plus explicit repository/operator confirmations; it does
  not wait for completed Platform protected-content implementation.
- The new Telegram repository creates its own root Specification and owns OIDC linking,
  uniqueness/recovery, `getChatMember` observation and provider-side contract tests.

Telegram commands, messaging, notifications, Tribute/billing, anonymous internet-public profiles,
social graph, production deployment and credentials are outside this contract.
