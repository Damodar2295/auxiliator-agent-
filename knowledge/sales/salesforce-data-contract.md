# Salesforce Data Contract for Playbook Recommendations

Status: proposed integration contract; API names and access rules require Salesforce SME approval.

## Minimum opportunity inputs

- Opportunity ID and name
- Stage and stage-entry date
- Amount, currency, type, lead source, expected close date, and probability
- Account industry, region, size or approved segment
- Products and opportunity line items
- Next step and recent completed activities
- Opportunity owner and team roles
- Contact roles and buying-group coverage
- Competitor and approved loss-risk fields
- Qualification, security, legal, procurement, and implementation fields when available

## Historical outcome inputs

Use closed-won and closed-lost opportunities with reliable stage history, activity history, products, amount,
segment, outcome, loss reason, competitor, cycle time, and stakeholder coverage. Exclude duplicates, test data,
cancelled records, and records without a trustworthy outcome according to SME-approved rules.

## Permissions

Recommendations must respect Salesforce object, field, sharing, and record-level permissions. Evidence from a
historical opportunity must not be exposed to a user who lacks access. Prefer aggregated or redacted pattern
evidence when individual opportunity details are sensitive.

## Data quality

Track completeness and freshness for every recommendation. Do not treat blank values as negative evidence.
Stage names, product taxonomy, segments, loss reasons, activity types, currencies, and regions require normalized
definitions. Surface low confidence when required fields or sufficient comparable history are unavailable.

## Adapter boundary

The application should read Salesforce through an approved integration user and Connected App or enterprise
integration layer. Credentials belong in the secrets manager. Retrieval results should contain stable record IDs,
permitted display labels, timestamps, source type, and access metadata. No production Salesforce credentials or
customer records belong in the repository knowledge folder.
