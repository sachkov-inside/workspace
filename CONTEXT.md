# Shared Inside product context

This glossary names shared Inside product concepts that cross application or repository boundaries.
Repository-specific glossaries refine local concepts without renaming these shared terms.

## Products

**Product**:
A standalone Inside learning programme built from an authored set of Materials; in generic Russian
interfaces and descriptions: «Продукт». A particular Product may be named a course, practicum or
guide without becoming a different kind of programme or purchase.
_Avoid_: Руководство or практикум as the universal category name, Material, Subscription

**Product Purchase**:
A one-time purchase of a specified Product under the accepted offer, distinct from the payment and
the resulting access rights; it does not create recurring charges.
_Avoid_: Subscription, payment, Access Grant

## Identity and Membership

**Inside Subscription**:
A recurring commercial arrangement for one Account's chosen Subscription Tier and Subscription
Option, covering Support and the Materials of every Product rather than naming a learning programme.
It is distinct from a payment, an Access Grant and a Platform permission; a no-charge assignment of
a tier does not itself create this billing arrangement.
_Avoid_: MembershipEntitlement, WorkshopEntitlement, Lifetime Access Grant

**Offer**:
A versioned commercial description of a set of benefits with independent for-sale, assignable and
archived states, separate from a Guide, payment and Access Grant. Its payment option states the
price, period and sale mode.
_Avoid_: Guide, Order, Payment, Access Grant

**Access Scope**:
The benefit or resource an Access Grant covers: Materials within a Content Scope, a particular
Product, Support or the single shared community chat.
_Avoid_: Price, tier name, Telegram presence, whole library

**Subscription Tier**:
An Offer with a Content Scope and benefits, such as Materials, Support and community
participation, assigned or sold independently of the duration and price used to obtain it.
_Avoid_: Subscription Option, payment period, permission

**Content Scope**:
The set of Products promised by a Subscription Tier or recorded in an Access Grant: every Product
for an Inside Subscription and the starter Subscription Tier, otherwise an explicit set. A Material
is covered only through a Product that contains it; no right opens an individual Material.
_Avoid_: Individual Material access, published library, catalogue, global Materials access

**Subscription Enrollment**:
An Account's assignment to a fixed version of a Subscription Tier, with its own origin and term.
It is neither a payment nor renewal consent.
_Avoid_: Inside Subscription, payment, Telegram membership

**Support**:
The right to ask the author for help within a stated term; in Russian, «Сопровождение».
_Avoid_: Personal mentoring, guaranteed answer, community participation

**Community Entitlement**:
An Account's effective right to participate in the single shared community chat, derived from its
live rights that cover Support, the chat or any Product. It is distinct from actual presence in the
chat.
_Avoid_: Chat membership, Membership Signal, tier name

**Admission Restriction**:
A moderator's or unexplained external restriction on joining the shared community chat,
independent of content rights.
_Avoid_: Expired right, revoked access, failed payment

**Subscription Option**:
A purchasable combination of a Subscription Tier, a duration in calendar months and a full price
for that duration.
_Avoid_: Subscription Tier, monthly instalment, payment attempt

**Access Grant**:
An Account's right to a defined set of Inside benefits for a stated interval or without an end date,
supported by an identifiable basis such as a payment or an owner's decision. Its scope, source,
state and history are independent of other grants and of the billing period.
_Avoid_: Payment, Inside Subscription, Telegram chat presence

**Lifetime Access Grant**:
An Access Grant without a scheduled end date, for a defined set of Inside benefits. It does not
promise every future separate paid offer.
_Avoid_: Never-expiring subscription, future all-access purchase, permanent Telegram membership

**Direct Right**:
A right an Account holds without a Subscription Enrollment or Product Purchase: an owner's or
carried-over Access Grant, or the legacy member bridge; in Russian, «Прямое право».
_Avoid_: Manual tier assignment, gift subscription, purchase

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
protected Materials allowed by its live rights and Member Profiles. It does not authorize
protected Workshop content.
_Avoid_: IdP role, Telegram role, subscription, WorkshopEntitlement

**Canonical Membership Chat**:
The single closed Telegram chat whose current roster is the Membership Signal for Inside.
_Avoid_: Community directory, Tribute roster, audience segment

## Materials and Guides

**Material**:
A self-contained Inside content unit with its own identity, such as a video, how-to guide or note.
It can be read independently and reused in Guides without copying its content.
_Avoid_: Lesson, Guide product, Workshop Resource

**Guide**:
The existing content model for a Product, with an authored learning path, optional Chapters,
supplementary Materials and Artifacts; its generic Russian name is «Продукт», while technical
Guide/Series identities and compatibility names remain stable.
_Avoid_: Series, Material Format guide, Workshop Track, Topic

**Guide Chapter**:
An optional named group within a Guide's main reading path. It organizes Materials without owning
copies of them or implying an access gate.
_Avoid_: Video chapter, Material, separately purchased Guide

**Supplementary Material**:
A Material associated with a Guide outside its main reading path, for reference or additional study.
Its role is specific to that Guide and does not change the Material's Format.
_Avoid_: Guide Chapter, copied Material, automatically free content

**Guide Artifact**:
A reusable resource included in a Guide, such as a prompt, template, file, example or external link,
with its own identity and purpose, discoverable separately from the reading path.
_Avoid_: Material, video chapter, ungoverned public download

**Guide Step Sequence**:
An explicitly named connection between some Materials within one Guide, following that Guide's
order, independent of Format; in Russian, «Последовательность шагов».
_Avoid_: Guide Chapter, main or supplementary role, video chapter

**Guide Purchase**:
The compatibility name for a Product Purchase represented by the existing Guide model.
_Avoid_: Inside Subscription, perpetual subscription period, Access Grant

**Topic**:
The primary subject area used to classify a Material for discovery.
_Avoid_: Guide, learning path, Tag

**Format**:
The primary way a Material is consumed, such as video, guide or note. The Material format «Гайд»
is distinct from a standalone Product represented by Guide.
_Avoid_: File type, Guide product, step membership, importance

**Tag**:
A managed label that connects and retrieves Materials across Topics and Formats.
_Avoid_: Topic, Guide, required step

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
