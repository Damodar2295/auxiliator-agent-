# Phase 1 — Foundation Report

## Status

Phase 1 implementation and gates passed on 2026-09-04. Phase 2 has not started.

## Delivered

- Repository assessment and Reuse/Extend/New architecture mapping.
- Strong Pydantic contracts for the governed intelligence domain.
- Four validated YAML-backed published POC Skills.
- Read-only synthetic entities, signals, facts, evidence, relationships, and metrics.
- Deterministic intent routing with explicit ambiguity/clarification behavior.
- Thin Phase 1 Intelligence Agent skeleton.
- PBKDF2/HMAC mock authentication with Viewer, Author, Reviewer, and Admin roles.
- Authenticated APIs for entities, Signals, Skills, Capabilities, Policies, and routing.
- React/TypeScript Intelligence Hub shell with login, Playground, Skills, and Signals.
- Existing Salesforce, chat, retrieval, indexing, and health APIs preserved.

## Automated gates

```text
Backend Ruff: passed
Backend mypy: passed (32 source files)
Backend pytest: 22 passed, 1 intentionally skipped integration test
Frontend ESLint: passed
Frontend Vitest: 1 passed
Frontend TypeScript/Vite production build: passed
```

## Smoke tests

```text
GET  /api/v1/health/ready       200, document store healthy
GET  /app/                      200
POST /api/v1/auth/login         200, viewer role and synthetic notice returned
GET  /api/v1/skills             200, four Skills returned
POST /api/v1/intelligence/execute 200, opportunity-risk selected deterministically
```

## Manual test

Open `http://127.0.0.1:8080/app/` and sign in with any of:

- `viewer`
- `author`
- `reviewer`
- `admin`

The shared synthetic POC password is `Demo123!`. This authentication is demonstrative only and
must not be treated as production IAM.

In Playground, retain the Northstar opportunity and ask:

```text
What is preventing this opportunity from progressing?
```

Expected Phase 1 behavior: the deterministic router selects `opportunity-risk` and reports that
governed execution begins in Phase 2. The current response is intentionally a routing plan, not a
fabricated business decision.

## Known Phase 1 boundaries

- Context assembly, evidence sufficiency, Skill execution, confidence, policy, and durable traces
  are Phase 2 work.
- MCP, Skill Studio, and draft lifecycle workflows are Phase 3 work.
- Reviews, evaluations, publishing gates, and decision replay are Phase 4 work.
- The login and all enterprise/customer records are synthetic POC data.
