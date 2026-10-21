# 02. Project structure

The project starts from the old project's skeleton (`app/core`, `modules/health`, `scripts/check_db.py`, `sql/`, Docker files, `pyproject.toml`; see `docs/09`) and adds the generic, module-based layout below.

## Layout (module-based)

```
erp-api/
├── AGENTS.md
├── README.md
├── .env.example
├── .gitignore                 # must list .venv/, .env, keys/, __pycache__/
├── .dockerignore
├── Dockerfile                 # includes msodbcsql18 (from the old project)
├── docker-compose.yml
├── pyproject.toml             # dependencies, dev extras, ruff and pytest settings
├── .venv/                     # local virtual environment, never committed
├── docs/                      # these documents
├── scripts/
│   ├── check_db.py            # read-only connectivity and permission diagnostic (old project)
│   └── gen_grants.py          # new: prints GRANT statements from config, for review
├── sql/
│   ├── 001_permissions.sql    # login, user and grants (old project, extended)
│   └── 002_generated_grants.sql   # generated, reviewed, run manually
├── app/
│   ├── main.py                # app factory, middleware, router registration, error handlers
│   ├── core/                  # cross-cutting infrastructure (no business rules)
│   │   ├── config.py          # pydantic-settings, absolute .env path (old project)
│   │   ├── db.py              # SQLAlchemy engines, sessions, get_db, get_db_write
│   │   ├── errors.py          # AppError and handlers (old project, extended)
│   │   ├── pagination.py      # keyset cursor helpers (old project)
│   │   ├── security.py        # JWT sign/verify, password hashing
│   │   ├── deps.py            # FastAPI dependencies: current_user, require_roles
│   │   └── logging.py
│   ├── shared/                # reusable engines, pure Python, no FastAPI imports
│   │   ├── params.py          # ::Param:: to ? binding engine
│   │   ├── expr/              # helper functions and safe expression evaluator
│   │   ├── roles.py           # role list matching
│   │   ├── catalog.py         # sys.columns reader with cache
│   │   └── types.py           # type normalization (col_type, datatype, uitype)
│   └── modules/               # one folder per feature
│       ├── health/            # /health and /health/db (old project; router.py only)
│       ├── auth/              # login, refresh, /me
│       ├── menu/              # navigation from the menu/tree tables
│       ├── meta/              # config loader, normalizer, schemaVersion
│       ├── browser/           # meta + rows, layout hints
│       ├── form/              # read, create, update, delete
│       ├── grid/              # grid rows (used by form and standalone)
│       ├── picker/            # lookup search and combo options
│       ├── command/           # toolbar commands, action parsing
│       ├── admin/             # config linter, cache refresh
│       └── orders/            # LEGACY, hard-coded Take Order module: reference only (docs/09)
└── tests/
    ├── conftest.py            # fixtures and test environment (old project)
    ├── test_config.py         # config and environment validation (old project)
    ├── test_health.py         # health endpoints (old project)
    ├── test_orders.py         # legacy: use as golden cases for the pilot
    ├── fixtures/              # language-neutral JSON cases
    ├── shared/
    └── modules/
```

## Module anatomy

Every feature folder under `app/modules/` (except `health`, which has only `router.py`) has the same files:

| File | Responsibility | May import |
|---|---|---|
| `router.py` | HTTP only: parse request, call service, return response | its own `service`, `schemas`, `core.deps` |
| `service.py` | Business logic and orchestration | its own `repository`, `schemas`, `shared.*`, other modules' **service** |
| `repository.py` | All SQL for the module | `core.db`, `shared.catalog`, `shared.params` |
| `schemas.py` | Pydantic request and response models | nothing from the app except `shared.types` |
| `__init__.py` | Exports `router` and the module's public service functions | |

Dependency rules:

1. Direction is `router -> service -> repository`. Never skip a layer, never go backwards.
2. A module may call another module's **service** (through its `__init__` exports), never its repository or router.
3. `shared/` imports nothing from `modules/`. `core/` imports nothing from `modules/` or `shared/` (except `config`).
4. SQL strings appear only in `repository.py` files and `shared/catalog.py`.
5. `meta/` is the only module that reads the `[System].[Form.*]` config tables. Everything else asks `meta` for normalized objects.
6. Sessions come from `Depends(get_db)` or `Depends(get_db_write)` in routers and are passed down. Repositories never open their own sessions (`docs/09`).

