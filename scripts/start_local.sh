#!/bin/bash
set -euo pipefail
echo "Starting AIX RAG Chatbot Template..."
if [[ -f .env ]]; then set -a; source .env; set +a; fi
export EPAS_ENV="${EPAS_ENV:-local}"
export DEBUG_MODE="${DEBUG_MODE:-true}"
if [[ ! -d .venv ]]; then ./scripts/install.sh; fi
exec .venv/bin/uvicorn agent.main:app --reload --host 0.0.0.0 --port "${PORT:-8080}"
