.PHONY: dev migrate test test-api test-web lint-web parity parity-fixture gate gate-full gate-sandbox install-api-dev install-web

dev:
	docker compose up --build

migrate:
	cd apps/api && alembic upgrade head

install-api-dev:
	python3 -m pip install -r requirements-dev.txt

install-web:
	cd apps/web && if [ ! -d node_modules ]; then npm ci; fi

test-api:
	cd apps/api && pytest -q --cov=app --cov-config=../../.coveragerc --cov-report=term-missing --cov-report=xml:coverage.xml --cov-report=html:htmlcov

BOE_WORKBOOK_PATH ?= $(CURDIR)/fixtures/boe/BOE_MF_Template_NYC.xlsx

parity:
	cd apps/api && BOE_WORKBOOK_PATH="$(BOE_WORKBOOK_PATH)" PYTHONPATH=. python3 scripts/run_boe_parity.py

parity-fixture:
	cd apps/api && PYTHONPATH=. python3 -c "from pathlib import Path; from app.boe.parity import run_fixture_parity; p=Path('tests/fixtures/boe'); e=run_fixture_parity(p); [print(x) for x in e]; raise SystemExit(1 if e else 0)"

lint-web:
	cd apps/web && npm run lint

test-web:
	cd apps/web && npm test

test: test-api

gate:
	@if [ "$$CODEX_SANDBOX" = "1" ] || [ "$$NETWORK_RESTRICTED" = "1" ] || ! command -v npm >/dev/null 2>&1; then \
		$(MAKE) gate-sandbox; \
	else \
		$(MAKE) gate-full; \
	fi

gate-full: install-api-dev install-web test-api parity lint-web test-web

gate-sandbox:
	@echo "Gate must run in CI or local dev; this sandbox cannot install deps or run npm."
