# Phase 2 — Governed Runtime Report

Date: 2026-09-04

## Outcome

Phase 2 replaces the Phase 1 routing placeholder with a bounded 14-stage LangGraph runtime. It assembles scoped synthetic context, performs one allowed recovery, evaluates sufficiency, executes exactly one registered Skill, validates evidence, computes confidence outside the model, applies deterministic policy, persists the decision and trace, and performs no external customer or Salesforce mutation.

Phase 3 MCP and self-service work has not started.

## Delivered

- Context Engine with relationship expansion, requested-window filtering, Skill input filtering, evidence deduplication, provenance, metrics, facts, and missing-requirement reporting.
- `SUFFICIENT`, one-attempt `RECOVERABLE`, and `INSUFFICIENT` behavior. Insufficient requests abstain before any model call.
- Four bounded executors: Complaint Root Cause, Opportunity Risk, Rewards Orientation, and Engagement Decline Escalation.
- Three-second model-call cutoff and deterministic grounded-explanation fallback. Analytics and rule Skills make zero model calls.
- Evidence-reference validation; unsupported references are removed and required unsupported conclusions abstain.
- Independent confidence formula with the approved 35/25/20/10/10 weights and missing-context/contradiction penalties.
- Deterministic `ALLOW`, `REVIEW`, `REJECT`, and `ABSTAIN` policy handling.
- Memory governance repository by default and optional idempotent PostgreSQL JSONB decision/trace persistence.
- Per-user decision/trace isolation, with Admin-wide retrieval.
- Synchronous and SSE execution, decisions, traces, and evidence-detail APIs.
- Governed `/playbook/recommend` adapter when `opportunity_id` is supplied; legacy behavior remains when omitted.
- Playground time-window selection, live 14-stage progress, result/policy/confidence displays, evidence drawer, warnings, and a Decisions/trace screen.

## Verification

Commands:

```text
.venv/bin/ruff check .
.venv/bin/mypy agent config tests
.venv/bin/pytest -q
npm run lint
npm run test
npm run build
GOVERNANCE_TEST_DB_URI=<local project PostgreSQL URI> .venv/bin/pytest tests/test_intelligence_phase2.py::test_postgres_repository_initializes_idempotently -q
.venv/bin/uvicorn agent.main:app --host 127.0.0.1 --port 8080
```

Results:

- Ruff: passed.
- mypy: passed for `agent`, `config`, and `tests`.
- pytest: 33 passed, 2 skipped in the default run. Skips are explicitly marked integration tests.
- PostgreSQL governance integration: 1 passed, covering idempotent initialization, decision/trace write and read, listing, and user isolation.
- ESLint: passed.
- Vitest: 2 passed.
- TypeScript/Vite production build: passed.
- Liveness and application startup: passed on `127.0.0.1:8080` with local PostgreSQL/pgvector.
- Visual browser test: login, 90-day selector, all 14 streamed stages, confidence, policy, four evidence links, evidence detail, Decisions list, and trace access passed.

Representative live smoke outcomes:

| Scenario | Skill | Outcome | Confidence | Evidence |
|---|---|---:|---:|---:|
| Customer complaint | Complaint Root Cause | ALLOW | 0.9657 | 2 |
| Stalled opportunity | Opportunity Risk | ALLOW | 0.9499 | 4 |
| Rewards preference | Rewards Orientation | ALLOW | 0.9552 | 4 |
| Engagement decline | Engagement Decline Escalation | ALLOW | 0.9624 | 1 |
| Unknown opportunity | Opportunity Risk | ABSTAIN | 0.0000 | 0 |

The provider-failure test confirms fallback output does not expose the provider error payload. Stored traces contain stage summaries and metrics only, never chain-of-thought.

## Manual test cases

1. Open `http://127.0.0.1:8080/app/` and use `viewer` / `Demo123!` (synthetic POC credentials).
2. Run Opportunity Risk for `OPP-3001`; inspect confidence, policy, evidence, and all 14 stages.
3. Open an evidence record and verify source interaction, provenance, timestamp, excerpt, and synthetic label.
4. Open Decisions, select the trace, and verify stage summaries and call/recovery counts.
5. Send a request scoped to `OPP-UNKNOWN`; verify `ABSTAIN`, confidence 0, no evidence, and model call count 0.
6. Call `/api/v1/playbook/recommend` with `opportunity_id: "OPP-3001"`; omit it to verify legacy compatibility.

## Known limitations

- Data, identities, evidence, outcomes, confidence values, and credentials are synthetic POC fixtures.
- Confidence weights are implemented exactly but are not empirically calibrated against production outcomes.
- PostgreSQL governance tables use JSONB and direct psycopg intentionally; migration/version management remains an enterprise extension.
- The POC auth token is not production IAM and logout is client-side only.
- External model explanations may degrade to deterministic text on provider failure or timeout; the governed result remains usable and visibly warned.
- Phase 4 owns review actions, immutable version publishing/rollback, and evaluation gates. The Phase 2 Decisions screen is read-only.
- MCP, Skill Studio, and external Skill invocation remain deferred to Phase 3.
