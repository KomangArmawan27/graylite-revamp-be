# 12. Backend hardening, contract fixes and performance

**Status:** change request. Where this file differs from `docs/05`, `docs/06`, `docs/10` or `docs/11`, **this file wins**. It is based on the real request and response samples from the running API (menu, browser meta, form meta, grid meta, picker meta, browser rows, `/new`, and a create).

Work in the order **P0, P1, P2, P3**. Each item has acceptance tests. Do not start P2 before P0 and P1 are done.

## Scope

**Do not touch** (already done and working): `app/core/config.py` and `.env` handling, `app/core/db.py`, authentication and authorization (`app/core/security.py`, `app/core/deps.py`, `app/modules/auth/*`, the role matcher), and `app/modules/health/*`.

**Allowed:**

- extend `app/modules/{meta,menu,browser,form,grid,picker,command,admin}`, `app/shared/*`, `app/core/errors.py`, `app/core/pagination.py`
- add `app/core/cache.py`, `app/core/timing.py`, `app/core/metrics.py`
- `app/main.py`: additive lines only (middleware, router includes)
- `pyproject.toml`: add dependencies only
- read optional settings with `getattr(settings, "NAME", default)`; do not add settings. Put constants in the module that uses them.

Anything that needs a database schema change is a **proposal only**. Do not implement it (see "Owner decisions").

---

# P0: correctness and safety

## P0.1 Role checks on every write

**Problem.** In the real sample, the browser `Browser.Sales.Order` reports `canAdd: false`, yet `POST /v1/forms/129/records` succeeded. Check whether that user was an admin. If not, writes are not enforcing roles.

**Rules** (using the existing role matcher; `docs/07` explains the role lists):

| Operation | Allowed when |
|---|---|
| Open, read, `new` | The form's `hdr_level` allows the user |
| **Create** | The form's `hdr_level` allows the user **and** at least one **browser that opens this form** (its `dtl_code` points to the form) is visible to the user and its `doc_header` Add/Remove list allows the user (the same rule that sets `canAdd`) |
| **Update** | The form's `hdr_level` allows the user (and the edit lock in `docs/06`) |
| **Delete** | Same as create (`canRemove`), plus `ENABLE_DELETE` and the edit lock |
| **Run command** | Screen Visible, then `cmd_privilege` |

If no browser points to the form, **create and delete are denied** (fail closed) and a warning is logged with the `hdrId`.

Implementation: in `meta`, build a reverse index (form `hdr_id` to the browsers whose trimmed `dtl_code` matches it) with the config cache, and expose `can_add(user, form_hdr_id)` and `can_remove(...)`. The browser meta's `canAdd` and the create endpoint must use the **same function**.

**Acceptance:** a user not in the add list gets `403 forbidden` on create and delete; a user in the list succeeds; a form with no referencing browser denies create; the browser meta and the create endpoint agree for the same user.

## P0.2 Readonly fields in the save engine

**Problem.** The sample create sent the readonly field `doc_no` and the server stored it, while real new entries show `doc_no: ""` (the number is assigned later). Clients must not set server-controlled fields.

**Rules:**

- For a field marked `readonly`, **ignore the client's value** (drop it silently, log at debug). Exception: **`widget = formula`** fields are accepted, because their values are computed on the client and saved (311 saved formulas, `docs/04`); validate type and range only.
- **On create**, for each updatable field the client did not send (or that was dropped as readonly), apply its `col_defaultvalue` resolved by the helper library (`TODAY()`, `_USERID`, ...). If there is no default, omit the column and let the database default or trigger fill it.
- **On update**, readonly fields are never written, and the record id is never written.
- Hidden, non-readonly fields (ids filled by pickers, `cust_id`) are accepted from the client.

Open point (verify with the Profiler trace, `docs/08` Q1): whether the old front end ever sends readonly fields such as `doc_no`. If it does and the database needs them, change this rule, not the code.

**Acceptance:** a create with `doc_no` in the payload does not store it; a create without `doc_date` stores the resolved `TODAY()` default; a formula field value is saved; a client-supplied `doc_id` on update is ignored.

## P0.3 Idempotent create

The `Idempotency-Key` header is accepted but ignored, and mobile networks retry. Implement behind an interface so storage can change:

