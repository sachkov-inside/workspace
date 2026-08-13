---
title: "Tribute для Telegram-first подписки и access lifecycle"
status: research
decision_date: 2026-08-13
tracker: "GitHub #2"
---

# Tribute для Telegram-first подписки и access lifecycle

Все внешние факты проверены 2026-08-13. Это decision input, а не разрешение создавать аккаунт,
подключать Telegram, принимать оплату, приглашать людей или открывать продажи.

## Рекомендация

**Открытый запуск: no-go. Ограниченный pilot: conditional-go только после owner GO и письменного
закрытия блокеров ниже.**

Tribute документирует основной happy path: месячную подписку, автопродление привязанной карты,
доступ в приватный канал через join request, связанную discussion group, семидневный retry/grace
после failed renewal и автоматическое удаление после исчерпания grace. Но для открытого запуска
не хватает подтверждённого payment-compliance, полной экономики для покупателя, российской
fiscalization, refund/chargeback lifecycle и восстановимого member ledger.

Самый серьёзный конфликт источников: Tribute принимает card payments для subscriptions внутри
своего Telegram bot и [отдельно пишет](https://wiki.tribute.tg/for-content-creators/stars), что
Stars пока применяются только к digital products, тогда
как действующие [Telegram Bot Platform Terms](https://telegram.org/tos/bot-developers#6-2-digital-goods-and-services)
требуют Stars для всех digital goods/services внутри bots и Mini Apps. Из публичных источников
нельзя доказать, что у модели Tribute есть допустимое исключение. До письменного ответа Tribute
и проверки owner/legal этот риск нельзя принимать молча.

## Requirements matrix

| Требование | Статус на 2026-08-13 | Evidence / граница |
|---|---|---|
| Monthly recurring | Частично подтверждено | Можно создать monthly period; привязанная карта продлевается автоматически. Точный порядок всех retry, кроме семидневного окна, не опубликован. |
| Экономика | Не готово к launch | Creator fee — 10%; банк может брать дополнительную комиссию. Для покупателя появилась динамическая service fee без публичной формулы. |
| RUB payout | Частично подтверждено | Wiki указывает RUB payout и порог 3 000 ₽, но Creator Terms всё ещё говорят о пороге, эквивалентном 100 €. Фактическое условие нужно подтвердить для owner account. |
| Creator/account geography | Не подтверждено | Есть KYC и выбор country/payout method; публичного актуального списка допустимых creator countries и гарантии регистрации/выплаты для нужного owner status нет. |
| Private channel access | Подтверждено документами | После оплаты пользователь запрашивает доступ, Tribute approve-ит join request; прямой обычный invite не связывает доступ с подпиской. |
| Community chat | Условно подтверждено | Поддержан private **linked discussion/comment group** для канала. Отдельная несвязанная community group теми же docs не доказана. |
| Failed renewal / grace | Подтверждено документами | Tribute повторяет списание до 7 дней и удаляет участника после неуспешного окончания этого окна. Расписание attempts не опубликовано. |
| Cancel / resubscribe | Частично подтверждено | Subscriber может cancel/renew в профиле; API различает `active`, `pre_cancelled`, `cancelled` и `expireAt`. Сохранение доступа до paid-through и exact rejoin нужно доказать pilot-ом. |
| Refund / dispute | Не готово к launch | Subscription refund публично описан только для technical error через support. Нет документированного subscription-refund webhook и гарантии удаления из обеих Telegram surfaces. |
| Receipts / taxes / fiscalization | Не подтверждено | Tribute действует как agent, но сделка заключается между Creator и Follower; Creator отвечает за legality. Terms говорят, что Tribute обычно не рассчитывает и не удерживает налоги. Российский fiscal receipt flow публично не описан. |
| Member data / export | Не готово к launch | Dashboard показывает new/renewed/cancelled/active. OpenAPI содержит `/subscribers`, но помечает endpoint `x-internal: true`; документированного CSV export или гарантированного public member-list API нет. |
| Webhooks / audit | Частично подтверждено | Есть HMAC-SHA256 и retries примерно 24 часа для new/cancelled/renewed events. Не документированы event ID, replay/backfill, failed-renewal event и reconciliation contract. |
| Provider outage / operator recovery | Не готово к launch | Terms не гарантируют uninterrupted service. Есть individual free invite, но не описаны его expiry, audit, reconciliation и взаимодействие с автоматическим removal. |
| Data processing | Подтверждено, нужно принять | TRBT Limited — controller; собираются Telegram ID, KYC/ID/selfie, transaction и due-diligence data; возможна передача processors/financial institutions/regulators; retention — минимум 5 лет после отношений. |

## Что документировано

### Деньги и выплаты

- [Fees, limits, currencies](https://wiki.tribute.tg/for-content-creators/fees-limits-currencies):
  Tribute удерживает 10% каждой successful transaction; банковские и conversion fees могут быть
  сверху. На buyer payments действует дополнительная dynamic service fee, но процент публично не
  раскрыт и предлагается уточнять у support.
- [Payouts](https://wiki.tribute.tg/for-content-creators/payouts): RUB/EUR можно выводить на карту
  или в `@wallet`, crypto — в `@wallet`; текущий wiki threshold — 3 000 ₽ / 100 € / 100 USDT.
  Scheduled payout идёт 25-го за первую половину месяца и 10-го за вторую; on-demand request — не
  чаще двух раз в месяц, заявленный срок 2–5 business days. Общий срок зависит от страны и метода
  и может достигать месяца.
- [Creator Terms](https://tribute.tg/terms-creator.html), updated 2025-12-23: Tribute — commercial
  agent Creator, а не сторона creator/follower deal. Terms фиксируют 10%, €35 за обработку одного
  chargeback message, возможные costs при refund и право задержать disputed или все collected funds
  при dispute threshold. Terms могут расходиться с wiki по payout threshold, поэтому launch
  опирается только на условие, подтверждённое для реального owner account.

### Subscription и Telegram access

- [Creating a subscription](https://wiki.tribute.tg/for-content-creators/subscriptions/how-to-create-a-subscription)
  позволяет выбрать one-time, weekly, monthly, 3/6 months или annual period, сумму и валюту.
- [Subscription publishing](https://wiki.tribute.tg/for-content-creators/subscriptions/subscription-publishing)
  даёт Telegram link и web link. После оплаты пользователь делает join request, который bot
  автоматически approve-ит. Обычный private invite этот lifecycle обходит.
- [Subscriber management](https://wiki.tribute.tg/for-subscribers/subscription-management) даёт
  пользователю просмотр period/payment, cancel и переход в канал; FAQ также описывает renew.
- [Deferred removal](https://wiki.tribute.tg/for-content-creators/subscriptions/deferred-subscriber-removal-for-failed-payments)
  оставляет доступ на 7 дней после failed payment, продолжает charge attempts и только затем
  автоматически удаляет участника.
- [Comment access](https://wiki.tribute.tg/for-content-creators/how-to-set-up-access-to-comments)
  требует private linked discussion group, `Only members`, `Approve new members` и Tribute bot с
  правами add/block users. В subscription отдельно включается `Comment Access`.
- [FAQ](https://wiki.tribute.tg/faq) обещает automatic removal при non-renewal, free individual
  invite и support при failed access/payment. FAQ не определяет auditable manual override protocol.

### API, audit и data

- [API authorization](https://wiki.tribute.tg/for-content-creators/api-documentation) использует
  secret `Api-Key`; key создаётся в Creator Dashboard и не должен попадать в repository/Issue.
- [Webhooks](https://wiki.tribute.tg/for-content-creators/api-documentation/webhooks) подписываются
  `trbt-signature` (HMAC-SHA256) и retry-ятся с exponential backoff примерно 24 часа. Для subscription
  заявлены `new_subscription`, `renewed_subscription`, `cancelled_subscription`.
- [Official OpenAPI](https://tribute.tg/api/v1/openapi/en) включает Telegram user ID, subscription,
  channel, `expires_at` и type в events. Member-list endpoint `/subscribers` помечен `x-internal`,
  поэтому считать его поддерживаемым export/reconciliation API без письменного подтверждения нельзя.
- [Statistics](https://wiki.tribute.tg/for-content-creators/statistics/available-data) показывает
  earnings, new/renewed/cancelled subscriptions и active subscribers;
  [source filter](https://wiki.tribute.tg/for-content-creators/statistics/where-to-find-it) выбирает
  General или конкретный channel/group. Public docs не обещают raw export, retention, immutable
  audit log или webhook replay.
- [Privacy Policy](https://tribute.tg/privacy-policy.html), updated 2025-10-09, описывает controller,
  KYC/transaction data, categories of recipients, GDPR rights и retention минимум 5 лет.

### Tax и platform-policy boundary

- [Creator Terms](https://tribute.tg/terms-creator.html) возлагают законность creator/follower deal
  на стороны и говорят, что Tribute обычно не рассчитывает, не удерживает и не платит Creator taxes.
  Возможность удержания остаётся, если этого требует applicable law.
- Ни Terms, ни wiki не подтверждают, кто и как формирует российский фискальный чек именно для
  выбранного статуса Кирилла. Наличие generic receipt notification в Privacy Policy не является
  доказательством 54-ФЗ/НПД compliance.
- [Telegram Bot Platform Terms](https://telegram.org/tos/bot-developers#6-2-digital-goods-and-services)
  и [Telegram payments guide](https://core.telegram.org/bots/payments-stars) требуют Stars для
  digital goods/services внутри Telegram bots/Mini Apps. Публичные Tribute docs одновременно
  описывают card subscriptions и говорят, что Stars используются только для digital products.

## Блокеры, которые владелец закрывает до pilot

Нужны сохранённые письменные ответы Tribute и, где отмечено, owner accountant/legal:

1. Допустима ли monthly card subscription для этой digital Membership по текущим Telegram rules;
   какая сторона несёт риск блокировки bot/payment flow.
2. Может ли выбранный owner status пройти KYC и стабильно получать RUB payouts; каков реальный
   threshold, список payout methods, processing time и полный buyer fee при плановой цене.
3. Кто выдаёт покупателю юридически корректный receipt/check и кто отвечает за 54-ФЗ/НПД,
   refunds и корректировки дохода. Это подтверждает accountant/legal, не только provider support.
4. Что происходит в channel **и linked group** при cancel, exhausted 7-day grace, refund,
   chargeback, manual removal и resubscribe; когда именно access прекращается или возвращается.
5. Доступен ли production `/subscribers`, есть ли supported CSV/export, stable event ID,
   webhook replay/backfill и способ reconciliate состояние после outage дольше 24 часов.
6. Как отключить новые продажи, сохранить paid-through access и выгрузить evidence при outage,
   account suspension или уходе с Tribute.

## Safe pilot verification plan

Pilot начинается только после отдельных owner GO на account/KYC, Telegram connection и real
payment. До этого допустимы только чтение и подготовка.

### Setup владельца

1. Зафиксировать legal/tax status, offer/terms/refund wording и owner support contact.
2. Создать owner account через verified `@Tribute`, пройти KYC и указать payout details; credentials
   и документы не копировать в control plane.
3. Создать отдельные private pilot channel и linked discussion group без production-аудитории.
4. Добавить verified `@Tribute` минимально необходимым admin: channel — invite/add subscribers и
   требуемые docs message permissions; group — add/block users и требуемые comment permissions.
5. Включить `Only members`, `Approve new members`, `Comment Access`; создать одну monthly RUB
   subscription и не публиковать ссылку широкой аудитории.
6. Если API/webhook разрешены, хранить key только в encrypted secrets store; проверять HMAC,
   idempotency и сохранять минимальный журнал event timestamps/Telegram ID/access outcome.

### Canary matrix

| Path | Что наблюдать | Pass evidence |
|---|---|---|
| First payment | Invoice, charge, join requests, channel + group approval | Одна charge; один участник в обеих surfaces; amount/fee/expiry совпадают в dashboard |
| Cancel | Renewal выключен без раннего удаления | Paid-through timestamp и фактический доступ до него совпадают; затем удалены обе surfaces |
| Failed renewal | Retry/grace и отсутствие скрытого вечного доступа | Attempts/support evidence; доступ сохраняется не дольше 7-day grace; затем удалены обе surfaces |
| Resubscribe | Новый платёж после cancel/removal | Доступ возвращается в обе surfaces без duplicate charge и без stale ban/invite |
| Refund/chargeback | Финансы и access коррекция | Provider evidence, corrected balance/receipt и определённый removal outcome в обеих surfaces |
| Manual override | Free invite/removal не ломают automation | Причина, owner, expiry и последующая reconciliation наблюдаемы; Tribute не re-add/remove ошибочно |
| Webhook outage | Signature, duplicate, delay > retry window | Duplicate-safe processing; dashboard/export позволяет восстановить exact current state |
| Payout | Полная экономика | Gross, creator fee, buyer fee, refund reserve, bank fee и net payout сходятся |

До open launch нужен минимум один полный billing cycle плюс завершённый 7-day failed-renewal path.
Одного successful payment недостаточно.

## Минимальный fallback

Если Tribute не закрывает хотя бы один must-have, **не открывать paid sales**. Минимальный безопасный
fallback — продолжить invite-only бесплатный pilot channel + linked chat с ручным owner register,
пока отдельная задача выбирает payment/access provider. Native Telegram Star subscriptions могут
принимать monthly Stars за доступ к channel, но сами по себе не доказывают RUB offer, linked-chat
lifecycle, export/reconciliation и российскую fiscalization; это не drop-in замена без отдельной
проверки.

## Decision boundary

Исследование не выбирает Tribute как billing/access authority и не меняет продуктовые решения Map
#1. Следующее решение принадлежит владельцу после письменных provider/legal ответов и canary
evidence. До этого корректный статус — `conditional-go for bounded pilot`, `no-go for open launch`.
