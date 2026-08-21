# Telegram and Tribute Membership access for Sachkov Inside Platform

**Status:** decision-grade research for [Workspace issue #41](https://github.com/sachkov-inside/workspace/issues/41)

**Snapshot:** 2026-08-21

**Decision owner:** product owner; this report is not an ADR

## Executive decision

Use **application-owned Telegram linking** after the user has authenticated by email. Telegram's
current OpenID Connect implementation is real and standards-based: Authorization Code Flow,
PKCE, discovery and JWKS are live. Store `(iss, sub)` as the durable external identity and store
the separate Telegram profile claim `id` as the candidate join key for Tribute. Do not turn
Telegram into the primary Platform login method and do not put Membership authorization in Logto
or another identity provider.

Telegram linking is technically **go, subject to one credentialed staging proof**. The proof must
show that the OIDC `id` for one real account equals its Bot API user ID and the
`telegram_user_id` delivered by Tribute. Telegram documents all three as Telegram user
identifiers, but neither Telegram nor Tribute explicitly guarantees their cross-product equality,
and Telegram's example shows that OIDC `sub` and `id` are different claims. Automatic access is
no-go until this join is observed with the same user.

Treat Tribute as **conditional, not yet go for unattended production authorization**. Its public
contract provides signed `new_subscription`, `renewed_subscription` and
`cancelled_subscription` webhooks with `expires_at`, but it does not provide a stable event ID,
terminal expiry/payment-failure/refund events, documented ordering, or a supported public member
backfill/reconciliation API. A `/subscribers` operation exists in the public OpenAPI document but
is marked `x-internal: true`; it cannot be a production dependency without written support from
Tribute.

If the Tribute gates in this report pass, use webhook-first ingestion into a durable inbox,
reconcile against a supported full member snapshot, and compute a local Membership entitlement
from the verified Telegram link plus a current external subscription. If they do not pass, use a
time-bounded owner-reviewed fallback for a small pilot or choose another external access provider
with a supported member lifecycle API. Do not grant indefinitely from a receipt, username,
webhook alone, or stale identity token.

## Product and authority boundary

The confirmed Platform brief requires one closed-access level, email authentication, a linked
Telegram account, and access based on an external Membership signal. The Platform does not take
payment or manage subscription terms. The application remains authoritative for access to
Platform content even when Tribute remains authoritative for payment and Telegram channel access
([Platform v1 brief](../../product/platform-mvp-brief.md)).

```text
Email authentication                    External evidence
--------------------                    -----------------
Logto/other IdP -> Principal             Telegram OIDC -> ExternalIdentity
                                                  |
Tribute webhook -> WebhookInbox -> ExternalSubscription
                                                  |
                         exact telegram_user_id join
                                                  v
                                      MembershipEntitlement
                                                  |
                                    Platform authorization
```

These facts must stay separate:

- authentication answers who owns the current Platform session;
- Telegram OIDC proves control of one Telegram identity;
- Tribute reports an external subscription observed for a Telegram user;
- the Platform evaluates the current application entitlement on each protected request.

No IdP role, Telegram username, Tribute email, browser token or channel membership alone grants
Membership.

## What primary sources prove

| Question | Proven contract | Remaining gap |
|---|---|---|
| Is modern Telegram Login OIDC? | Telegram documents Authorization Code Flow, PKCE, discovery, token and JWKS endpoints. | A real BotFather client is still required to test the full callback. |
| What identifies the Telegram account? | OIDC `sub` is the subject; `profile` adds a Telegram user `id`. Bot API user IDs are unique integers with at most 52 significant bits. | Telegram does not state that `sub == id`; its example uses different values. |
| Can Telegram link after email login? | The OIDC flow can be initiated as a separate proof and its result can be associated with the already authenticated Principal. | Anti-relink and recovery policy are application responsibilities. |
| Is a bot required? | Telegram requires a bot to represent the OIDC client and BotFather supplies client ID/secret. | Whether to reuse an existing branded bot is an owner/security decision. |
| Can Tribute events identify the same Telegram user? | Subscription payloads contain required `telegram_user_id` as `int64`; `trb_user_id` is a separate Tribute ID. | Cross-product equality with Telegram OIDC `id` needs a same-user fixture. |
| Are Tribute webhooks authenticated? | `trbt-signature` is HMAC-SHA256 over the request body using the API key. | Encoding, prefix, replay window and key rotation are undocumented. |
| Is the subscription lifecycle complete? | New, renewal and cancellation events include event/send times and `expires_at`. | No documented expired, failed-payment, refund or resume event; cancellation timing is unclear. |
| Can missed events be reconciled? | OpenAPI exposes `/subscribers` with active/pre-cancelled/cancelled and expiry fields. | The operation is marked internal, has no public page/pagination contract and is not a supported dependency yet. |

Primary contracts: [Telegram Login](https://core.telegram.org/bots/telegram-login),
[Telegram OIDC discovery](https://oauth.telegram.org/.well-known/openid-configuration),
[Telegram JWKS](https://oauth.telegram.org/.well-known/jwks.json),
[OpenID Connect Core subject identifiers](https://openid.net/specs/openid-connect-core-1_0.html#SubjectIDTypes),
[Telegram Bot API user](https://core.telegram.org/bots/api#user),
[Telegram Bot API IDs](https://core.telegram.org/api/bots/ids),
[Tribute API authorization](https://wiki.tribute.tg/for-content-creators/api-documentation.md),
[Tribute webhooks](https://wiki.tribute.tg/for-content-creators/api-documentation/webhooks.md), and
[Tribute OpenAPI](https://tribute.tg/api/v1/openapi/en).

## Live read-only verification

The following public checks were run on 2026-08-21 without owner credentials, payments or
external writes.

### Telegram discovery and keys

```bash
curl -fsSL https://oauth.telegram.org/.well-known/openid-configuration | jq .
curl -fsSL https://oauth.telegram.org/.well-known/jwks.json \
  | jq '{keys: [.keys[] | {kty,kid,use,alg,crv}]}'
```

The discovery request returned HTTP 200 and advertised only authorization code response/grant,
`S256` and `plain` PKCE, `public` subjects, the `openid profile phone telegram:bot_access` scopes,
and `RS256`, `ES256`, `EdDSA`, `ES256K` ID-token algorithms. Use only `S256` and pin an allowed
algorithm (`RS256` initially); never accept the JWT header's algorithm without configuration.
The JWKS request returned current verification keys for all four advertised algorithms.

There is no advertised UserInfo, revocation, introspection or end-session endpoint. Telegram also
states that requested user claims are returned in the ID token rather than from UserInfo. The
discovery metadata does not list the documented profile claim `id` or `nonce` in
`claims_supported`; this mismatch is another reason to run the credentialed flow before design
freeze.

### Tribute specification and protected routes

```bash
curl -fsSL https://tribute.tg/api/v1/openapi/en
curl -i https://tribute.tg/api/v1/subscriptions
curl -i https://tribute.tg/api/v1/subscribers
```

The OpenAPI request returned HTTP 200 as a version `1.0.0` YAML document. Both protected GETs
returned HTTP 401 with `error_not_permitted`, proving that the routes exist and require an API key;
this does not prove that the internal subscribers route is supported for third-party production
use. A real result, rate limit, pagination behavior and consistency lag cannot be tested without
the owner's Tribute key.

## Telegram linking contract

### Protocol

Prefer the generic OIDC Authorization Code Flow over the legacy iframe and the convenience popup
flow. Telegram's manual contract uses:

- authorization endpoint `https://oauth.telegram.org/auth`;
- token endpoint `https://oauth.telegram.org/token`;
- discovery issuer `https://oauth.telegram.org`;
- exact BotFather-registered redirect URI;
- `response_type=code`, scopes `openid profile`, random `state`, and PKCE `S256`;
- server-side code exchange with `client_secret_basic`;
- server-side ID-token signature and claim validation.

Request neither `phone` nor `telegram:bot_access` for v1. Phone is unnecessary personal data for
the Membership join. Bot messaging permission is a different product capability and can be added
later with an explicit consent decision. Telegram's current scopes and flow are documented in
[Telegram Login](https://core.telegram.org/bots/telegram-login); PKCE for confidential web clients
is also recommended by [OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html#section-2.1.1).

### Safe link sequence

1. Require an authenticated Platform session and recent primary email re-authentication.
2. Create a short-lived, single-use server transaction bound to the Principal and session. Store
   hashes of `state` and `nonce`, the PKCE verifier, creation/expiry times and intended operation.
3. Redirect with an exact registered callback, `openid profile`, random `state`, `nonce` and PKCE
   `S256`. The credentialed spike must verify that Telegram echoes nonce in the code flow.
4. Consume state exactly once before exchanging the code. Never accept Principal/email/target
   account from callback query parameters.
5. Exchange the code server-side with the exact redirect URI and client credentials.
6. Validate signature against the configured algorithm and current JWKS; validate exact issuer,
   audience containing the Bot client ID, non-empty subject, expiry, issued-at freshness and nonce.
   Follow the [OIDC ID-token validation rules](https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation).
7. Normalize `sub` as an opaque case-sensitive string. Normalize profile `id` as a decimal string
   at JSON boundaries and an exact representation with at least signed 64-bit range in the
   eventual Platform store. Never use a 32-bit type.
8. In one transaction, enforce global identity and Telegram-ID uniqueness, record an audit event,
   consume the link transaction and attach the identity to the current Principal.
9. Linking is idempotent only when the same identity is already attached to the same Principal.
   It does not itself create Membership entitlement.

### Identifier policy

Use both identifiers because they answer different questions:

| Value | Use | Never use it for |
|---|---|---|
| `iss + sub` | Durable Telegram OIDC identity and provenance. OIDC public subjects are locally unique and never reassigned within the issuer. | Joining to Tribute until Tribute documents or a fixture proves a mapping. |
| OIDC profile `id` | Candidate raw Telegram user ID; exact join to Tribute `telegram_user_id` after the proof gate. | Replacing the OIDC subject or skipping token validation. |
| `preferred_username` | Display/audit snapshot only. | Identity, joining, recovery or uniqueness. |
| phone/name/picture | Optional display/contact data only if separately justified. | Automatic merge or account recovery. |
| Tribute `trb_user_id` | Tribute-local provenance (`T-...` or `W-...`). | Telegram identity; legacy `user_id` is explicitly deprecated. |

Telegram says Bot API user identifiers are unique, can exceed 32 bits and have at most 52
significant bits. Telegram further documents that MTProto user IDs equal Bot API user dialog IDs
([Bot API IDs](https://core.telegram.org/api/bots/ids)). Changing a phone preserves a Telegram
account, while deletion and later sign-up creates a new account
([Telegram account FAQ](https://telegram.org/faq#q-how-do-i-change-my-phone-number)). Therefore
never transfer an old link because a new account has the same phone or username.

### Anti-relink and recovery rules

- Unique active `(provider, issuer, subject)` across all Principals.
- Unique active `(provider, telegram_user_id)` across all Principals.
- At most one active Telegram identity per Principal for v1.
- An identity linked to another Principal enters `conflict`; never auto-merge or reassign it.
- Replacing an existing link requires recent email re-auth plus proof of the currently linked
  Telegram identity, an explicit confirmation, security notification and immutable audit.
- If current-Telegram proof is impossible, owner support uses a documented recovery policy. Email,
  phone, username, screenshot or display name alone is insufficient.
- Unlink is immediate for future authorization, retains a tombstone/audit and does not delete
  subscription history. It does not make the same Telegram identity silently claimable elsewhere.
- Telegram exposes user-side reset of connected web authorization, but no RP backchannel
  revoke/logout webhook is documented
  ([`account.resetWebAuthorization`](https://core.telegram.org/method/account.resetWebAuthorization)).
  Local unlink/recovery cannot depend on receiving such a notification.

## Telegram-to-Tribute join

Tribute describes `telegram_user_id` as the user's Telegram ID and uses `int64`. Telegram describes
the OIDC profile `id` as the user ID and Bot API `User.id` as the unique Telegram user identifier.
This is strong semantic alignment, but still an inference across two independent contracts.

The required proof fixture is one consenting staging user observed in all three places:

```text
Telegram OIDC profile id == Bot API User.id == Tribute webhook telegram_user_id
```

Also capture OIDC `sub` separately and prove it is stable across two logins. Do not require
`sub == id`. If the three numeric IDs differ or Tribute sends a missing/ambiguous ID, quarantine
the evidence and deny automatic access.

Events may arrive before a user links Telegram. Store the external subscription keyed by provider
connection and Telegram ID without a Principal. Once a verified identity with the same numeric ID
is linked, recompute the entitlement. This avoids discarding legitimate pre-existing members and
does not weaken the identity proof.

## Tribute lifecycle contract

### Documented webhook surface

Tribute documents a `trbt-signature` header containing HMAC-SHA256 of the request body with the
creator API key. Verify the exact raw bytes before JSON parsing and compare in constant time. The
documentation does not state whether the header is lower/uppercase hex, Base64 or prefixed, so the
handler cannot be finalized safely without a canonical test vector or a real delivery
([webhook contract](https://wiki.tribute.tg/for-content-creators/api-documentation/webhooks.md)).

Subscription webhooks have an envelope of `name`, `created_at`, `sent_at` and `payload`. The public
OpenAPI defines these events:

| Event | Confirmed payload facts | Provisional meaning until staging proof |
|---|---|---|
| `new_subscription` | Subscription/period IDs, type, money fields, Tribute/Telegram user IDs, channel, `expires_at`. | Paid/trial/gift access observed through the reported expiry. |
| `renewed_subscription` | Same core IDs and a new `expires_at`; gift/trial renews as `regular`. | Extend/restart access through the newer expiry. |
| `cancelled_subscription` | Same core IDs, `cancel_reason` and `expires_at`. | Auto-renew is off; keep paid-through access until expiry, not immediate revocation. This interpretation must be confirmed. |

There is no event/delivery ID. `type` is required for renewal but optional in the new/cancelled
schemas. Webhook periods enumerate only monthly/quarterly/yearly while the subscription catalog
also lists trial, one-time, weekly and half-yearly. `telegram_user_id` is required even though
`trb_user_id` documents email-authorized `W-...` users. These schema gaps must be handled as
unknowns, not guessed away ([Tribute OpenAPI](https://tribute.tg/api/v1/openapi/en)).

### Cancellation, failed payment, expiry and gift gaps

Tribute lets a subscriber cancel and documents that deleting a creator subscription stops future
renewal while existing subscribers retain access until expiry
([subscriber management](https://wiki.tribute.tg/for-subscribers/subscription-management.md),
[creator deletion](https://wiki.tribute.tg/for-content-creators/subscriptions/how-to-delete-subscription.md)).
This supports, but does not prove, the paid-through interpretation of `cancelled_subscription`.

Tribute separately documents a seven-day period of repeated charges after a failed payment and
channel removal only after the period ends
([deferred removal](https://wiki.tribute.tg/for-content-creators/subscriptions/deferred-subscriber-removal-for-failed-payments.md)).
It does not say whether webhook `expires_at` includes that grace, which webhook marks final failure,
or whether Platform access is expected to mirror channel access during it. Do not invent a
seven-day local grace until this is answered.

Gift access is activated through a unique link sent to the recipient
([gift subscription](https://wiki.tribute.tg/for-content-creators/subscriptions/gift-subscription.md)).
The webhook documentation does not say whether the event occurs at purchase or redemption or
whether its Telegram ID belongs to buyer or recipient. Refund/chargeback behavior for
subscriptions is also absent from the public API and event list.

### Delivery and retry gaps

The current canonical webhook page lists retries after 5m, 15m, 30m, 1h, 2h, 4h, 8h and 8h,
approximately one day. A separate current integration guide still lists 5m, 15m, 30m, 1h and 10h
and tells implementers to be idempotent
([integration guide](https://wiki.tribute.tg/for-content-creators/info-products-and-content/api-integration.md)).
Ordering, timeout, retry-triggering status codes, duplicate guarantees, whether `sent_at` changes,
and event retention/replay are not documented.

Design for duplicate, late, missing and out-of-order delivery. HMAC authenticates bytes but does
not prevent replay because the contract provides no signed delivery ID or replay window.

## Application data model

The names below describe ownership and invariants, not final ORM mappings.

### `external_identity`

| Field | Purpose |
|---|---|
| `id`, `principal_id` | Application identity and owner. |
| `provider`, `issuer`, `subject` | `telegram`, exact issuer and opaque OIDC `sub`. |
| `telegram_user_id` | Verified OIDC profile `id` in an exact representation with at least signed 64-bit range; serialize it as a decimal string at JSON boundaries. |
| `status` | `active`, `unlinked`, `conflict`, `recovery_hold`. |
| `verified_at`, `unlinked_at`, `last_seen_at` | Lifecycle/audit timestamps. |
| display snapshots | Optional name/username only for support; never identity keys. |

Enforce unique provider/issuer/subject, unique active provider/Telegram ID and one active Telegram
identity per Principal. Keep a tombstone after unlink.

### `webhook_inbox`

| Field | Purpose |
|---|---|
| `id`, `provider_connection_id`, `received_at` | Durable delivery identity and tenant/key boundary. |
| `raw_body`, `body_sha256`, `signature` | Exact verification/audit input with bounded retention and protected access. |
| `signature_status`, `schema_version`, `event_name` | Admission result and decoder selection. |
| `provider_created_at`, `provider_sent_at` | Provider times; never replace server receipt time. |
| `semantic_fingerprint` | Provisional dedupe hash excluding `sent_at`; not treated as a provider guarantee. |
| `processing_status`, `attempt_count`, `next_attempt_at`, `processed_at`, `error_code` | Async processing, retry and dead-letter state. |

Commit the inbox row before acknowledging delivery. Keep raw bytes at least through the provider
retry/reconciliation window, then retain a body hash and redacted audit according to the eventual
privacy policy.

### `external_subscription`

| Field | Purpose |
|---|---|
| `id`, `provider_connection_id` | Local aggregate and Tribute creator/account boundary. |
| `telegram_user_id`, `trb_user_id` | Correlation key and Tribute-local provenance. |
| `provider_subscription_id`, `provider_period_id`, `provider_channel_id` | Whitelisted product/period/channel facts. |
| `kind` | `regular`, `gift`, `trial`, or `unknown`. |
| `state` | `active`, `non_renewing`, `expired`, `unknown`, `disputed`. |
| `valid_from`, `valid_until` | Observed access interval; `valid_until` comes from `expires_at`. |
| `last_provider_created_at`, `last_inbox_id` | Ordering and evidence pointer. |
| `last_reconciled_at`, `reconciliation_source` | Snapshot freshness and provenance. |

Use `(provider_connection_id, telegram_user_id, provider_subscription_id)` as the provisional
aggregate key, subject to real gift and multi-period fixtures. Whitelist the Inside subscription
and channel IDs; a validly signed event for a different creator product must not grant Inside.

### `membership_entitlement`

| Field | Purpose |
|---|---|
| `principal_id`, `entitlement_key` | Application authorization key, one `inside_membership` level in v1. |
| `state` | `granted`, `denied`, `manual_hold`, `conflict`. |
| `valid_from`, `valid_until` | Bounded effective window. |
| `external_identity_id`, `external_subscription_id` | Exact evidence chain. |
| `evaluated_at`, `reason_code`, `evidence_version` | Deterministic policy/audit. |

Entitlement is a rebuildable projection, not a mutable flag copied into the IdP. Every protected
request evaluates the current projection and `valid_until`; an already issued login session does
not preserve expired Membership.

Time-bounded manual adjustments, if approved, belong in a separate audited record with owner,
reason, evidence, creation and mandatory expiry. They never rewrite Tribute facts.

## Access state machine

Identity and subscription evolve independently. The entitlement is their join.

```text
IDENTITY

UNLINKED -- verified OIDC + uniqueness --> LINKED
LINKED   -- local unlink ---------------> UNLINKED (audit/tombstone retained)
any      -- duplicate/relink mismatch --> CONFLICT (deny, manual recovery)

EXTERNAL SUBSCRIPTION

NONE -- new(valid future expiry) ----------------> ACTIVE(until T)
ACTIVE -- renewal(newer evidence) ---------------> ACTIVE(until later T)
ACTIVE -- cancellation(newer evidence) ----------> NON_RENEWING(until T)
NON_RENEWING -- renewal(newer evidence) ----------> ACTIVE(until later T)
ACTIVE/NON_RENEWING -- clock reaches T ----------> EXPIRED
EXPIRED -- late new/renewal with future expiry ---> ACTIVE(until T)
any -- contradictory/invalid provider evidence --> DISPUTED

ENTITLEMENT

LINKED + ACTIVE/NON_RENEWING + now < T + whitelisted product -> GRANTED(until T)
otherwise                                                   -> DENIED/CONFLICT
```

Processing rules:

- A duplicate transition is a no-op with an audit reference.
- For new/renewal, only newer logical evidence may extend access. An older delivery never shortens
  or rolls back a newer period.
- A logically newer cancellation may set non-renewing and its reported expiry. If it unexpectedly
  shortens a known paid-through interval, quarantine until cancellation semantics are proven.
- Compare provider `created_at` for logical order, record `sent_at`, and always retain local
  `received_at`. Equal/contradictory versions become `disputed`, not last-write-wins.
- Expiry is enforced by the authorization clock, not only by a scheduled worker. A worker updates
  projections/notifications, but a delayed job cannot extend access.
- If a renewal is missed, access fails closed at the last proven expiry. A later valid renewal
  reactivates it. Any product grace must be an explicit owner decision backed by provider facts.
- Unlink immediately removes the Principal join while retaining the unclaimed external
  subscription; re-linking the same verified Telegram ID can restore still-current access.

## Idempotent webhook processing

1. Apply TLS, request-size and content-type limits; capture exact raw bytes.
2. Look up the provider connection/key version without logging the key.
3. Verify `trbt-signature` over raw bytes using the confirmed encoding and constant-time compare.
4. Insert a delivery into `webhook_inbox`; acknowledge success only after durable commit.
5. Parse a versioned schema asynchronously. Preserve unknown fields and quarantine unknown event
   names rather than granting.
6. Derive a provisional semantic fingerprint from provider connection, event name,
   `telegram_user_id`, subscription/period IDs, `expires_at` and `created_at`, excluding
   retry-oriented `sent_at`.
7. In one transaction, lock/upsert the external subscription conditionally on evidence order,
   record the applied/no-op/disputed result and rebuild affected entitlement.
8. Retry transient processing errors internally. Dead-letter permanent schema/conflict errors and
   alert without causing an infinite provider retry storm.

The semantic fingerprint is only a dedupe aid because Tribute supplies no event ID and has not
promised which fields remain stable on redelivery. Correctness comes from idempotent conditional
state transitions, not from trusting that fingerprint.

## Reconciliation and recovery

A webhook-only feed cannot backfill existing subscribers or prove that no event was missed. The
supported public `/subscriptions` endpoint returns the creator's catalog, not member status
([Subscriptions API](https://wiki.tribute.tg/for-content-creators/api-documentation/subscriptions.md)).
The broader OpenAPI exposes `/subscribers?subscriptionID=...` with Telegram ID, status
`active|pre_cancelled|cancelled`, activation and expiry, but marks it `x-internal: true` and gives
no pagination or consistency contract.

Production reconciliation requires either a supported version of that operation or another
Tribute-provided full export/API with these properties:

- complete snapshot for a specific creator subscription and channel;
- stable Telegram user ID plus paid-through expiry and cancellation state;
- documented pagination, consistency lag, rate limits and snapshot completeness marker;
- safe repeated reads and an initial backfill path;
- defined behavior for trials, gifts, refunds, grace, manual removal and reactivation.

Once available:

1. Take a complete initial snapshot before enabling automatic closed-content access.
2. Reconcile frequently enough to recover within the agreed access RTO; choose the interval only
   after observing limits and snapshot size. Also expose a rate-limited user “refresh access” path.
3. Mark every row with a reconciliation run ID. Treat absence as evidence only after a complete,
   successful snapshot; never revoke from a partial page or failed run.
4. Replay the durable inbox after decoder/processing repairs, then reconcile to authoritative
   current state.
5. Alert when the last complete snapshot is older than two intended intervals, webhook delivery
   is silent unexpectedly, unknown events appear, or inbox lag approaches a known expiry.

### Manual fallback

For a bounded pilot, the owner may issue a short manual adjustment only after checking provider
evidence that contains the exact verified Telegram ID and paid-through date. Username, receipt
screenshot or payment email alone is insufficient. Record reason/evidence and expire the override
automatically; suggested maximum is seven days pending an owner decision.

If Tribute offers no supported identity-bearing export, the safe fallback is “access pending
manual review” or another provider, not indefinite access. Public/free content remains available
during integration outages; protected content fails closed after the last proven expiry.

## Failure and error table

| Failure | Detection | Access behavior | Recovery |
|---|---|---|---|
| Email session absent/stale at link start | Session/re-auth check | No link; existing access unchanged. | Re-authenticate by primary method. |
| Telegram authorization denied/expired | Callback error or expired transaction | No link. | Start a new transaction. |
| State, PKCE or nonce mismatch/replay | Single-use transaction validation | No link; security alert on repetition. | Discard transaction; investigate session compromise. |
| Bad Telegram signature/issuer/audience/algorithm/time | Strict ID-token validation | No link. | Refresh JWKS only by policy; retry new login, then escalate. |
| Missing/invalid OIDC `id` | Claim/range validation | No automatic Membership join. | Quarantine and contact Telegram support. |
| Telegram identity already linked elsewhere | Unique constraint | `conflict`, deny transfer. | Audited recovery with both proofs/owner policy. |
| Principal already has another Telegram link | Unique constraint | Keep current link; deny replacement. | Explicit replace/recovery flow. |
| Telegram provider unavailable | Discovery/token failure metrics | Existing bounded entitlement continues; no new link. | Retry with backoff; show status. |
| Tribute signature absent/invalid | Raw-body HMAC verification | No state change. | Return confirmed auth error behavior, alert and check key/encoding. |
| Tribute payload malformed/unknown | Versioned decoder | No grant; store/quarantine if authenticated. | Fix decoder/support case, replay inbox. |
| Valid event for wrong subscription/channel | Allowlist | No grant; audit. | Correct provider configuration. |
| Missing/mismatched Telegram/Tribute identity | Join constraints | External record remains unclaimed/disputed. | Real identity proof or provider correction. |
| Exact duplicate webhook | Inbox hash/fingerprint and idempotent transition | No duplicate effect. | Acknowledge and retain audit. |
| Out-of-order old event | Evidence ordering | No rollback of newer state. | Audit; reconcile. |
| Contradictory same/newer event | Invariant checks | `disputed`, fail closed if current access cannot be proven. | Reconcile/provider support/manual review. |
| Database unavailable at ingestion | Inbox commit fails | No state change; provider should retry. | Restore DB; monitor retry horizon. |
| Processor unavailable after inbox commit | Inbox lag | Existing access only until proven expiry. | Internal retry/replay; alert before expiry. |
| Missed webhook beyond provider retries | Reconciliation drift | Correct from supported snapshot; otherwise no silent extension. | Full reconcile/manual bounded review. |
| Cancellation before expiry | Newer cancellation plus `expires_at` | Provisional non-renewing until T. | Confirm semantics; timer denies at T unless renewed. |
| Failed payment/grace ambiguity | Provider response/event mismatch | Do not invent grace. | Supported snapshot or owner-approved temporary policy after proof. |
| Clock reaches `valid_until` | Request-time entitlement evaluation | Deny immediately; keep account/read state. | Valid renewal/reconcile reactivates. |
| Renewal arrives late | Valid newer future expiry | Reactivate; record access gap. | Monitor provider latency and reconcile. |
| Refund/chargeback without event | Reconciliation/support discrepancy | Cannot guarantee prompt revocation: hard go/no-go gap. | Provider contract or alternative provider. |
| Provider key compromised/rotated | Secret incident/audit | Pause ingestion that cannot be authenticated; preserve last bounded state. | Rotate with confirmed dual-key procedure, replay/reconcile. |

## Bot boundary

Telegram requires a bot object to represent the OIDC application. It does **not** require a
separate bot deployment, worker or repository when the bot is used only as Login/OIDC client.
BotFather manages allowed URLs and client credentials; the Bot API token is a separate secret and
is not needed to validate OIDC ID tokens.

Reuse an existing bot only if it represents the same Inside Platform brand/trust boundary, is
owned by the same operator and its client secret can be isolated. Otherwise create one dedicated
Inside Platform login bot. In either case:

- keep the OIDC adapter and secrets inside the autonomous Platform repository/deployment;
- do not make the login bot a channel administrator for this flow;
- do not request `telegram:bot_access` until direct messages are an approved requirement;
- keep Tribute's official `@Tribute` bot separate. Tribute requires it to administer the paid
  private channel and warns that direct invite links bypass its subscription access flow
  ([connect Tribute](https://wiki.tribute.tg/for-content-creators/how-to-connect-the-bot.md),
  [publish a subscription](https://wiki.tribute.tg/for-content-creators/subscriptions/subscription-publishing.md)).

If later product behavior needs messages or join-request handling, it can initially be another
adapter/worker in the Platform modular monolith. A new repository is justified only by a real
independent ownership, deployment or security boundary.

## Go/no-go gates

### Telegram linking is go only when

1. A BotFather-configured staging Authorization Code flow succeeds twice for the same user with
   strict issuer/audience/algorithm/expiry, state, PKCE S256 and nonce validation.
2. `sub` is stable across both logins; the observed `id` is stable and exactly equals the same
   account's Bot API user ID and Tribute `telegram_user_id`.
3. Duplicate identity, duplicate Telegram ID, same-account idempotency, attempted relink and
   expired/replayed transaction tests behave as specified.
4. The chosen OIDC library works without a UserInfo endpoint and does not treat Telegram access
   tokens as application sessions.
5. The owner approves bot identity/branding and the recent-auth/recovery UX.

### Tribute automatic access is go only when

1. A real delivery or Tribute test vector confirms the exact raw-body signature encoding,
   constant-time verification, retry-triggering responses and a workable key-rotation procedure.
2. Controlled fixtures capture new, renewal and cancellation plus duplicate and deliberately
   out-of-order delivery. Event field stability and idempotency behavior are recorded.
3. Tribute answers when cancellation, final failed payment, expiry, resume, gift redemption,
   refund and chargeback occur, whose Telegram ID is sent, and whether `expires_at` includes the
   seven-day failed-payment window.
4. Tribute supports a member snapshot/backfill contract with exact ID, expiry, statuses,
   pagination, consistency and rate limits. An internal undocumented route is insufficient.
5. Initial backfill, webhook outage beyond the retry horizon, full reconciliation, clock expiry,
   late renewal and replay from inbox all pass with no indefinite overgrant.
6. The exact Inside subscription/period/channel allowlist is captured and events for other
   products cannot grant access.

Any unresolved gate above is **no-go for unattended production entitlement**. It does not prevent
a small manual pilot with explicit owner-reviewed, expiring access adjustments.

## Bounded credentialed proof

This research performed no credentialed or paid external action. The remaining proof is bounded
to staging and needs owner-controlled BotFather/Tribute credentials plus approval for any test
payment.

| Timebox | Proof | Required evidence |
|---|---|---|
| 0.5 day | Telegram client | Staging bot/redirect, two code flows, validated token claim shapes, `sub`/`id` stability, nonce and no-UserInfo behavior. |
| 0.25 day | Identity correlation | Same user's OIDC `id`, Bot API user ID and Tribute ID captured/redacted and compared exactly. |
| 0.5 day | Tribute deliveries | Signature vector plus new/renew/cancel/gift or trial fixtures, retry/duplicate behavior and raw envelopes without secrets. |
| 0.5 day | Inbox/state replay | Duplicate/out-of-order/malformed/wrong-product cases, request-time expiry and late renewal. |
| 0.5 day | Backfill/reconcile | Supported member snapshot, pagination/rate/lag, initial import, partial-run safety and drift repair. |
| 0.25 day | Failure drill | Provider outage beyond retry window, key rotation, processor recovery and manual bounded fallback. |

Stop the spike after evidence and a go/no-go memo; do not stretch it into production integration.

## Questions for Telegram and Tribute

### Telegram/BotSupport

1. Is OIDC profile `id` guaranteed to be the same numeric Telegram user ID exposed by Bot API for
   that account, and is it stable for the lifetime of the account?
2. Is `sub` issuer-wide and stable across bot clients as the advertised `public` subject type
   implies? Is any relationship to profile `id` guaranteed?
3. Is `nonce` supported and returned in the standard authorization-code ID token even though it is
   absent from discovery `claims_supported` and the manual code example?
4. What is the supported RP behavior when a user resets Telegram web authorization, given the lack
   of a revocation/backchannel endpoint?

Telegram directs OIDC questions to `@BotSupport` with `#oidc` in the
[Login documentation](https://core.telegram.org/bots/telegram-login).

### Tribute Support

1. What is the exact `trbt-signature` representation and canonical test vector? Is there a
   version/prefix, replay age or dual-key rotation window?
2. Which HTTP statuses/timeouts trigger retry, what schedule is authoritative, is ordering
   guaranteed, and does `sent_at` change on retry?
3. Is there a stable delivery/event ID or official idempotency key?
4. When is `cancelled_subscription` sent, and does its `expires_at` always mean paid-through
   access rather than immediate revocation?
5. Does `expires_at` include the seven-day failed-payment grace? What events mark failed payment,
   final expiry, resume/reactivation, refund and chargeback?
6. For gifts, is the event sent at purchase or redemption and whose `telegram_user_id` is present?
7. Can subscription events contain a `W-...` Tribute identity without a Telegram ID despite the
   schema declaring it required?
8. Is `GET /subscribers` a supported third-party production API? What are its pagination,
   consistency, status meanings, retention and rate limits?
9. Is there a supported event-history, transaction, lookup or export endpoint for initial
   backfill and reconciliation?
10. What happens to the reported lifecycle when `@Tribute` loses admin rights, a member leaves or
    is manually banned, or a creator deletes a subscription?

## Open owner decisions

1. Approve one staging bot identity: reuse an existing Inside bot only if its brand/credentials
   fit, otherwise create a dedicated configuration-only Platform login bot.
2. Approve the sensitive-action UX: recent email re-auth for first link, stronger proof for
   replacement, and an audited owner recovery path.
3. Decide whether the launch can be a bounded manual pilot if Tribute does not supply supported
   reconciliation, or whether that is an immediate provider no-go.
4. Set the maximum manual adjustment duration and who may approve it; seven days is the proposed
   ceiling, not a confirmed product decision.
5. After Tribute answers, decide whether Platform access mirrors its failed-payment grace or ends
   exactly at the last proven `expires_at`.
6. Approve a small real subscription/trial/gift test cost and sanitized fixture capture. Payments
   and external support messages remain owner-gated actions.

Until these gates are closed, the reversible architecture is **Telegram OIDC linking ready for a
staging proof; Tribute webhook ingestion designed but automatic Membership access disabled;
manual expiring review or another provider as fallback**.
