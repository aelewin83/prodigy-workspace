# Prodigy Workspace

Institutional Intelligence for Emerging GPs (NYC-first), built as a BOE-gated deal workspace.

## 1) Architecture Diagram (Text)

```
[Next.js Web App]
  -> calls -> [FastAPI API]
                |- Auth (JWT)
                |- Workspace/Deal APIs
                |- BOE Run APIs (PR1 stub outputs only)
                v
             [Postgres]
                |- users/workspaces/deals
                |- boe_runs (versioned input/output snapshots)
                |- boe_test_results (queryable PASS/FAIL/WARN/N/A)
                |- audit_log

[Redis + Worker Scaffold]
  reserved for Phase 2 ingestion jobs

[S3-compatible storage]
  reserved for Phase 2 document/comps ingestion
```

## 2) Repo Structure

```
apps/
  api/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
    alembic/
    tests/
  web/
    src/app/
infra/
```

## 3) DB Schema (Phase 1 implemented)

- `users`: id, email, hashed_password, full_name, created_at
- `workspaces`: id, name, created_by, created_at
- `workspace_members`: id, workspace_id, user_id, role
- `deals`: id, workspace_id, name, address, asking_price, created_by, created_at
- `boe_runs`: id, deal_id, version, inputs(JSONB/JSON), outputs(JSONB/JSON), decision, binding_constraint, hard_veto_ok, pass_count, advance, created_by, created_at
- `boe_test_results`: id, boe_run_id, test_key, test_name, test_class, threshold, actual, result(PASS/FAIL/WARN/N/A), note, created_at
- `audit_log`: id, workspace_id, user_id, entity_type, entity_id, action, payload, created_at

## 4) BOE Parity Plan

- Reverse engineer the Excel formulas in the BOE workbook fixture (`fixtures/boe/BOE_MF_Template_NYC.xlsx` or `BOE_WORKBOOK_PATH`) into a formula map (inputs -> derived metrics -> tests -> decision).
- Build a deterministic Python BOE engine module with explicit intermediate fields.
- Build parity harness:
  - load fixture scenarios with expected Excel outputs
  - compare percent/ratio fields to +/-0.10%
  - compare dollar fields to +/-$1 to +/-$5 based on sheet rounding
  - enforce exact match for each test result state (PASS/FAIL/WARN/N/A)
- PR1 intentionally returns placeholder BOE outputs/tests; parity logic ships in PR2.

## 5) PR Plan

- PR1: Scaffold repo + DB schema + auth + deals + BOE run storage (manual inputs, stub calcs)
- PR2: BOE engine implementation + parity harness vs Excel + PASS/FAIL/WARN/N/A + gate logic hardening
- PR3: BOE UI (inputs/outputs/tests) + run history + compare runs
- PR4: Gating + Full UW placeholders + deployment docs
- PR5: Hardening (audit, roles, performance)
- PR6 (Phase 2): Comps module (manual) + rollups/variance + export
- PR7 (Phase 2): Connector framework + private file ingest
- PR8 (Phase 2): Public connectors (allowlist) + caching + outlier detection

## 6) Top Risks + Mitigations

- Excel parity drift risk: mitigate with locked fixture harness and CI build-break on mismatch.
- Ambiguous spreadsheet assumptions: mitigate with documented formula dictionary + named source cells.
- Rounding inconsistency: mitigate with centralized rounding policy helpers.
- Unauthorized cross-workspace data access: mitigate with strict membership checks per endpoint.
- Scope creep in Phase 1: mitigate by keeping Full UW/ingestion placeholder-only until PR2+.

## PR1 Status

Implemented in this repo (PR1 scope):
- FastAPI scaffold with JWT auth endpoints
- Workspace and deal CRUD/list endpoints
- BOE run persistence with versioning and per-test result rows (stub values)
- Next.js navigation shell, deals list, deal detail, and BOE input form placeholder
- Alembic migration for Phase 1 schema
- Basic API and DB contract tests

## Phase 2 Comps Ingestion Scaffold

