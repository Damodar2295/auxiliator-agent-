# Phase 3 — MCP and Self-Service Report

Date: 2026-09-04

## Outcome

Phase 3 adds one official MCP v2 Skill Gateway and a self-service Skill Studio without weakening the Phase 2 control plane. Published Skills now execute through the same in-memory MCP protocol used by tests; external clients can inspect the same server through authenticated Streamable HTTP at `/mcp/`.

Phase 4 governance workflows have not started.

## Delivered

- Official `mcp[cli]` v2 dependency and one Auxiliator Skill Gateway server.
- Typed `list_skills`, `get_skill`, `get_skill_schema`, and `execute_skill` tools.
- One registry and executor implementation shared by MCP, HTTP discovery, and runtime execution.
- Real in-memory MCP client invocation from the Phase 2 runtime.
- Authenticated Streamable HTTP transport whose lifespan is owned by FastAPI.
- MCP execution limited to Approved or Published Skills.
- Draft create, update, constrained generation, listing, and lifecycle APIs.
- Strict Draft → Validated → Evaluated → Review → Approved → Published → Deprecated transitions.
- Server-side role separation: Author drafts/validates/evaluates/submits; Reviewer approves; Admin publishes/deprecates.
- Registry-constrained fallback generation visibly labelled as an AI-assisted Draft.
- React Skill Studio with generation, form editing, YAML-style inspection, validation feedback, and role-aware actions.
- Unified Catalog tabs for Skills, Signals, Capabilities, and Policies.

## API additions

```text
GET  /api/v1/skills/drafts
POST /api/v1/skills/drafts
POST /api/v1/skills/drafts/generate
PUT  /api/v1/skills/drafts/{skill_id}
POST /api/v1/skills/{skill_id}/lifecycle/{action}
POST /mcp/
```

Lifecycle actions are `validate`, `evaluate`, `submit-review`, `approve`, `publish`, and `deprecate`.

## Verification

```text
.venv/bin/ruff check .
.venv/bin/mypy agent config tests
.venv/bin/pytest -q
npm run lint
npm run test
npm run build
.venv/bin/uvicorn agent.main:app --host 127.0.0.1 --port 8080
```

Phase 3 tests cover MCP discovery/schema/execution parity, generation constraints, invalid lifecycle transitions, role authorization, prevention of AI self-publishing, external MCP authentication, and previous-phase regressions.

- Ruff: passed.
- mypy: passed across `agent`, `config`, and `tests`.
- pytest: 37 passed and 2 explicitly marked integration tests skipped by default.
- ESLint: passed with no warnings.
- Vitest: 4 passed.
- TypeScript and Vite production build: passed.

Live verification passed:

- Official Streamable HTTP client discovered all four expected tools.
- Rewards Orientation executed through MCP with `ALLOW`, confidence `0.9552`, and four evidence records.
- Skill Studio generated a Draft using only registered complaint signals.
- Author UI exposed `validate` and hid publish/deprecate.
- Catalog displayed all three registered capabilities.

## Known limitations

- Drafts and lifecycle state are in-process in Phase 3; durable version snapshots arrive in Phase 4.
- Evaluation actions advance the lifecycle contract only. Golden datasets, metrics, and publish gates arrive in Phase 4.
- Generation currently uses the deterministic registry-constrained fallback and is intentionally labelled Draft.
- YAML is an inspection view; import/export and source-control workflows remain extension points.
- MCP HTTP authentication uses synthetic POC bearer tokens, not production OAuth or enterprise IAM.
- Review Queue, comments, modifications, rollback, and immutable published versions remain Phase 4 work.
- The configured external Gemini model is unavailable and safely falls back locally.

## Phase boundary

Do not begin evaluation gates, Review Queue work, or version rollback until Phase 4 is explicitly approved.
