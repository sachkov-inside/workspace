The participant has answered the bounded follow-up questions. Produce the final assessment from all
initial and follow-up exchanges. Do not ask any more questions: `followUps` must be an empty array.

Use `mastery_supported` when every core risk actually asked is now answered correctly without a
material contradiction. Use `mastery_not_yet_shown` when a core answer remains wrong, missing or
contradicted. Use `inconclusive` when the evidence itself cannot resolve the question. Return only
the strict assessment schema; this remains advisory and never assigns `Verified`.