```python
class IdempotencyStore(Protocol):
    def begin(self, key: str, user_id: int, route: str, body_hash: str) -> Replay | InFlight | New: ...
    def finish(self, key: str, user_id: int, route: str, status: int, body: bytes) -> None: ...
```

Behavior (only on `POST /v1/forms/{hdrId}/records`):

- Key format `^[A-Za-z0-9_-]{8,64}$`; otherwise `400 bad_request`.
- Scope the key by user id, route and a hash of the body.
- Same key and same body after completion: return the stored response with `Idempotent-Replay: true`. Do not write again.
- Same key, different body: `409 conflict` (`details[0].code = key_reused`).
- Same key while the first request is still running: `409 conflict` (`details[0].code = in_progress`).
- Retention 24 hours. Store only successful (2xx) results.

**Ship now:** an in-process store (`app/core/cache.py`), clearly documented as valid for **a single worker only** and lost on restart. Log a startup warning if more than one worker is detected.

**Proposal, not implemented:** a small durable table (for example `[System].[Api.Idempotency]`) for several workers. It is a schema addition, so it needs the owner's approval (`docs/09`, rule 6). Write the SQL as a proposal in `sql/proposals/`, do not run it.

**Acceptance:** two identical requests create one record; a different body with the same key gives 409; a failed save (4xx or 5xx) can be retried with the same key.

## P0.4 Writes switch

- Confirm `ENABLE_WRITES` is false by default in code and in `.env.example`, and that it is checked by create, update, delete and writing commands (`403 forbidden`).
- At startup, log one line with the database name and whether writes and delete are enabled. Never log credentials.

**Acceptance:** with the switch off, every write endpoint returns 403 and nothing changes in the database.

---

# P1: contract fixes (they block the front end)

## P1.1 One builder for grid meta (embedded and standalone)

The grid inside form meta is currently a reduced copy. Use **one function** (`build_grid_meta`) for both `GET /v1/meta/grid/{hdrId}` and the `grids` map in `GET /v1/meta/form/{hdrId}`. Shape:

```json
{
  "hdrId": 132,
  "code": "Grid.Sales.Order.Detail",
  "caption": "Sales Item",
  "rowKey": "trans_id",
  "parentField": "doc_id",
  "rowNumberField": "trans_idx",
  "canAddRemove": true,
  "saveWithForm": true,
  "columns": [
    { "name": "trans_id", "caption": "Trans Id", "widget": "integer", "type": "integer",
      "hidden": true, "readonly": true, "update": true, "scale": 0, "width": 100 },
    { "name": "item_no", "caption": "Code", "widget": "picker", "type": "text",
      "hidden": false, "readonly": false, "update": false, "pickerCode": "Picker.Inventory.Item.brgJadi", "pickerHdrId": 803 },
    { "name": "trans_qty", "caption": "Qty", "widget": "number", "type": "number",
      "hidden": false, "readonly": false, "update": true, "scale": 2 },
    { "name": "trans_total", "caption": "Total", "widget": "formula", "type": "money",
      "hidden": false, "readonly": true, "update": false, "scale": 0, "expression": "trans_qty*trans_price" }
  ],
  "variables": [
    { "name": "docqty", "aggregate": "sum", "column": "trans_qty" }
  ]
}
```

- Sources: `parentField` is the grid column with `col_key = 2`, `rowKey` is `col_key = 1`, `rowNumberField` is `col_key = 3`; `canAddRemove` is `hdr_addremove = 1`; `saveWithForm` is the `col_update` flag of the form's grid field; `variables` come from the grid's `Form.Variables` rows with `var_aggr = sum`.
- Keep `rowKey` (already used by the real API), not `rowIdField`.
- `caption` falls back to the grid field's `col_caption` in the form when the grid's own caption is empty (the sample shows `""`).

**Acceptance:** the embedded grid meta equals the standalone grid meta for the same `hdrId` (deep equality test), and contains `widget`, `update`, `readonly`, `expression` for formula columns, and `variables`.

## P1.2 Real column types

In the sample, every grid column has `type: "text"`, including `trans_qty` and `trans_total`. Fix with one function in `shared/types.py`:

