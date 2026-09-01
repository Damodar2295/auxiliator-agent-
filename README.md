# Salesforce Playbook Agent

An AIX/LangGraph assistant that recommends seller-reviewed next-best-action playbooks for
Salesforce opportunities using approved playbooks and historical win/loss patterns.

The repository ships with synthetic SME-review templates only. Replace or validate these
templates with governed Salesforce history before production use.

## Local start

```bash
cp .env.example .env
./scripts/install.sh
./scripts/start_local.sh
```

Open `http://localhost:8080/docs`.

Start the native PostgreSQL 16 installation, then start the application:

```bash
make db-up
./scripts/start_local.sh
```

At startup, every Markdown file under `knowledge/sales/` is chunked, embedded, and idempotently
upserted into PostgreSQL. PostgreSQL with pgvector is the system of record for content, metadata,
and embeddings. The internal SafeChain embedding provider is selected when installed, with a
deterministic local embedding adapter for development.

## Recommend a playbook

```bash
curl -X POST http://127.0.0.1:8080/api/v1/playbook/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "opportunity_name": "Acme Expansion",
    "stage": "Solution Validation",
    "industry": "Financial Services",
    "customer_segment": "Enterprise",
    "deal_value": 250000,
    "days_in_stage": 35,
    "recent_activity": "Only one contact attended the last meeting",
    "pain_points": ["manual onboarding"],
    "competitors": ["Competitor A"]
  }'
```

Recommendations are advisory. Customer messages, pricing, forecasts, contracts, and Salesforce
record changes require human approval.

Database commands are also available through Make:

```bash
make db-up       # start native PostgreSQL/pgvector
make db-status   # check native server readiness
make db-shell    # open psql
make db-down     # stop the database
```

Postgres.app is installed at `~/Applications/Postgres.app`. Docker remains an
optional fallback through `make db-up-docker` and uses host port 5433.

Local connection details come from the ignored `.env` file:

```text
postgresql://auxiliator:auxiliator-local@127.0.0.1:5432/context_engine
```

The application creates the `vector` extension, `public.sales_playbook_chunks` table, primary key,
and department index automatically during startup.

## Verification

```bash
make test
make lint
make typecheck
```

See `docs/reference-coverage.md` for the screenshot/PDF fidelity audit.
