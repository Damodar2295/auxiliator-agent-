#!/bin/bash
set -euo pipefail

POSTGRES_APP="${POSTGRES_APP:-${HOME}/Applications/Postgres.app}"
PG_BIN="${POSTGRES_APP}/Contents/Versions/16/bin"

"${PG_BIN}/pg_isready" -h 127.0.0.1 -p 5432
