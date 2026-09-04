# Shared Inside product context

This glossary names shared Inside product concepts that cross application or repository boundaries.
Repository-specific glossaries refine local concepts without renaming these shared terms.

## Identity and Membership

**Inside Subscription**:
The current commercial bundle that, while active, grants both Membership-scoped access and
Workshop access through two separate finite entitlements. It is not itself a Platform permission.
_Avoid_: MembershipEntitlement, WorkshopEntitlement, permanent purchase

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

## Production Workshop

**Workshop**:
Inside's practical learning area in which an Account follows Workshop Tracks, experiments in
Laboratories and solves Production Cases. An active Inside subscription currently grants access
to it through a distinct Workshop Entitlement.
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

**Assignment**:
An Account's private working instance of one Case Variant. It owns the starter baseline and the
submitted Attempts without becoming the Production Case itself.
_Avoid_: Production Case, repository template, course enrollment

**Attempt**:
An immutable declaration that one Assignment state is ready for evaluation, bound to an exact
source revision and the versions of the case and evaluator that interpret it.
_Avoid_: Commit, push, local test run

**Attempt Evidence**:
The versioned facts collected for one Attempt, including its source revision and accepted local
evaluation report. Evidence records how a result was reached without becoming a certificate.
_Avoid_: Local report, certificate, log bundle

**Attempt Result**:
Workshop's outcome for one Attempt derived from its required executable checks and source binding.
`Passed` means the Workshop checks passed; it is not an external professional certification.
_Avoid_: Mastery Result, Verified, certificate, grade, XP

**Solution Reveal**:
The recorded unlocking of an exact author solution for an Account and Production Case version,
either after an Attempt or through the Account's explicit choice to study the solution earlier.
_Avoid_: Material publication, case completion, pass

**Workshop Entitlement**:
Platform's finite grant that an Account may access protected Workshop content. It remains a
separate authority from MembershipEntitlement even when one active Inside subscription grants and
renews both.
_Avoid_: MembershipEntitlement, purchase record, permanent member flag

`Assignment`, `Attempt`, `Attempt Evidence`, `Attempt Result` and `Solution Reveal` below describe
the implemented case-first foundation. They are deferred vocabulary, not the current Kafka
evaluation contract, until the post-CaseSpec decision explicitly accepts their reuse.