1. By `col_uitype`: `integer`, `number`, `money`, `date`, `datetime`, `boolean` map to themselves; `image` and `document` map to themselves.
2. Otherwise by `col_datatype`: `number` becomes `number` (or `integer` when scale is 0 and the column name ends in `_id`), `date` becomes `date`, `datetime` becomes `datetime`, `integer` becomes `integer`.
3. Otherwise `text`. For `formula` columns use the datatype, or `number` if unknown.

Every column in browser, form and grid meta (and picker meta) carries both `widget` (the normalized uitype) and `type` (the value type). Form fields currently have `dataType: "text"` for dates; add the same `type` there and keep `dataType` for compatibility.

**Acceptance:** `trans_qty` is `number` with scale 2, `trans_total` is `money`, `doc_date` fields are `date`; a table-driven test covers every uitype and datatype combination.

## P1.3 Form variables and aggregates

In the sample, form meta has `{ "name": "docQty", "from": "" }`, which tells the app nothing. Replace the `variables` array with:

```json
{ "name": "docQty",  "kind": "aggregate", "gridHdrId": 132, "aggregate": "sum", "column": "trans_qty" }
{ "name": "DocID",   "kind": "field",     "from": "doc_id" }
{ "name": "docTotal","kind": "aggregate", "gridHdrId": 132, "aggregate": "sum", "column": "trans_total" }
```

Resolution: a form variable with an expression that names a field is `kind: "field"`. A form variable with no expression (or an expression naming a grid variable) that matches, **case-insensitively**, a grid variable of an embedded grid becomes `kind: "aggregate"` with the grid's `aggregate` and `column`. Anything unresolved is `kind: "unresolved"` with a linter warning, never an error.

**Acceptance:** `docQty` resolves to the sum of `trans_qty` of grid 132; an unresolved name is reported by the linter.

## P1.4 One number serialization rule

Rows currently return decimals as strings (`"1.0000"`) while the create response returns numbers (`840000`). Use **one serializer** (`serialize_row(row, columns)` in `shared/types.py`) for browser rows, form reads, grid rows, picker rows, `/new` and save responses:

| Value | JSON |
|---|---|
| integer | number (`220`) |
| `number`, `money`, any decimal | **string**, canonical (`"840000.0000"`, exactly as the database returns, no rounding at the API) |
| date | `"2026-10-27"` |
| datetime | `"2026-10-27T14:05:00"` (no time zone) |
| boolean (bit) | `true` / `false` |
| null | `null` |

- The meta's `scale` is for display only.
- For columns not in the meta (extra result columns), choose by Python type: `Decimal` to string, `int` to number, `date`/`datetime` as above, `bytes` to `null` with a warning.
- **Requests** accept numbers or numeric strings for decimal fields; reject `NaN`, `Infinity` and anything else with `422 validation_failed` (`type_mismatch`).
- A save response is built by **re-reading the record** with the normal read path, so it uses the same serializer.

**Acceptance:** the same record read after a save and through the read endpoint is byte-identical; a decimal sent as `840000` and as `"840000"` stores the same value.

## P1.5 Resolve filter defaults on the server

In the sample, `filters[].default` is `"DATEADD(-360,TODAY())"` and `"EDOM(NOW())"`. `docs/04` says the API resolves them.

- Evaluate each default with the helper library and return an ISO date (`"2025-11-03"`) or datetime for datetime filters.
- Add **`NOW()`** (current date and time) to the helper library. For a date-typed filter, coerce the result to a date.
- Business time zone: define one constant in `shared/expr` (`ERP_TIMEZONE`). The data suggests Indonesia (IDR currency, Indonesian customer names), so use `"Asia/Jakarta"` and confirm it.
- If evaluation fails, return `default: null` and add `defaultExpression` with the raw text, and log a config warning with the `hdrId`.

**Acceptance:** fixtures with a frozen clock check `DATEADD(-360,TODAY())`, `EDOM(NOW())`, `FDOM(TODAY())`; a broken expression yields `null` plus `defaultExpression`.

## P1.6 Smaller contract cleanups

