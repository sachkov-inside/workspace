# Review profile

Review asks whether the control plane remains truthful, bounded and operable. Pure content changes
do not require an independent code-review ritual; automation or future product code uses the
normal engineering review workflow.

## Required review evidence

- Facts, hypotheses and owner decisions are visibly distinct.
- Product promises do not invent response times, personal mentoring, content volume or outcomes.
- The Telegram-first launch does not silently depend on the future application.
- The future application is not specified outside the build-series owner decisions.
- Content production artifacts are linked to `sachkov-content`, not duplicated here.
- External provider claims are source-backed and dated.
- No secret, payment credential, participant PII, private invite or access token is present.
- Publication, payment activation, invitations, removals and repository merge have explicit owner
  authority appropriate to that action.

## Security boundary

Research and planning are read-only by default. Provider credentials belong in the encrypted
shared secrets store when they become necessary; never commit them or paste them into Issues.
Access operations require auditable provider or manual records without exposing participant data.
