.PHONY: install test lint typecheck run frontend-install frontend-dev frontend-test frontend-build verify security-audit db-up db-down db-status db-shell db-up-docker db-down-docker
install:
	./scripts/install.sh
test:
	.venv/bin/python -m pytest -q
lint:
	.venv/bin/ruff check .
typecheck:
	.venv/bin/mypy agent config
run:
	./scripts/start_local.sh
frontend-install:
	cd frontend && npm install
frontend-dev:
	cd frontend && npm run dev
frontend-test:
	cd frontend && npm test
frontend-build:
	cd frontend && npm run build
verify: lint typecheck test frontend-test frontend-build
security-audit:
	! rg -n '(BEGIN (RSA|OPENSSH) PRIVATE KEY|AKIA[0-9A-Z]{16})' --glob '!frontend/node_modules/**' --glob '!.git/**' .
db-up:
	./scripts/start_postgres.sh
db-down:
	./scripts/stop_postgres.sh
db-status:
	./scripts/postgres_status.sh
db-shell:
	PGPASSWORD=auxiliator-local "/Users/$${USER}/Applications/Postgres.app/Contents/Versions/16/bin/psql" -h 127.0.0.1 -p 5432 -U auxiliator -d context_engine
db-up-docker:
	docker compose up -d postgres
db-down-docker:
	docker compose down
