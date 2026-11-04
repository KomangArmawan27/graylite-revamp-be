# 11. Pagination and error handling

**Status:** change request. Where this file differs from `docs/05-api-contract.md` or `docs/06-crud-engine.md`, **this file wins**. It builds on `docs/10-endpoint-changes.md` (endpoints are addressed by `hdr_id`).

## Scope

This change covers **list paging** and **error handling** only.

**Do not touch** (already done and working): `app/core/config.py` and `.env` handling, `app/core/db.py`, authentication and authorization (`app/core/security.py`, `app/core/deps.py`, `app/modules/auth/*`, the role matcher), and `app/modules/health/*`.

**Allowed edits:**

- `app/core/pagination.py` and `app/core/errors.py`: **extend them**. Read both first. Keep every existing public function, class and signature working, because the legacy `orders` module and the old tests use them. Add new functions beside the old ones.
- `app/main.py`: additive lines only (register exception handlers and the request-id middleware).
- Page-size limits and similar numbers are **constants in `app/core/pagination.py`**, not new settings.

---

# Part A: Pagination

## Response shape

Every paged endpoint returns the same shape (a generic `Page` model in `app/core/pagination.py`):

```json
{
  "items": [ { "doc_id": 900101, "doc_no": "STO26100001" } ],
  "pageSize": 50,
  "hasMore": true,
  "nextCursor": "eyJ2IjoxLCJtIjoia2V5c2V0Ii..."
}
```

- `nextCursor` is `null` when `hasMore` is false.
- `total` is **not** returned by default (counting arbitrary config SQL is expensive). `?includeTotal=true` adds `total` from a separate `SELECT COUNT(*) FROM (<expr>) x`, under the normal query timeout. Use it sparingly.
- Request parameters: `pageSize`, `cursor`, `q`, `sort`, plus the screen's filters.

## Which endpoints page

| Endpoint | Paging | Default order | pageSize default / max |
|---|---|---|---|
| `GET /v1/browsers/{hdrId}/rows` | keyset | date column (`col_key = 4`) DESC, then row key (`col_key = 1`) DESC | 50 / 200 |
| `GET /v1/pickers/{hdrId}/rows` | keyset | first visible column ASC, then key ASC | 30 / 100 |
| `GET /v1/grids/{hdrId}/rows` (standalone) | keyset | row number (`col_key = 3`) ASC, then row id (`col_key = 1`) ASC | 100 / 500 |
| Grid rows inside a form read | **none**: all rows, hard cap 2000 | row number, then row id | n/a |
| `GET /v1/forms/{hdrId}/fields/{name}/options` | **none**, cap 500 | as the query returns | n/a |
| `GET /v1/menu` | none | `docs/10` | n/a |

Exceeding a hard cap returns `422 result_too_large`. Never silently truncate.

A `pageSize` above the maximum is **clamped**, below 1 is a `422 validation_failed`.

## Keyset paging over config SQL

Config SQL is arbitrary, so it is wrapped as a derived table (see the wrapper caveats in `docs/06`):

```sql
SELECT TOP (?) *
FROM ( <hdr_expr with ::Params:: bound> ) AS x
WHERE <keyset predicate>         -- only when a cursor is present
  AND <search predicate>         -- only when q is present
ORDER BY x.[doc_date] DESC, x.[doc_id] DESC
```

Rules:

1. **Fetch `pageSize + 1` rows** (`TOP (?)` bound as an integer). If the extra row exists, `hasMore` is true and it is dropped from `items`.
2. **A deterministic order needs a unique last key.** Sort keys are the requested sort columns (at most 2) **plus the row key as the final tie-breaker**. If the screen has no row key (`col_key = 1` missing), fall back to **offset paging** (see below).
3. **Identifiers come from config, never from the cursor or the request.** A sort column must be one of the screen's known columns (configured columns, or the result columns found by a cached `SELECT TOP 0 * FROM (<expr>) x` probe). Quote as `[name]`. Anything else is `422 invalid_sort`.
4. **Values are always bound parameters** (`?`).
5. **The sort and row-key columns must appear in the result.** `SELECT *` normally guarantees this; if one is missing, use offset paging.

### Sort parameter

`sort=doc_date:desc,doc_no:asc` (direction optional, default `asc`). At most 2 columns; the row key is appended automatically. Without `sort`, use the default order in the table above.

### Keyset predicate

For sort keys `c1 .. cn` with the last returned row's values `v1 .. vn`, the next page's predicate is:

```
after(c1) OR (eq(c1) AND after(c2)) OR (eq(c1) AND eq(c2) AND after(c3)) ...
```

