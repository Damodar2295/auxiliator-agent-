#!/bin/bash
set -euo pipefail

POSTGRES_APP="${POSTGRES_APP:-${HOME}/Applications/Postgres.app}"
PG_BIN="${POSTGRES_APP}/Contents/Versions/16/bin"
PG_DATA="${PG_DATA:-${HOME}/Library/Application Support/Postgres/var-16}"
PG_LOG="${PG_LOG:-${HOME}/Library/Application Support/Postgres/postgres-16.log}"

if [[ ! -x "${PG_BIN}/pg_ctl" ]]; then
  echo "PostgreSQL 16 is not installed at ${POSTGRES_APP}" >&2
  exit 1
fi

if "${PG_BIN}/pg_isready" -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
  echo "PostgreSQL is already running on 127.0.0.1:5432"
  exit 0
fi

"${PG_BIN}/pg_ctl" -D "${PG_DATA}" -l "${PG_LOG}" start
"${PG_BIN}/pg_isready" -h 127.0.0.1 -p 5432