Register routers in `app/main.py`: feature routers under `/v1`, health routers without a prefix.

```python
app.include_router(health.router)                 # /health, /health/db
app.include_router(auth.router, prefix="/v1")
```

## Environment setup with `.venv`

```bash
python -m venv .venv

# activate
.venv\Scripts\Activate.ps1        # Windows PowerShell
.venv\Scripts\activate.bat        # Windows cmd
source .venv/bin/activate         # Linux / macOS

python -m pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env              # fill in the database settings
python scripts/check_db.py        # verify connectivity and permissions
uvicorn app.main:app --reload --port 8000
```

Interactive API docs are at `http://localhost:8000/docs`, and the OpenAPI JSON at `/openapi.json`.

**Docker:** `docker compose up --build`. The image installs `msodbcsql18` (from the old project's `Dockerfile`).

**SQL Server driver (without Docker):** install "ODBC Driver 18 for SQL Server". On Linux install `msodbcsql18` and `unixodbc`. `DB_DRIVER` must match the installed name.

### `pyproject.toml` (dependencies)

Take the old project's `pyproject.toml` and add the new dependencies:

```toml
[project]
name = "erp-api"
requires-python = ">=3.11"
dependencies = [
  "fastapi",
  "uvicorn[standard]",
  "sqlalchemy>=2.0",
  "pyodbc",
  "pydantic>=2",
  "pydantic-settings",
  "PyJWT[crypto]",        # new: RS256 tokens
  "argon2-cffi",          # new: strong password hash
  "python-multipart",     # new
]

[project.optional-dependencies]
dev = ["pytest", "httpx", "ruff"]
```

Add every new dependency here (runtime in `dependencies`, test and lint tools in the `dev` extra), with a pinned minor version once chosen.

### `.env.example`

```
ENV=dev

# database (names follow the old project)
DB_HOST=
DB_PORT=1433
DB_NAME=
DB_USER=                      # read-only login in production
DB_PASSWORD=
DB_WRITE_USER=                # read-write login; empty = reuse DB_USER (dev only)
DB_WRITE_PASSWORD=
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_TRUST_SERVER_CERT=no       # yes only for development
DB_CONNECT_TIMEOUT_SECONDS=10
DB_POOL_RECYCLE_SECONDS=1800

# limits and switches
QUERY_TIMEOUT_SEC=30
ROW_CAP=1000
CONFIG_CACHE_TTL_SEC=60
ENABLE_WRITES=false           # true only against a staging database
ENABLE_DELETE=false
EDIT_LOCK_FIELD=docflow_seq
EDIT_LOCK_VALUE=0

# auth
JWT_PRIVATE_KEY_PATH=./keys/jwt_private.pem
JWT_PUBLIC_KEY_PATH=./keys/jwt_public.pem
JWT_ACCESS_TTL_MIN=30
JWT_REFRESH_TTL_DAYS=14
CORS_ORIGINS=
```

Never commit `.env` or the `keys/` folder.

## Portability to PHP

The API may be ported to PHP later (the Flutter app only sees HTTP and JSON). Keep that cheap:

1. **The OpenAPI contract is the product.** Routes live under `/v1`. Once a shape is published, change it only by adding fields or a new version.
2. **Keep modules small and rule-based.** About 8 pieces must be ported: param engine, role matcher, config loader, save engine, action parser, default resolver, login, paging. Use plain code and SQL. No ORM for ERP tables, no pandas, no Python-only tricks. SQLAlchemy is only the pool and transaction manager.
3. **Language-neutral fixtures.** `tests/fixtures/*.json` hold config rows and inputs plus the expected SQL text, bound params and response JSON. A PHP port runs the same files.
4. **RS256 JWTs** so another service can verify tokens with the public key.
5. **Known PHP differences:** SQL Server drivers (`sqlsrv`, PDO_SQLSRV) handle multiple result sets and decimal types differently from pyodbc. Normalize decimals and dates in one place (`shared/types.py`).
6. During a migration, put a reverse proxy in front and move one route at a time; both backends read the same database.