SQL Server sorts `NULL` as the lowest value (first in `ASC`, last in `DESC`). Because the last row's values are known when the query is built, choose the form at build time:

| Direction | Last value | `after(c)` | `eq(c)` |
|---|---|---|---|
| DESC | not null | `(x.[c] < ? OR x.[c] IS NULL)` | `x.[c] = ?` |
| DESC | null | *(nothing sorts after it: drop this term)* | `x.[c] IS NULL` |
| ASC | not null | `x.[c] > ?` | `x.[c] = ?` |
| ASC | null | `x.[c] IS NOT NULL` | `x.[c] IS NULL` |

Example (default browser order, last row `doc_date = 2026-10-20`, `doc_id = 900101`):

```sql
WHERE ( x.[doc_date] < ? OR x.[doc_date] IS NULL
        OR (x.[doc_date] = ? AND x.[doc_id] < ?) )
```

The row key is never null. Write this as one function (`build_keyset_predicate`) with fixtures for every row of the table.

### Cursor

An **opaque, URL-safe base64 JSON** string, at most 1 KB, containing only: version, mode (`keyset` or `offset`), the last row's sort values, and a **fingerprint**.

```json
{ "v": 1, "m": "keyset", "last": ["2026-10-20", 900101], "fp": "9b1c4e07" }
```

- **Fingerprint:** a short hash of `hdrId`, the effective sort, the filter values, `q`, and the screen's `schemaVersion`. If the fingerprint of the request differs from the cursor's, return `400 invalid_cursor` ("The list changed, restart from the first page"). This prevents mixing a cursor with different filters.
- **Never trust the cursor for SQL.** It carries values only. Column names come from config. Convert each value with the column's normalized type (date, integer, decimal, text); a value that does not convert is `400 invalid_cursor`. No signing is needed because nothing in it reaches SQL text.
- Malformed, oversized or unknown-version cursors are `400 invalid_cursor`.

### Offset fallback

Used only when keyset is impossible (no row key, or sort columns missing from the result). Cursor mode `offset`, containing the next offset. Query:

```sql
SELECT * FROM ( <expr> ) AS x
ORDER BY x.[<first column>] OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
```

It is slower for deep pages and can repeat or skip rows when data changes between requests. Log a warning with the `hdrId` so the linter can report screens without a row key.

### Search (`q`)

- Optional. Applies to the screen's **visible text columns**, at most 8, as `x.[col] LIKE ? ESCAPE '\'` joined with `OR`, with the value `%` + escaped `q` + `%` bound as a parameter. Escape `\`, `%`, `_` and `[` in `q`.
- A screen with no text columns ignores `q`.
- Limit `q` to 100 characters (`422 validation_failed` above that).
- `q` is part of the fingerprint.

### Filters and paging

Filter variables (`ADate`, `BDate`, ...) are bound **inside** the derived table through the param engine; the outer `WHERE` only holds keyset and search predicates. A missing required filter is `422 invalid_filter` before any SQL runs.

### Consistency

Keyset paging is stable while rows are inserted. If rows change between requests, a row may appear on neither or on both pages; that is accepted. The app reloads from the first page on pull-to-refresh.

## Module layout

Extend `app/core/pagination.py` with:

- `Page` (generic Pydantic model), `DEFAULT_PAGE_SIZE`, `MAX_PAGE_SIZE` and per-endpoint limits as constants
- `encode_cursor`, `decode_cursor`, `make_fingerprint`
- `resolve_sort(known_columns, sort_param, default, row_key)`
- `build_keyset_predicate(sort, last_values)` returning SQL and parameters
- `build_page_query(base_sql, base_params, sort, cursor, page_size, search)` returning final SQL and parameters
- `finish_page(rows, page_size, sort)` returning `Page` data (drops the extra row, makes `nextCursor`)

Repositories call these; routers never build SQL. Keep the existing functions used by the legacy orders module as they are.

---

# Part B: Error handling

## Envelope

All `/v1/*` errors use one envelope:

```json
{
  "error": {
    "code": "validation_failed",
    "message": "Invalid payload",
    "requestId": "c1f2a9e07b3d4e55",
    "details": [
      { "path": "grids.1425.rows[2].trans_qty", "field": "trans_qty", "code": "type_mismatch", "problem": "must be a number" }
    ]
  }
}
```

- `code` is stable and is what the app switches on. `message` is for people and may change.
- `details` is optional (an array; may be empty or absent).
- Check what the existing handlers in `app/core/errors.py` return. If they already produce this shape, keep them. If not, produce this envelope for paths starting `/v1`, and leave the format of legacy routes unchanged (decide by path prefix).
- Messages are English. The app localizes by `code`.

