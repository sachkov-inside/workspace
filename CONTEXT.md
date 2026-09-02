# Shared Inside product context

This glossary names concepts that cross the Platform and Telegram application boundary.
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
