# AGENTS.md

Instructions for the coding agent working on the ERP API. Read this file first, then the docs in the order listed below.

## What we are building

A FastAPI service that exposes an existing SQL Server ERP to a Flutter app.

The ERP is **metadata-driven**. Browsers, forms, grids, pickers, variables, commands and permissions are all rows in the `[System].[Form.*]` tables, and the old PHP/JS front end is a generic renderer of those rows. This API is a second back end for a second renderer: it reads the **same** config, serves it as JSON, and runs generic CRUD and commands from it.

> **There is no per-screen code.** If a row changes in the config portal, the API must keep working with no deployment. Any code that mentions a specific form, grid, table or column name (for example `Sales.Order`) is a bug, except in tests.

The SQL Server database is the source of truth and stays unchanged. The old app and the new API run side by side on the same database.

## Reading order

1. `docs/01-overview.md`: how the ERP works (mental model and conventions)
2. `docs/02-project-structure.md`: module layout, `.venv` setup, commands, portability rules
3. `docs/03-config-tables.md`: every config table and column, with confidence levels
4. `docs/04-expression-language.md`: `::Param::` engine, variables, helper functions, formulas
5. `docs/05-api-contract.md`: endpoints and JSON shapes (the product; treat as frozen once published)
6. `docs/06-crud-engine.md`: generic read, save and delete algorithm
7. `docs/07-security-and-roles.md`: auth, roles, SQL safety rules
8. `docs/08-open-questions-and-roadmap.md`: unknowns with safe defaults, build order, test strategy
9. `docs/09-database-connection.md`: how the API connects to SQL Server (reused from the old project). **Read this before touching any database code.**

## Golden rules

1. **No per-screen code.** Everything comes from config rows and the SQL Server catalog (`sys.columns`).
2. **Never put a value into SQL text.** All values are bound parameters (`?`). Identifiers (table and column names) are allowed only if they exist in the catalog or config, and are then quoted as `[name]`.
3. **Run only SQL that is stored in config tables** (`hdr_expr`, `cmd_controlexpr`, combo queries). Never run SQL sent by a client.
4. **Session values come from the token, never from the request.** `_USERID`, `_USERLOGIN`, `_CCID`, roles and so on are filled by the server.
5. **Enforce roles on the server** for every endpoint. Hiding a button in the app is not security.
6. **Fail closed.** An empty or unparseable role list means denied. An unknown field in a payload is rejected, not ignored.
7. **Never execute text returned by a stored procedure.** Parse it into the whitelisted action list (see `docs/05-api-contract.md`) and drop and log the rest.
8. **Do not change the database schema or config rows.** The ERP database owns the schema: never create, alter, drop or migrate ERP tables, never add Alembic, and never write ORM models for ERP tables. Writes go only through the save engine to base tables and through configured commands.
9. **Stay portable.** The API contract and the language-neutral JSON test fixtures are the product. Keep logic in small, plain modules so it can be ported to PHP later.
10. **Do not guess unknowns.** If the docs mark something `[unknown]`, use the safe default from `docs/08` and leave a `# TODO(question): ...` comment.
11. **Use the shared database layer.** Import `settings` from `app.core.config` and `engine`/`get_db` (or `get_db_write`) from `app.core.db`. Never hardcode hosts, ports, users, passwords or the driver name, and never build a connection string by hand (use `URL.create`).
12. **Synchronous SQLAlchemy 2.0 with `pyodbc`.** Use plain `def` endpoints (FastAPI runs them in a threadpool). Do not add async database drivers.
13. **Multi-step writes are one transaction** with row locks and the edit-lock check (see `docs/06`). Roll back immediately on any error.

## Environment (use `.venv`)

Always work inside the project virtual environment named `.venv`. Never install packages globally and never commit `.venv`.

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Windows (cmd)
.venv\Scripts\activate.bat
# Linux / macOS
source .venv/bin/activate

pip install -e ".[dev]"
cp .env.example .env        # then fill in the staging DB settings
python scripts/check_db.py  # verify connectivity and permissions before starting the API
```

Common commands (run with the venv active):

```bash
uvicorn app.main:app --reload --port 8000    # run the API
pytest -q                                    # run tests
ruff check . && ruff format --check .        # lint and format check
docker compose up --build                    # run in a container (image includes msodbcsql18)
```

Add every new dependency to `pyproject.toml` (`dependencies` for runtime, the `dev` extra for dev only).

## Conventions

- Python 3.11 or newer, type hints everywhere, Pydantic v2 models for all request and response shapes.
- One feature per folder under `app/modules/`. Each module has `router.py`, `service.py`, `repository.py` and `schemas.py` (details in `docs/02`). SQL lives only in `repository.py` files and `app/shared/catalog.py`.
- JSON: **meta properties use camelCase**; **row and field data use the database column names verbatim** (for example `doc_id`, `trans_qty`), because field names must match the database.
- Errors use the envelope in `docs/05` and the exception classes in `app/core/errors.py`. Never return raw SQL error text to clients; log it with a request id.
- Log one line per request (request id, user id, route, duration) and one line per executed config SQL (screen code, duration, row count). Never log passwords, tokens or bound values of sensitive fields.
- Tests use the fixtures in `tests/fixtures/` (plain JSON: config rows and inputs, with the expected SQL, params and response). Add a fixture for every new rule.

## Working on a task

1. Read the relevant docs, and the `[unknown]` items that touch the task.
2. Write or extend the JSON fixtures first, then the code.
3. Keep the diff small and inside one module where possible.
4. Run `ruff` and `pytest`.
5. Update the docs if behavior changed. If you discovered something new about the config tables, add it to `docs/03` with a confidence level.

## Definition of done

- Tests pass and cover the new rule, including a permission-denied case and a bad-input case.
- No value is concatenated into SQL, and every endpoint checks roles.
- The change works for a screen the code has never seen (try a second config example, not only the pilot).
- Docs and fixtures are updated.

## Pilot screens

The first screens to get working end to end are `Browser.Sales.Order.Retail` (Take Order list), `Form.Sales.Order.Retail` (header) and `Grid.Sales.Order.Retail.Detail` (lines). Use them as test data, never as special cases in code.

## Reusing the old project

An earlier project already solved database connectivity and a hard-coded Take Order API. Reuse what it solved and nothing more:

- **Copy and extend** `app/core/config.py`, `db.py`, `errors.py`, `pagination.py`, `modules/health`, `scripts/check_db.py`, `sql/001_permissions.sql`, the Docker files, `pyproject.toml` and the config/health tests (details in `docs/09`).
- **Do not extend** its `orders` module. The generic form engine replaces it. Use it for facts (for example the rule that an order may be changed only while `docflow_seq == 0`) and its tests as golden cases for the pilot.
- The ERP database is on a remote SQL Server (Azure VM). Treat it as production until `docs/08` Q16 says otherwise: `ENABLE_WRITES` stays `false` outside a staging database.