## Request id

- Middleware: accept an inbound `X-Request-Id` only if it matches `^[A-Za-z0-9_-]{8,64}$`, otherwise generate one (UUID4 without dashes). Store it in `request.state.request_id`, put it in every log line and error body, and return it as the `X-Request-Id` response header (also on errors).

## Error classes

Keep the existing `AppError` constructor. Add subclasses or factory functions so callers never build status codes by hand:

`NotFound`, `WrongScreenType`, `Forbidden`, `ValidationFailed`, `InvalidCursor`, `InvalidSort`, `InvalidFilter`, `SchemaStale`, `Conflict`, `RuleViolation`, `ResultTooLarge`, `ConfigError`, `QueryTimeout`, `DbUnavailable`, `NotImplementedYet`, `Internal`.

Each has a fixed HTTP status and `code` from the table below. Routers declare error responses through one shared `ERROR_RESPONSES` dict so the OpenAPI spec shows the envelope.

## Codes (replaces the error table in `docs/05`)

| HTTP | `code` | When |
|---|---|---|
| 400 | `bad_request` | Malformed request |
| 400 | `invalid_cursor` | Cursor malformed, changed filters, or unknown version |
| 401 | `unauthorized` | Handled by the existing auth. Do not change. |
| 403 | `forbidden` | Role not allowed (existing role matcher). Also writes while `ENABLE_WRITES` is false |
| 404 | `not_found` | Unknown screen, record, or command not on that screen |
| 404 | `wrong_screen_type` | The `hdrId` exists but is the wrong type for this endpoint |
| 405 | `method_not_allowed` | Wrong HTTP method |
| 409 | `schema_stale` | Config changed since the app loaded it |
| 409 | `conflict` | Unique, foreign key or check violation, deadlock after retry, lock timeout, edit lock (`docflow_seq`) |
| 422 | `validation_failed` | Payload or parameter failed validation |
| 422 | `invalid_sort` | Sort column not allowed |
| 422 | `invalid_filter` | Required filter missing or value invalid |
| 422 | `result_too_large` | A hard cap was exceeded |
| 422 | `rule_violation` | The database rejected the operation on purpose (custom `RAISERROR`/`THROW`, see below) |
| 500 | `config_error` | The screen's configuration is broken (bad SQL, missing object or column, unparseable expression) |
| 500 | `internal_error` | Anything unexpected |
| 501 | `not_implemented` | For example delete while `ENABLE_DELETE` is false |
| 503 | `db_unavailable` | Cannot reach or log in to the database. Add `Retry-After: 5`. |
| 504 | `query_timeout` | A config query exceeded the time limit |

## Handlers (registered in `app/main.py`)

| Source | Result |
|---|---|
| `AppError` | the envelope with its status and code |
| FastAPI/Pydantic `RequestValidationError` | `422 validation_failed`; each error becomes a `details` item with `path` (from `loc`, for example `query.pageSize`), `field` (last element), `code` and `problem` |
| Starlette `HTTPException` | map 404 to `not_found`, 405 to `method_not_allowed`, 401 and 403 pass through unchanged, others to `bad_request` |
| `sqlalchemy.exc.DBAPIError` (safety net) | `map_db_error(exc)` below |
| Any other `Exception` | `500 internal_error` with a generic message; log the traceback with the request id |

Validation `details[].code` values: `required`, `type_mismatch`, `too_long`, `out_of_range`, `unknown_field`, `not_allowed` (field is not updatable), `invalid_value`. For grid rows, `path` is `grids.<gridHdrId>.rows[<index>].<field>`.

## Mapping database errors

Add `map_db_error(exc) -> AppError` to `app/core/errors.py`.

**Always `session.rollback()` first**, then map. Extract the SQLSTATE from `exc.orig.args[0]` and the SQL Server error number from the message with a regex such as `\[SQL Server\].*?\((\d+)\)` (the number appears in parentheses). If no number is found, use the SQLSTATE.