- **`/new` and meta defaults.** `/new` must resolve defaults for **all** updatable fields, including hidden ones, and return **every embedded grid key with empty rows** (`"grids": { "132": { "rows": [] } }`), matching the save and read responses. Remove `defaults` from form meta so there is one source of truth.
- **Record id.** Mark the `idField` in form meta with `"isId": true` and `"hidden": true` (the sample shows `doc_id` as a visible text field).
- **Rows.** Omit `total` unless `includeTotal=true` was requested.
- **Docs.** Fix `final_be.md`: the menu is `{ "count", "items": [...] }`, and a save returns the saved record (`header`, `grids`, `schemaVersion`), not `{success, recordId}`.

**Acceptance:** snapshot tests for `/new` and form meta; a request without `includeTotal` has no `total` key.

---

# P2: performance (measure first)

Most time is probably spent in SQL Server, not in Python. Do P2.1 before anything else in P2, and keep only changes that measurably help.

## P2.1 Timing and metrics

- `app/core/timing.py`: a context manager `timed_query(kind, hdr_id)` used by every repository that runs config SQL (browser rows, form read, grid rows, picker rows, options, commands, saves). It logs duration and row count, and logs a **WARNING above 1000 ms** (constant).
- Request middleware (additive in `main.py`): log duration per request (`docs/11` format) and send a **`Server-Timing`** header (`db;dur=<ms>, total;dur=<ms>`; no other information).
- `app/core/metrics.py`: in-memory counters and a ring buffer of the last 1,000 requests: cache hits and misses, slow-query count, status counts, and per route (template) p50 and p95.
- **New** `GET /v1/admin/metrics` (same admin gate as `/v1/admin/lint`) returns those numbers plus **read-only** pool status (`engine.pool.status()`), without touching `db.py`.
- At debug level, log the final wrapped SQL text with its `hdrId` (never bound values), so slow queries can be taken to SQL Server.

**Acceptance:** a request produces a log line and a `Server-Timing` header; `/v1/admin/metrics` shows p95 per route after some traffic and requires the admin role.

## P2.2 In-process caches (`app/core/cache.py`)

One small thread-safe TTL cache class (bounded size, **single-flight**: only one thread computes a missing key while others wait, so a cold start does not stampede the database). Register every cache in a registry so `POST /v1/admin/cache/refresh` clears them all.

| Cache | Key | TTL |
|---|---|---|
| Screen config objects (normalized, with `schemaVersion`) | `hdrId` | `getattr(settings, "CONFIG_CACHE_TTL_SEC", 60)` |
| Reverse index (form to opening browsers), `code` to `hdrId` map | one entry | same |
| Menu, unfiltered | one entry | same |
| Catalog (`sys.columns`) | table name | 600 s |
| Result-column probe (`SELECT TOP 0 ...`) | `hdrId` + `schemaVersion` | 600 s |

Per-user results (menu after role filtering, meta flags) are **computed per request** from the cached objects and are cheap. Each worker process has its own caches, so the refresh endpoint only clears the worker that receives it. Document this limit, and prefer short TTLs over relying on refresh.

**Acceptance:** two identical meta requests cause one config query (assert with a query counter); concurrent cold requests cause one load; refresh empties every registered cache.

## P2.3 HTTP caching for meta and menu

For `GET /v1/meta/*` and `GET /v1/menu`:

- `ETag: W/"<schemaVersion>-<rolesHash>"`, where `rolesHash` is the first 8 hex characters of a SHA-1 over the user's sorted, lowercase role names (meta contains role-dependent flags such as `canAdd` and `commands`). For the menu use a version of the menu cache plus `rolesHash`.
- `Cache-Control: private, max-age=0, must-revalidate` and `Vary: Authorization`.
- On `If-None-Match` equal to the ETag, return **`304`** with an empty body. This check happens **after** authentication and the Visible check, and is computed from `schemaVersion` **before** the response body is built.

**Acceptance:** second request with `If-None-Match` returns 304 and runs no config SQL; a different role set gets a different ETag; a config change gives a new ETag.

## P2.4 Compression and serialization

