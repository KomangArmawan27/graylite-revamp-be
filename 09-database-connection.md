# 09. Database connection (reused from the old project)

This document keeps the approach of the old project's `connect.md` and adapts it to the generic, metadata-driven API. **Copy the old project's real files and extend them; do not rewrite them.** The code blocks below only show the pattern.

## 1. Approach

The API connects to the remote Microsoft SQL Server ERP database (an Azure VM) with **synchronous SQLAlchemy 2.0** and **`pyodbc`** using **Microsoft ODBC Driver 18 for SQL Server**.

- SQLAlchemy is used as a **connection pool and transaction manager**. The generic engine runs raw SQL (config SQL and catalog queries), so there are **no ORM models for ERP tables**.
- Endpoints are plain `def` functions. FastAPI runs them in a threadpool. `pyodbc` is blocking, so do not add async database drivers.
- The ERP database owns the schema. Never create, alter, drop or migrate ERP tables, and do not add Alembic.

## 2. Files to copy from the old project

| File | Role | Change for the generic API |
|---|---|---|
| `app/core/config.py` | `pydantic-settings`, absolute `.env` path, `get_sqlalchemy_database_url()`, fail-fast validation | Add settings for the write login, JWT, limits and feature switches (table in section 3) |
| `app/core/db.py` | Engine, `SessionLocal`, `get_db` | Add a second engine and `get_db_write` (section 4) |
| `app/core/errors.py` | `AppError` and unified handlers | Add the error codes from `docs/05` (`schema_stale`, `validation_failed`, ...) |
| `app/core/pagination.py` | Keyset cursor helpers | Reuse for browser rows and picker rows (`docs/05`) |
| `app/modules/health/router.py` | `/health`, `/health/db` | Keep as is |
| `scripts/check_db.py` | Read-only connectivity and permission diagnostic | Add checks (section 7) |
| `sql/001_permissions.sql` | Login, user and table grants | Extend for the generic engine (section 6) |
| `Dockerfile`, `docker-compose.yml`, `.dockerignore` | Container build with `msodbcsql18` | Keep |
| `pyproject.toml` | Dependencies, dev extras, ruff | Add `PyJWT[crypto]`, `argon2-cffi`, `python-multipart` |
| `tests/conftest.py`, `test_config.py`, `test_health.py` | Test setup and config tests | Keep; add new tests beside them |

The old `app/modules/orders/` is **reference only** (section 9).

## 3. Settings

Loaded with `pydantic-settings` from an absolute `.env` path. The API refuses to start if a required value is missing.

| Variable | Required | Purpose |
|---|---|---|
| `DB_HOST`, `DB_PORT`, `DB_NAME` | yes (port defaults to 1433) | SQL Server address and database |
| `DB_USER`, `DB_PASSWORD` | yes | Default login. In production this is the **read-only** login. |
| `DB_WRITE_USER`, `DB_WRITE_PASSWORD` | no | **Read-write** login for saves and commands. If empty, the default login is used (dev only). |
| `DB_DRIVER` | no | Default `ODBC Driver 18 for SQL Server` |
| `DB_TRUST_SERVER_CERT` | no | `yes` only for development with a self-signed certificate |
| `DB_CONNECT_TIMEOUT_SECONDS` | no | Fail fast on network problems |
| `DB_POOL_RECYCLE_SECONDS` | no | Recycle idle connections across the remote network |
| `QUERY_TIMEOUT_SEC`, `ROW_CAP` | no | Per-query limits |
| `CONFIG_CACHE_TTL_SEC` | no | Config cache lifetime |
| `ENABLE_WRITES` | no | Default `false`. When false, save, delete and commands that write are rejected. Turn on only against a staging database. |
| `ENABLE_DELETE` | no | Default `false`. See `docs/06`. |
| `EDIT_LOCK_FIELD`, `EDIT_LOCK_VALUE` | no | Defaults `docflow_seq` and `0`. See `docs/06`. |
| `JWT_*`, `CORS_ORIGINS`, `ENV` | see `docs/02` | Auth and runtime |

