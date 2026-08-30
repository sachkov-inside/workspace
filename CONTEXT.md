# Shared Inside product context

This glossary names the cross-repository concepts shared by Platform and the separate
`inside-telegram` application. Repository-specific models may refine them without changing their
ownership.

## Identity and Membership

**Principal**:
A person or machine identity recognized by an Inside application.
_Avoid_: User when the distinction from a person matters, account role

**External identity**:
A provider-verified identity bound to one Principal independently of changeable profile data.
_Avoid_: Email address, login, Member Profile

**Platform session**:
A finite authentication context through which Platform recognizes a Principal for subsequent
authorization.
_Avoid_: Membership, entitlement, permission

**Platform account**:
The private Platform state through which a human Principal manages identity, security, linking and
recovery.
_Avoid_: Member Profile, Principal, Membership

**Member Profile**:
A presentation of a human Principal that is visible only to active Inside members and never grants
identity, Membership or content access.
_Avoid_: Platform account, public internet profile, identity record

**Membership signal**:
The current presence of a linked Telegram identity in the canonical closed Inside chat.
_Avoid_: Tribute subscription, payment status

**Membership evidence**:
A finite-lifetime normalized observation of a Membership signal associated with a Principal.
_Avoid_: Telegram status, permanent member flag

**Membership entitlement**:
A finite-lifetime Platform grant for access to closed content.
_Avoid_: IdP role, Telegram role, subscription

## Content access

**ContentAccess**:
The Platform capability that decides a Subject's content Action on a Resource.
_Avoid_: paywall check, route guard, Membership middleware

**Subject**:
The anonymous visitor or authenticated Principal whose access is being decided.
_Avoid_: Telegram user, session

**Resource**:
A Platform material body, asset or video governed by a publication state and access class.
_Avoid_: URL, Kinescope object, S3 key

**Access decision**:
The allow or deny outcome for one Subject, Action and Resource, including its reason and validity.
_Avoid_: boolean Membership check, provider response
