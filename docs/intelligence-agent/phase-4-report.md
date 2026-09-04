# Phase 4 — Governance Report

Date: 2026-09-04

## Outcome

Phase 4 adds deterministic evaluation gates, auditable human review, immutable Skill snapshots, rollback-as-a-new-version, and replayable audit records. These controls remain outside the Skill and model execution boundary, so neither can approve, publish, override policy, or rewrite history.

Phase 5 enterprise-polish work has not started.

## Delivered

- Synthetic golden evaluation service with routing, decision-contract, evidence correctness/coverage, abstention, policy compliance, latency, token, and mock-cost metrics.
- Mandatory publish thresholds: 100% policy compliance, evidence-reference validity, deterministic-case accuracy, and required-case completion; at least 90% routing accuracy.
- Version-specific publish gate; missing or failed evaluation blocks publishing with a controlled conflict.
- Review Queue sourced from decisions with `review_required=true`.
- Reviewer approve, reject, modify, and comment actions.
- Original decisions remain intact; reviewed decisions, reviewer, comments, and timestamps are recorded separately.
- Completed review outcomes are immutable.
- Immutable snapshots for initially published and newly published Skills.
- Rollback restores a prior definition as a new patch version and records the source snapshot.
- Decision-to-Skill-version linkage through audit replay.
- REST APIs for evaluations, gates, reviews, versions, rollback, and audit replay.
- React Reviews, Evaluations, and Audit workspaces with role-aware controls and safe stage replay.
- No chain-of-thought is stored or displayed.

## API additions

```text
POST /api/v1/evaluations/run
GET  /api/v1/evaluations/results
GET  /api/v1/evaluations/publish-gate/{skill_id}
GET  /api/v1/reviews
GET  /api/v1/reviews/{review_id}
POST /api/v1/reviews/{review_id}/{approve|reject|modify|comment}
GET  /api/v1/skills/{skill_id}/versions
POST /api/v1/skills/{skill_id}/rollback
GET  /api/v1/audit/replay/{decision_id}
```

## Verification results

- Ruff: passed.
- mypy across `agent`, `config`, and `tests`: passed.
- pytest: 43 passed and 2 explicitly marked integration tests skipped by default.
- ESLint: passed.
- Vitest: 7 passed.
- TypeScript/Vite production build: passed.
- FastAPI, PostgreSQL/pgvector, and MCP Streamable HTTP startup: passed.
- Live Opportunity Risk evaluation: passed with routing `1.0`, policy compliance `1.0`, and evidence-reference validity `1.0`.
- Live publish gate: passed.
- Live immutable version lookup: returned published snapshot `1.0.0`.
- Visual evaluation screen: passed, displaying a passed gate and metrics.
- Visual audit replay: passed with all 14 stages and the no-chain-of-thought disclosure.
- Author review access denial: passed.

## Key tests

- Threshold reproducibility and gate enforcement.
- Missing-evaluation publish blocking.
- Review approval/rejection/modification/comment audit behavior.
- Preservation of original and reviewed decisions.
- Immutable completed reviews.
- Snapshot immutability and rollback to a new version.
- Decision/trace/version replay linkage.
- Human override policy result.
- Viewer, Author, Reviewer, and Admin authorization boundaries.
- Phase 1–3 compatibility and MCP execution regression.

## Known limitations

- Evaluation data and expected outcomes are synthetic POC fixtures; production calibration requires governed historical outcomes.
- Review, evaluation, and version ledgers are in-process control stores in this phase. Decision and trace persistence still supports memory or PostgreSQL; durable enterprise control-ledger storage is a Phase 5 extension.
- Review Queue receives only decisions whose deterministic policy outcome requires review; ordinary high-confidence demonstrations will not create queue entries.
- Rollback publishes a prior snapshot as a new patch version. It never rewrites or deletes historical snapshots.
- Production IAM, OAuth for MCP, enterprise audit sinks, notification workflows, and real approval attestations remain Phase 5 extension points.

## Phase boundary

Phase 4 is complete. Do not begin enterprise connectors, resilience/circuit-breaker work, event/batch polish, deployment updates, or Phase 5 documentation until Phase 5 is explicitly approved.
