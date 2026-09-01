# Auxiliator Agent

Auxiliator rebuilt using the supplied AIX/LangGraph backend-agent boilerplate.

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

At startup, every Markdown file under `knowledge/<department>/` is chunked, embedded, and idempotently upserted into PostgreSQL. PostgreSQL is the system of record for chunk content, metadata, and embeddings; no separate vector-database service is used. The internal SafeChain embedding provider is selected when installed, with a deterministic local embedding adapter for development.

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

The application creates the `vector` extension, `public.knowledge_chunks` table, primary key, and department index automatically during startup.

## Verification

```bash
make test
make lint
make typecheck
```

See `docs/reference-coverage.md` for the screenshot/PDF fidelity audit.
