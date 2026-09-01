# Recommendation and Automation Policy

Status: governance template requiring Sales, Salesforce, Security, Legal, and Compliance approval.

## Required recommendation structure

Every playbook should provide:

1. Assessment based only on supplied opportunity facts and permitted evidence.
2. Prioritized actions with human owner, recommended timing, and rationale.
3. Risks and the evidence supporting each risk.
4. Missing information that would materially change the recommendation.
5. Historical or approved playbook sources.
6. Confidence stated as high, medium, or low with a reason.

## Human control

The assistant may recommend or draft. Without explicit approved workflow and user confirmation, it must not:

- send customer communications;
- change opportunity stage, probability, forecast category, amount, or close date;
- create commitments, quotes, discounts, or contract terms;
- approve deals or legal terms;
- expose inaccessible opportunity or contact data.

## Feedback

Capture whether the seller accepted, modified, rejected, or deferred a recommendation, plus an optional reason.
Do not equate acceptance with effectiveness. Measure downstream outcomes separately and account for differences in
segment, territory, product, deal size, and market conditions.

## Safety and fairness

Do not recommend actions based on protected or sensitive personal characteristics. Do not use seller demographics
as predictors. Provide explanations and an escalation path when recommendations appear incorrect or inappropriate.
Retain prompts, evidence references, decisions, and feedback according to the approved audit and retention policy.