Never hardcode credentials, hosts, ports or the driver name. Never build a connection string by hand: use `sqlalchemy.engine.URL.create(...)`, which handles special characters (`@`, `:`, `/`) in passwords.

## 4. Engine and sessions

Pattern (extend the old `db.py`; keep its existing names `engine`, `SessionLocal`, `get_db`):

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings, get_sqlalchemy_database_url


def _make_engine(user: str, password: str):
    # get_sqlalchemy_database_url(settings, user=..., password=...) wraps URL.create(...)
    return create_engine(
        get_sqlalchemy_database_url(settings, user=user, password=password),
        connect_args={"timeout": settings.DB_CONNECT_TIMEOUT_SECONDS},  # fail fast
        pool_pre_ping=True,                                             # drop dead sockets
        pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
        execution_options={"fast_executemany": True},                   # as in the old project
    )

engine = _make_engine(settings.DB_USER, settings.DB_PASSWORD)           # read login
engine_write = _make_engine(
    settings.DB_WRITE_USER or settings.DB_USER,
    settings.DB_WRITE_PASSWORD or settings.DB_PASSWORD,
)                                                                       # write login

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
SessionWrite = sessionmaker(bind=engine_write, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_write():
    db = SessionWrite()
    try:
        yield db
    finally:
        db.close()
```

Notes:

- `fast_executemany` only affects `executemany` calls. SQLAlchemy documents it as a `create_engine(..., fast_executemany=True)` argument for `mssql+pyodbc`. Check that the old project's `execution_options` form really takes effect, and switch if it does not.
- Use `get_db` for meta, browsers, pickers and reads. Use `get_db_write` only in the save engine and the command runner.
- Inject sessions with `Depends(get_db)` or `Depends(get_db_write)` in routers and pass them down to services. Repositories never create their own sessions.

## 5. How the generic engine uses the connection

- **Config SQL** (`hdr_expr`, grid expressions, combo queries, commands): the param engine returns SQL with `?` markers and an ordered list. Run it with `db.connection().exec_driver_sql(sql, tuple(params))`. Do not use `text()` for it (`text()` expects named binds).
- **Fixed repository SQL and catalog queries:** `text()` with named binds is fine.
- **Transactions:** one transaction per write request.

  ```python
  def save_form(db, payload, ...):
      try:
          conn = db.connection()
          # lock, validate, insert header (OUTPUT ... INTO @o), write grids
          db.commit()
      except Exception:
          db.rollback()
          raise
  ```

- **Bulk grid rows:** `executemany` with `fast_executemany` is fine for rows whose generated ids are not needed (the record is re-read after the save). Insert the **header** with a single execute and the `OUTPUT ... INTO` pattern (`docs/06`).
- **Query timeout:** set per request on the raw DBAPI connection (`QUERY_TIMEOUT_SEC`), in a helper in `core/db.py`. The connect timeout comes from `DB_CONNECT_TIMEOUT_SECONDS`.
- **Locking and the edit lock** (`WITH (UPDLOCK, ROWLOCK)`, `docflow_seq = 0`): see `docs/06`.

## 6. Permissions

The old project grants `SELECT`, `INSERT`, `UPDATE`, `DELETE` on the two order tables in `sql/001_permissions.sql`. The generic engine reaches many more objects:

| Login | Needs |
|---|---|
| Read login (`DB_USER`) | `SELECT` on `[System].[Form.*]`, `User.*` and the objects behind config SQL (tables, views, table-valued functions); `VIEW DEFINITION` (or `SELECT`) on every base table so `sys.columns` returns its columns. Catalog visibility depends on these permissions: an empty `sys.columns` result for a real table means a missing grant. |
| Write login (`DB_WRITE_USER`) | `INSERT`, `UPDATE`, `DELETE` on the base tables (`hdr_basetable` values) and `EXECUTE` on procedures used by commands |

Per-table grants by hand do not scale (179 forms, 152 grids). Add `scripts/gen_grants.py`, which reads the config and prints the `GRANT` statements for every base table and command procedure. Save the reviewed output as `sql/002_generated_grants.sql` and run it manually. The API never runs `GRANT` or any DDL.

## 7. Diagnostic script (`scripts/check_db.py`)

Read-only. Keep the old checks: configuration (no passwords), TCP reachability of `DB_HOST:DB_PORT`, ODBC Driver 18 presence, login (`SELECT 1`), server metadata and TLS (`sys.dm_exec_connections`), visibility of the order tables, permission checks (`HAS_PERMS_BY_NAME`), and a sample read.

Add these checks:

1. The `[System].[Form.Headers]`, `Form.Browsers`, `Form.Details`, `Form.Grids`, `Form.Variables`, `Form.Commands`, `User.Management` and `User.Level` tables are readable. (Table names for Grids, Variables and Commands are inferred; confirm them.)
2. `sys.columns` returns columns for `Sales.[Order.Retail.Header]` and `Sales.[Order.Retail.Detail]` (catalog visibility).
3. The same permission matrix for the write login when `DB_WRITE_USER` is set.

The script never writes.

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `IM002` (data source name not found) | ODBC Driver 18 missing or `DB_DRIVER` mismatch | Install `msodbcsql18` and `unixodbc`; check `pyodbc.drivers()` |
| Timeout, `08001`, TCP failure | Network block, wrong host or port, firewall, Azure NSG | Run `python scripts/check_db.py`; verify reachability and that the API's outbound IP is allowed in the NSG |
| `28000` / error 18456 (login failed) | Wrong password, SQL authentication not enabled, disabled login | Check `.env`; confirm mixed mode authentication |
| SSL or certificate verify failed | Self-signed certificate without trust | `DB_TRUST_SERVER_CERT=yes` in development; install a trusted certificate for production |
| Error 4060 (cannot open database) | Wrong `DB_NAME` or no `CONNECT` permission | Check the name; grant `CONNECT` |
| Error 229 (permission denied on a table) | Missing `SELECT`, `INSERT`, `UPDATE` or `DELETE` | Review `sql/001_permissions.sql` and the generated grants |
| Error 229 on a procedure or function | Missing `EXECUTE` (procedures) or `SELECT` (table-valued functions) | Add the grant for the write or read login |
| `sys.columns` returns nothing for an existing table | Missing `VIEW DEFINITION` or `SELECT` | Grant it to the login that reads the catalog |
| Error 1033 (`ORDER BY` in a derived table) | The read wrapper in `docs/06` met an expression with `ORDER BY` | See the wrapper caveats in `docs/06`; the linter reports these |

## 9. The legacy `orders` module

The old `app/modules/orders/` (`models.py`, `schemas.py`, `router.py`, `service.py`) is hard-coded for Take Order. In the generic API it is replaced by the form engine.

- **Do not extend it and do not copy its structure.** No ORM models for ERP tables.
- **Use it as a source of facts.** The old project already inserts and updates `Sales.[Order.Retail.Header]` and `Sales.[Order.Retail.Detail]` directly, runs updates and deletes in one transaction, takes row locks and requires `docflow_seq == 0` before modifying records. It also implements idempotency and keyset pagination. Review `orders/service.py` and `models.py` to settle `docs/08` Q1, Q2 and Q15 (how `doc_no` and the initial `docflow_seq` are set, how delete works, how idempotency is stored).
- **Use its tests as golden cases.** `tests/test_orders.py` (creation, updates, pagination) gives expected results for the pilot. Port them into `tests/fixtures/` as language-neutral cases and require the generic engine to produce the same rows.

## 10. Rules for agents

1. Always import `settings` from `app.core.config` and `engine`/`get_db` (or `get_db_write`) from `app.core.db`.
2. Never hardcode hosts, ports, users, passwords or the driver name; never concatenate connection strings.
3. Synchronous SQLAlchemy 2.0 and `pyodbc` only.
4. Wrap multi-step writes in one transaction and roll back immediately on any error.
5. Take row locks and check the edit lock before updating or deleting (`docs/06`).
6. Do not create, alter, drop or migrate ERP tables; no Alembic; no ORM models for ERP tables.
7. Fix connection problems with the table in section 8 and `scripts/check_db.py` before changing code.