Implemented architecture scaffolding for connector/file-based comps ingestion:
- Canonical comps schema + migration (`comp_sources`, `comp_runs`, `comp_listings`, `comp_rollups`, `comp_subjects`, `comp_subject_variance`, `documents`, `document_spans`)
- Connector abstraction + allowlist-ready sample connector
- Private ingestors for CSV/XLSX and deterministic fail-soft PDF parser placeholder
- Deterministic normalization, dedupe, outlier (IQR), old-comp flagging, rollups, and subject variance
- RQ worker queue + Redis caching flow for public connectors
- API routes:
  - `POST /v1/deals/{deal_id}/comps/runs/manual`
  - `POST /v1/deals/{deal_id}/comps/runs/private-import`
  - `POST /v1/deals/{deal_id}/comps/runs/public-pull`
  - `GET /v1/deals/{deal_id}/comps/runs`
  - `GET /v1/deals/{deal_id}/comps/runs/{comp_run_id}/listings`
  - `GET /v1/deals/{deal_id}/comps/runs/{comp_run_id}/rollups`
  - `GET /v1/deals/{deal_id}/comps/runs/{comp_run_id}/variance`
  - `PUT /v1/deals/{deal_id}/comps/subjects`
  - `GET /v1/deals/{deal_id}/comps/recommendations`

## PR2 BOE Engine + Parity Harness

Implemented:
- Deterministic server-side BOE engine in `apps/api/app/boe/engine.py`
- Exact BOE test-state evaluation (`PASS`/`FAIL`/`WARN`/`N/A`) and gate logic:
  - all hard veto tests must pass
  - pass-count includes `PASS` and `WARN`
  - `advance` requires pass-count >= 4
- BOE API route integrated to execute engine:
  - `POST /v1/deals/{deal_id}/boe/runs`
  - `GET /v1/deals/{deal_id}/boe/runs`
- Persistence updates:
  - `boe_runs.outputs` now stores full engine output snapshot
  - `boe_test_results` stores numeric `threshold`/`actual` and string display fields
- Migration:
  - `0003_boe_test_display_fields.py` adds `threshold_display`, `actual_display`

Parity harness:
- Fixture parity module: `apps/api/app/boe/parity.py`
- Golden fixtures: `apps/api/tests/fixtures/boe/*.json`
- Runner script: `apps/api/scripts/run_boe_parity.py`
- Sample workbook cell map template: `apps/api/tests/fixtures/boe/cell_map.sample.json`
- Default workbook path: `fixtures/boe/BOE_MF_Template_NYC.xlsx`
- Override workbook path with env var: `BOE_WORKBOOK_PATH`

Run parity locally:
- `cd apps/api`
- `PYTHONPATH=. python3 scripts/run_boe_parity.py`

Workbook setup:
- Put the workbook at `fixtures/boe/BOE_MF_Template_NYC.xlsx`, or set:
- `export BOE_WORKBOOK_PATH="/absolute/path/to/BOE MF Template NYC.xlsx"`
- If the workbook is missing, parity exits with a clear error and setup instructions.

Validated output fields in parity fixtures:
- `market_cap_rate`
- `seller_noi_from_om`
- `asking_cap_rate`
- `analysis_cap_rate`
- `y1_exit_cap_rate`
- `y1_dscr`
- `y1_capex_value_multiple`
- `y1_expense_ratio`
- `y1_cash_on_cash`
- `y1_yield_on_cost_unlevered`
- `residual_sale_at_exit_cap`
- `profit_potential`
- `max_price_at_yoc`
- `max_price_at_capex_multiple`
- `max_price_at_coc_threshold`
- `boe_max_bid`
- `delta_vs_asking`
- `deposit_amount`
- `binding_constraint`

## PR4 Gating + FUW Hardening

Implemented:
- Formal deal gate state machine with canonical states:
  - `NO_RUN`, `KILL`, `ADVANCE`
- Deal-level persisted gating fields:
  - `deals.current_gate_state`
  - `deals.latest_boe_run_id`