- Add `GZipMiddleware(minimum_size=1024)` (skip it if the reverse proxy already compresses).
- **Benchmark before switching to `ORJSONResponse`.** FastAPI with Pydantic v2 already serializes quickly when `response_model` is used. Try orjson only on the endpoints that return raw row dictionaries (browser rows, grid rows, picker rows). Keep it only if a 50-row and a 500-row response get at least 20% faster in the benchmark. Add `orjson` to `pyproject.toml` only if kept. Decimals are already strings after P1.4, so no custom hook is needed.

**Acceptance:** `Content-Encoding: gzip` on large responses; the benchmark result is recorded in the PR description.

## P2.5 SQL-side review (report, do not "fix" in code)

1. **Multi-statement functions.** Add a **linter check**: parse the function or table name from `FROM [Schema].[Name] (` in a browser expression, look it up in `sys.objects`, and warn when `type = 'TF'` (multi-statement table-valued function). SQL Server estimates these poorly, and the wrapper's `ORDER BY` runs on top. Converting them to inline functions (`IF`) is an owner decision on the database side.
2. **Sort cost.** Keyset paging still sorts the filtered range for each page. Cost scales with the rows in the date range, not with `pageSize`. Report to the owner that browser defaults such as `DATEADD(-360,TODAY())` mean a year of data per page; narrower default ranges are a config change in the variables.
3. **Slow screen report.** After a day of traffic, take the top five by p95 from `/v1/admin/metrics`, capture their logged SQL, and run them in SQL Server Management Studio with `SET STATISTICS IO, TIME ON` and the actual execution plan. Write findings (missing indexes, scans, estimates) in `docs/12-findings.md`.
4. `includeTotal` stays off by default; row caps and query timeout stay on (`docs/11`).

## P2.6 Connection pool (recommendation only)

`app/core/db.py` is off limits for this change. Pool settings need the owner's decision. Provide the data: pool status and wait times from `/v1/admin/metrics`, and this guidance:

- Each worker has its own pool. SQLAlchemy defaults allow 5 + 10 overflow connections per process.
- Synchronous endpoints run in a thread pool (about 40 threads by default), so concurrent requests can exceed the connection pool. Symptoms are `QueuePool limit` errors or long waits for a connection.
- Keep `pool_pre_ping` and `pool_recycle`. Size the pool to peak concurrency per worker and stay under the SQL Server connection limit across all workers and both logins.

## P2.7 Optional: form bundle

Only if measurements show round-trip latency matters on mobile: `GET /v1/forms/{hdrId}/bundle?recordId=` returning form meta plus the record (or the `new` record) in one response. Bundles do not cache as well as meta alone, so prefer HTTP/2 and the ETags above first.

---

# P3: observability and load tests

- **Nightly lint:** run `GET /v1/admin/lint` from cron or a scheduler outside the app, log the report, and alert on new errors. Do not add a scheduler to the API process.
- **Load test** `loadtest/takeorder.js` (k6, or Locust). Run it against **staging only**, with writes on only there. Flow: login, menu, meta browser, rows (3 pages), meta form, read record, create, update. Budgets (p95, tune after the first run):

| Call | Budget |
|---|---|
| Meta with matching ETag (304) | under 50 ms |
| Meta, cache warm, 200 | under 150 ms |
| Browser rows, 50 rows | under 500 ms |
| Form read with grid | under 400 ms |
| Create or update with 10 grid rows | under 800 ms |

- Record results in `docs/12-findings.md` so regressions are visible.

---

## Owner decisions needed

| # | Decision | Default until decided |
|---|---|---|
| D1 | Approve a durable idempotency table (schema addition) | In-process store, single worker only |
| D2 | Confirm the create/delete permission rule (referencing browser's Add/Remove list) | As in P0.1; deny when no browser references the form |
| D3 | Confirm readonly handling (ignore client values except formulas) after the Profiler trace | As in P0.2 |
| D4 | Business time zone | `Asia/Jakarta` |
| D5 | Pool sizing in `db.py` and worker count | Unchanged |
| D6 | Convert multi-statement table-valued functions to inline ones | Report only |

## After implementing

Update `docs/05-api-contract.md` (grid meta, variables, number serialization, filter defaults, `/new`), `docs/06-crud-engine.md` (readonly rule, create permission), `final_be.md`, and re-share real request and response samples with the front-end team, including a form read with grid rows, a save with grid rows, picker rows, field options, a command run, and a 409 or 422 error.