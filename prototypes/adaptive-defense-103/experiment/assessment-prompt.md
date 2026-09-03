The participant has now answered the initial questions generated in a separate call. The Platform
retains those questions as an immutable artifact; do not reproduce or rewrite them. Assess all four
rubric dimensions and add at most two grounded follow-ups only when an answer is vague, wrong or
contradicted by evidence.

Return an advisory defense signal and learner feedback using the strict result schema. Cite exact
input fact or exchange IDs. A follow-up indicates what a live session would ask next; the current
signal describes only the evidence already present and never assigns `Verified`.

Use `mastery_supported` when the participant correctly answers every core risk actually asked and
shows no material contradiction, even if the three-question budget did not directly sample every
rubric dimension. Use `mastery_not_yet_shown` for a wrong, missing or contradicted answer on a core
risk. Do not fail an attempt merely because the question generator did not select a dimension.
