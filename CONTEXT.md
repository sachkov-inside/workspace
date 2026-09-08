# Shared Inside product context

This glossary names shared Inside product concepts that cross application or repository boundaries.
Repository-specific glossaries refine local concepts without renaming these shared terms.

## Identity and Membership

**Inside Subscription**:
A recurring commercial arrangement for one Account's chosen Subscription Tier and Subscription
Option. It is distinct from a payment, an Access Grant and a Platform permission.
_Avoid_: MembershipEntitlement, WorkshopEntitlement, Lifetime Access Grant

**Subscription Tier**:
A named Inside offer with a defined set of benefits, such as materials or materials with community
participation. It is independent of the duration and price used to purchase it.
_Avoid_: Subscription Option, payment period, permission

**Subscription Option**:
A purchasable combination of a Subscription Tier, a duration in calendar months and a full price
for that duration.
_Avoid_: Subscription Tier, monthly instalment, payment attempt

**Access Grant**:
An Account's right to a defined set of Inside benefits for a stated interval or without an end date,
supported by an identifiable basis such as a payment or an owner's decision.
_Avoid_: Payment, Inside Subscription, Telegram chat presence

**Lifetime Access Grant**:
An Access Grant without a scheduled end date, for a defined set of Inside benefits. It does not
promise every future separate paid offer.
_Avoid_: Never-expiring subscription, future all-access purchase, permanent Telegram membership

**Account**:
Platform's stable private identity for one authenticated human. It owns Platform permissions and
is independent of profile presentation and Membership.
_Avoid_: Principal, Platform Account, user, Member Profile

**TelegramIdentity**:
The provider-verified Telegram identity linked to an Account through the Telegram application.
_Avoid_: Username, BotContact, Account

**Member Profile**:
A presentation of an Account visible only to active Inside members. It grants neither identity,
Membership, nor content access.
_Avoid_: Account, public profile, identity record

**Membership Signal**:
The current presence of a linked TelegramIdentity in the Canonical Membership Chat.
_Avoid_: Tribute subscription, payment status

**MembershipObservation**:
A Telegram-owned observation of a Membership Signal at a specific time.
_Avoid_: Permanent member flag, entitlement

**MembershipEvidence**:
A finite normalized statement derived from a MembershipObservation and associated with an Account
through an opaque cross-repository reference.
_Avoid_: Raw Telegram status, permanent member flag, MembershipEntitlement

**MembershipEntitlement**:
Platform's finite grant that an Account may access Membership-scoped Platform surfaces, including
protected Library content and Member Profiles. It does not authorize protected Workshop content.
_Avoid_: IdP role, Telegram role, subscription, WorkshopEntitlement

**Canonical Membership Chat**:
The single closed Telegram chat whose current roster is the Membership Signal for Inside.
_Avoid_: Community directory, Tribute roster, audience segment

## Materials and Series

**Material**:
A self-contained Inside content unit with its own identity, such as a video, guide or note.
It can be read independently and reused in Series without copying its content.
_Avoid_: Lesson, Series, Workshop Resource

**Series**:
An authored collection of Materials with a single explicit mixed reading order and a reader task.
A Material may belong to zero, one or several Series; the Russian product name is «Серия».
_Avoid_: Playlist, Course, Workshop Track, Topic

**Series Step Sequence**:
An explicitly named connection between some Materials within one Series, following that Series's
order. It is independent of Format and importance, and may differ for the same Material in another
Series; in Russian, «Последовательность шагов».
_Avoid_: Main path, optional role, Module, parallel Track

**Topic**:
The primary subject area used to classify a Material for discovery.
_Avoid_: Series, learning path, Tag

**Format**:
The primary way a Material is consumed, such as video, guide or note.
_Avoid_: File type, step membership, importance

**Tag**:
A managed label that connects and retrieves Materials across Topics and Formats.
_Avoid_: Topic, Series, required step

## Content access

**ContentAccess**:
Platform's authority for deciding a Subject's content Action on a Resource.
_Avoid_: Paywall check, route guard, Membership middleware

**Subject**:
The anonymous visitor or authenticated Account whose access is being decided.
_Avoid_: Telegram user, authentication context

**Resource**:
A Platform material body, asset, download, or video governed by publication state and access class.
_Avoid_: URL, provider object, storage key

**AccessDecision**:
The allow or deny outcome for one Subject, Action, and Resource, including its reason and validity.
_Avoid_: Boolean Membership check, provider response

## Production Workshop (deferred direction)

**Workshop**:
Inside's deferred practical learning area in which an Account follows Workshop Tracks, experiments
in Laboratories and solves Production Cases. Its historical offer links access to a distinct
Workshop Entitlement; it is not part of the current subscription launch promise.
_Avoid_: Course, Material Series, separate current subscription

**Workshop Track**:
An authored thematic path through ordered Track Items around a technology or transferable
engineering capability. Its order is a recommendation, not an implicit unlock rule, and it need
not map one-to-one to a content Topic.
_Avoid_: Learning Branch, Material Series, Topic, course

**Track Item**:
One ordered placement in a Workshop Track that references exactly one Material, Laboratory or
Production Case and presents that target's canonical availability. It neither owns content nor
changes its access policy.
_Avoid_: Lesson, copied Material, prerequisite gate

**Laboratory**:
A versioned guided local experiment in which a learner builds or changes an environment, predicts
behaviour, observes the real system and records an optional conclusion. Manual step progress is a
resume aid, not verified mastery.
_Avoid_: Material format, Production Case, hosted sandbox, quiz

**Production Case**:
A versioned business engineering problem in which a learner designs and implements a change under
explicit context and constraints. One Production Case may have several stack-specific Case
Variants; its submission and evaluation policy is defined separately.
_Avoid_: Coding exercise, homework, quiz

**Case Variant**:
A supported stack-specific working form of one Production Case that preserves its learning outcome
and observable contract. Availability is declared explicitly in the case-to-stack coverage matrix.
_Avoid_: Separate case, reference solution

**Workshop Entitlement**:
Platform's finite grant that an Account may access protected Workshop content. It remains a
separate authority from MembershipEntitlement even when one active Inside subscription grants and
renews both.
_Avoid_: MembershipEntitlement, purchase record, permanent member flag

**Workshop Resource**:
A published Workshop Track outline, Laboratory or Production Case body or artifact governed by
Workshop publication state and access mode. A referenced Material remains a ContentAccess Resource.
_Avoid_: Material Resource, URL, Track Item, Git source file

**WorkshopAccess**:
Platform's authority for deciding a Subject's Workshop Action on a Workshop Resource. It consumes
public access mode or Workshop Entitlement without weakening ContentAccess for referenced Materials.
_Avoid_: ContentAccess, UI lock state, route-local entitlement check

## Уведомления

**Notification**:
Сообщение для одного Account по определённому событию продукта. Оно имеет назначение и может
доставляться по нескольким каналам независимо.
_Avoid_: Событие продукта, рассылка, попытка отправки

**Notification Delivery**:
Доставка одного Notification по выбранному каналу подтверждённому получателю. Результат одного
канала не определяет результат другого и не означает прочтения.
_Avoid_: Notification, broker acknowledgement, прочтение
