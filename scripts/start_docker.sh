#!/bin/bash
set -euo pipefail
export PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
if [[ "${EPAS_ENV:-}" == "" || "${EPAS_ENV:-}" == "local" ]]; then
  exec "${PYTHON_BIN}" -m agent.main --host 0.0.0.0 --port 8080
fi
exec gunicorn -c gunicorn.conf.py agent.main:app
