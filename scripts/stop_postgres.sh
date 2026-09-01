#!/bin/bash
set -euo pipefail

POSTGRES_APP="${POSTGRES_APP:-${HOME}/Applications/Postgres.app}"
PG_BIN="${POSTGRES_APP}/Contents/Versions/16/bin"
PG_DATA="${PG_DATA:-${HOME}/Library/Application Support/Postgres/var-16}"

if ! "${PG_BIN}/pg_ctl" -D "${PG_DATA}" status >/dev/null 2>&1; then
  echo "PostgreSQL is not running"
  exit 0
fi

"${PG_BIN}/pg_ctl" -D "${PG_DATA}" stop -m fast