| SQL Server situation | Result |
|---|---|
| 1205 deadlock victim | The **save engine** retries the whole transaction once (100 to 300 ms jitter). If it fails again: `409 conflict` ("Please try again"). Never retry reads or commands. |
| 1222 lock request timeout | `409 conflict` ("The record is being edited by someone else") |
| 2627, 2601 unique violation | `409 conflict`, generic message (no constraint or table name) |
| 547 foreign key or check violation | `409 conflict`, generic message |
| 515 NULL into a NOT NULL column | `422 validation_failed`, `details`: the column name parsed from the message, `code: required` |
| 8152 string truncation | `422 validation_failed`, `code: too_long` (field if it can be identified) |
| 245, 241, 242, 8114, 8115 conversion or overflow | `422 validation_failed`, `code: type_mismatch` or `out_of_range` |
| 50000 or higher, raised with `RAISERROR` or `THROW` on purpose | `422 rule_violation`; `message` is the database's text after cleaning (below) |
| 207, 208, 156, 8156, 1033, 102, 105 (bad column or object name, syntax, duplicate column, ORDER BY in a derived table) | `500 config_error`; details: `{ "hdrId": <id> }` only if known. Log the full SQL error. |
| 229, 230, 262, 300 (permission denied) | `500 internal_error`; log object name and a hint to review the grants (`docs/09`) |
| SQLSTATE `HYT00`, `HYT01`, "Query timeout expired" | `504 query_timeout` |
| SQLSTATE `08001`, `08S01`, `08003`, `28000`, errors 53, 40613, 18456 at runtime, "Communication link failure" | `503 db_unavailable` with `Retry-After: 5` |
| Anything else | `500 internal_error` |

**Cleaning database messages** (for `rule_violation` only): remove the driver prefix (`[Microsoft][ODBC Driver 18 for SQL Server][SQL Server]`) and the trailing `(50000) (SQLExecDirectW)`, collapse whitespace, cut at 300 characters. These messages are written by database developers for users, so they are shown; all other SQL errors are never shown.

**Never leak:** SQL text, bound values, server or database names, table and constraint names, stack traces. Clients see only `code`, a safe `message`, `requestId` and structured `details`.

## Config errors are expected

Because screens are driven by configuration, broken config will happen. `config_error` is a normal, loud, non-fatal outcome:

- A failure in one screen never affects others.
- The log line includes `hdrId` and the screen code so the config linter (`docs/06`) can be run for it.
- The app should show "This screen is unavailable" (no SQL detail).
- Param engine problems (placeholder inside a string literal, unresolved required variable that is a config issue, unparseable expression) also raise `config_error`; a missing **user-supplied** value is `invalid_filter`.

## Logging

One line per request: request id, user id (read `request.state.user_id` **if present**; do not depend on auth internals), method, route template, status, error `code` when present, `hdrId` when known (set by `get_screen`), duration in ms.

- 5xx: ERROR level with the traceback.
- 403: WARNING. Other 4xx: INFO.
- DB errors: also log SQLSTATE and the SQL Server error number.
- **Never log** request bodies, passwords, tokens, bound parameter values, or `Authorization` headers. For validation errors log field paths only.

## Tests and acceptance

Add fixtures under `tests/fixtures/pagination/` and `tests/fixtures/errors/` and unit tests (no database needed):

**Pagination**

1. `build_keyset_predicate` for every row of the NULL table (ASC and DESC, last value null and not null), with one, two and three keys; check SQL text and parameter order.
2. `encode_cursor` / `decode_cursor` round trip; tampered, oversized, unknown-version and wrong-type values give `invalid_cursor`; a changed filter, sort or `q` changes the fingerprint.
3. `finish_page`: exactly `pageSize` rows gives `hasMore = false`; `pageSize + 1` gives `hasMore = true` and a correct `nextCursor`.
4. `resolve_sort`: unknown column gives `invalid_sort`; the row key is always last; default order uses the date column when present.
5. `pageSize` clamped to the maximum; 0 gives `validation_failed`.
6. `q` escaping (`%`, `_`, `[`, `\`) and the 8-column limit.
7. Offset fallback when no row key.

**Errors**

8. Every row of the DB mapping table, using fake exceptions that mimic `pyodbc` messages (SQLSTATE plus `[SQL Server]... (2627)` text).
9. The envelope has `code`, `message`, `requestId` on every error; no test response contains SQL text, a table name or a bound value.
10. `rule_violation` message cleaning (prefix and suffix removed, length cut).
11. Validation details paths for query, body and grid rows (`grids.1425.rows[2].trans_qty`).
12. The request id is echoed in the header and body; a malformed inbound id is replaced.
13. The deadlock retry happens once, then returns `409`.

**Acceptance on staging:** page through `Browser.Sales.Order.Retail` (`hdrId` 1422) with `pageSize=20` and collect every row exactly once; the count matches an unpaged run. A broken test config row returns `500 config_error` without SQL text and with the request id in the log.

## After implementing

Update `docs/05-api-contract.md` (paging fields and the error table) and `docs/06-crud-engine.md` (the "Errors from the database" section now points here).