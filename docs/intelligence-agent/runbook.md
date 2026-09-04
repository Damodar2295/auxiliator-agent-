# Runbook

1. Copy `.env.example` to `.env` and supply local-only values.
2. Run `make install`, `make frontend-install`, and `make verify`.
3. Start with `make run`; use `/app/` with a synthetic persona.
4. Check `/api/v1/health/live` and `/api/v1/health/ready`.
5. Inspect `/mcp/` with a bearer token.
6. Set `GOVERNANCE_STORE_BACKEND=postgres` and `GOVERNANCE_STORE_DB_URI` for durable mode.

On failure, inspect structured logs, breaker state and safe traces. Never paste credentials into requests or logs.