- Gate transitions applied automatically on BOE run creation.
- BOE run immutability preserved (no update endpoints for `boe_runs`).
- Full underwriting protection:
  - backend route: `GET /v1/full-underwriting/deals/{deal_id}`
  - returns `403` unless `deal.current_gate_state == ADVANCE`
- Audit logging additions:
  - `CREATE_RUN` events on BOE run creation
  - `GATE_TRANSITION` events when gate state changes
  - fields added: `previous_state`, `new_state`, `created_by`

Frontend gating updates:
- Deal detail now shows canonical gate badge: `NO_RUN` / `KILL` / `ADVANCE`
- Explicit discipline copy:
  - `Hard Veto: X/3 PASS`
  - `Total: (PASS+WARN)/7 (>=4 required)`
- Full Underwriting tab disabled unless gate is `ADVANCE` with unlock tooltip.
- Dedicated underwriting route:
  - `/deals/{id}/underwriting`
  - locked UI state if backend returns `403`
  - unlocked placeholder tabs if allowed (`Pro Forma`, `Rent Roll`, `Waterfall`, `Debt Model`)

New backend endpoints:
- `GET /v1/full-underwriting/deals/{deal_id}` (protected by gate)
- Existing BOE endpoints retained:
  - `POST /v1/deals/{deal_id}/boe/runs`
  - `GET /v1/deals/{deal_id}/boe/runs`
  - `GET /v1/deals/{deal_id}/boe/runs/{run_id}`

Environment variables (deployment hardening):
- `APP_ENV` (set `prod` in production)
- `DEBUG` (`false` in production)
- `CORS_ALLOW_ORIGINS` (comma-separated allowed origins)
- `JWT_SECRET_KEY` (must be set securely)
- `DATABASE_URL`
- `REDIS_URL`

Production/dev artifacts:
- `Makefile`:
  - `make dev`
  - `make migrate`
  - `make test`
  - `make gate` (backend tests + parity gate + frontend lint/tests)
- Production Dockerfiles:
  - `apps/api/Dockerfile.prod`
  - `apps/web/Dockerfile.prod`
- Production compose:
  - `docker-compose.prod.yml`

## Local run

1. Create and activate a virtualenv from repo root:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
2. Install Python deps from repo root:
   - `pip install -r requirements-dev.txt`
3. Install frontend deps:
   - `cd apps/web && npm ci && cd ../..`
4. Run migrations:
   - `cd apps/api && alembic upgrade head && cd ../..`
5. Start stack:
   - `docker compose up --build`
6. Endpoints:
   - API: `http://localhost:8000`
   - Web: `http://localhost:3000`

## Gate Command

- Run full portability/tooling gate:
  - `make gate`
  - Optional override: `BOE_WORKBOOK_PATH="/absolute/path/to/BOE MF Template NYC.xlsx" make gate`
- `make gate` runs:
  - backend tests (`pytest`)
  - BOE parity runner (validates workbook path + fixture parity)
  - frontend lint/tests (`npm run lint`, `npm test`)
- In Codex sandbox or network-restricted environments (`CODEX_SANDBOX=1`), `make gate` prints:
  - `Gate must run in CI or local dev; this sandbox cannot install deps or run npm.`

Root command sequence (local/CI):
1. `python -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -r requirements-dev.txt`
4. `cd apps/web && npm ci && cd ../..`
5. `make gate`

## CI Gate

- GitHub Actions workflow: `.github/workflows/gate.yml`
- Runs on pull requests and executes `make gate` in a full CI environment after Python/Node setup.
- CI is strict about workbook fixture availability and fails if `fixtures/boe/BOE_MF_Template_NYC.xlsx` is missing.

## Deal Workspace (Phase 4)

Open the institutional deal workspace route:

- `/workspaces/<workspace_id>/deals/<deal_id>`

Quick local demo route:

- `/workspaces/local-workspace/deals/queens-24`

This page consumes:

- `GET /v1/workspaces/{workspace_id}/deals/{deal_id}/summary`
- `GET /v1/deals/{deal_id}/activity`
- `POST /v1/deals/{deal_id}/gate/override`
- `POST /v1/deals/{deal_id}/comments`
