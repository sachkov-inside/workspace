# Shared Inside product context

This glossary names shared Inside product concepts that cross application or repository boundaries.
Repository-specific glossaries refine local concepts without renaming these shared terms.

## Identity and Membership

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
Platform's finite grant that an Account currently has Inside Membership access.
_Avoid_: IdP role, Telegram role, subscription

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
An Inside learning product in which an Account works through Production Cases and receives
structured practice feedback. It is commercially and operationally distinct from Membership even
when Membership temporarily grants beta access.
_Avoid_: Course, Material Series, Membership feature

**Learning Branch**:
A curated path through Production Cases and related Materials around a technology or transferable
engineering capability. It is not a Git branch and need not map one-to-one to a content Topic.
_Avoid_: Git branch, Topic, grade track

**Production Case**:
A versioned, multi-stage engineering situation with existing context, constraints, evidence and a
mastery rubric. One Production Case may have several stack-specific Case Variants.
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
The versioned facts collected for one Attempt, including its source revision, evaluation report,
decision explanation and defense. Evidence records how a result was reached without becoming a
certificate.
_Avoid_: Local report, certificate, log bundle

**Mastery Result**:
Workshop's assessment of one Attempt across the case rubric, including whether the case is complete.
It is not a grade, leaderboard score or external professional certification.
_Avoid_: Certificate, grade, XP

**Workshop Entitlement**:
Platform's grant that an Account may access a Workshop scope and the Materials explicitly included
with it. It is independent of MembershipEntitlement.
_Avoid_: MembershipEntitlement, purchase record, permanent member flag
