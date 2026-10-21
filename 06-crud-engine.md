# 06. Generic CRUD engine

The engine builds every read, save and delete from three sources and contains no per-form code:

1. **Config** (`Form.Headers`, `Form.Details`, `Form.Grids`, `Form.Variables`): fields, flags, keys, base tables.
2. **SQL Server catalog** (`sys.columns`): real column names, types, lengths, nullability, identity and computed flags, defaults.
3. **The request**: only values for fields the config allows.

> **Verify first.** The save mechanism (generic INSERT/UPDATE on `hdr_basetable`) is **[likely]**, not proven. The old PHP's queries, document numbering and delete behavior are unseen. Capture a SQL Profiler or Extended Events trace of the old app saving, editing and deleting a Take Order and a Sales Order, and compare the engine's SQL with it before trusting writes. Develop against a **staging copy**, never production.

## Executing SQL

The database layer is synchronous SQLAlchemy 2.0 over `pyodbc` (`docs/09`), used as a **connection pool and transaction manager only**. There are no ORM models.

- Config SQL (browser rows, form and grid reads, combo queries, commands) runs with `db.connection().exec_driver_sql(sql, tuple(params))`, where `sql` has `?` markers and `params` is the ordered list from `shared/params.py`. Do not use `text()` for it.
- Fixed repository SQL and catalog queries may use `text()` with named binds.
- Reads use `get_db`. Saves, deletes and writing commands use `get_db_write`.
- Grid rows may be inserted with `executemany` (`fast_executemany` is on) **only when generated ids are not needed**, because the record is re-read after the save. Insert the **header** with a single execute and the `OUTPUT ... INTO` pattern below.
- One `db.commit()` at the end of a successful save. On any exception, `db.rollback()` and re-raise.
- Set the query timeout (`QUERY_TIMEOUT_SEC`) on the raw DBAPI connection for each request.

## Catalog reader (`app/shared/catalog.py`)

```sql
SELECT c.name,
       t.name AS type_name,
       c.max_length, c.precision, c.scale,
       c.is_nullable, c.is_identity, c.is_computed,
       OBJECT_DEFINITION(c.default_object_id) AS default_definition
FROM sys.columns c
JOIN sys.types t ON t.user_type_id = c.user_type_id
WHERE c.object_id = OBJECT_ID(?);
```

Pass the base table as written in config (for example `Sales.[Order.Header]`). Cache per table with `CONFIG_CACHE_TTL_SEC`. Insertable columns exclude identity, computed, `timestamp`/`rowversion`.

**Identifier safety.** A column or table name goes into SQL text only if it exists in the catalog result (or the config table list) and is then written as `[name]` with `]` doubled. Anything else is rejected.

## Allowed field set

For a form (and likewise for a grid), a field is writable when **all** are true:

- `col_update` is true
- `col_name` is set and `col_uitype` is not a layout type (`grid`, `hr`, `label`, `button`, `import`, `listener`)
- the column exists in the base table catalog and is insertable
- (for update) it is not the record id

Everything else in a payload is rejected with `validation_failed` listing the offending keys.

## Read

**Header:**

```sql
SELECT * FROM ( <hdr_expr with ::Params:: bound> ) AS x WHERE x.[<id field>] = ?
```

where `<id field>` is the `col_PK = 1` field. A bare-name `hdr_expr` becomes `SELECT * FROM <name>`.

**Each grid** (every field with `col_uitype = 'grid'`):

```sql
SELECT * FROM ( <grid hdr_expr> ) AS x WHERE x.[<parent field>] = ? ORDER BY x.[<row number or row id>]
```

where `<parent field>` is the grid column with `col_key = 2`. If the grid expression already uses `::DocID::` or similar, bind it through the param engine and skip the extra filter.

**Wrapper caveats** (not verified against the old app): T-SQL does not allow `ORDER BY` inside a derived table without `TOP`, and a derived table cannot have duplicate column names. The loader detects both, the linter reports them, and the engine falls back to `SELECT * FROM (expr)` with a trailing `ORDER BY` stripped.

**New record** (`/new`): empty header with resolved defaults (`docs/04`), empty grids.

## Create (POST)

All in **one transaction** with `SET XACT_ABORT ON`:

1. **Check schemaVersion** equals the current one, else 409 `schema_stale`.
2. **Check roles** (form Visible, and add permission).
3. **Validate the header** against the allowed field set and catalog:
   - Types: integer, decimal (round to `col_scale`), date (`yyyy-mm-dd`), datetime, bit (from boolean), text (check `max_length`; `nvarchar` byte length is chars times 2).
   - NOT NULL columns without a default and not identity must be present (use `col_defaultvalue` to fill gaps).
4. **Insert the header**, getting the new key. Use a table variable so it works on tables with triggers (`OUTPUT` without `INTO` fails if the table has enabled triggers):

   ```sql
   DECLARE @o TABLE (id BIGINT);
   INSERT INTO <base table> ([c1],[c2],...)
   OUTPUT INSERTED.[<pk>] INTO @o
   VALUES (?,?,...);
   SELECT id FROM @o;
   ```

5. **Grids** (only those with the form's grid field `col_update` true and a base table):
   - Set the parent field (`col_key = 2`) to the new header id on every row.
   - Fill the row number field (`col_key = 3`) 1..n if missing.
   - Insert rows with the same `OUTPUT ... INTO` pattern.
6. **Commit**, then read the record back with the **read** path and return it.

On any error: roll back and map it (see Errors below).

## Update (PUT)

Same checks, then:

- **Header:** `UPDATE <base> SET [c1]=?, ... WHERE [<pk>] = ?`. Require 1 row affected, else 404.
- **Grid rows:**
  - A row with an id: `UPDATE ... WHERE [<row id>] = ? AND [<parent>] = ?`. Require 1 row affected. **Always include the parent in the WHERE** so one document cannot modify another document's lines.
  - A row without an id: insert (parent and row number set as in create).
  - Ids in `deleted`: `DELETE ... WHERE [<row id>] IN (...) AND [<parent>] = ?`.
- Row add, row delete and structural changes require the grid header `hdr_addremove = 1`. For `hdr_addremove = 0` reject any grid write.
- **Concurrency:** if the base table has a `rowversion` column, send it back and use it in the WHERE (409 `conflict` on mismatch). Otherwise last write wins **[unknown whether the old app checks]**.

## Edit lock and row locks

Taken from the old project's order rules (`docs/09`) and generalized:

1. Update and delete first read the record **under row locks**, inside the transaction: `SELECT ... FROM <base table> WITH (UPDLOCK, ROWLOCK) WHERE [<pk>] = ?`. Two requests cannot race.
2. If the base table has the column named by `EDIT_LOCK_FIELD` (default `docflow_seq`), the record may be changed or deleted **only when it equals `EDIT_LOCK_VALUE`** (default `0`). Otherwise reject with 409 `conflict` ("document already in flow"). This is **[likely]**: the old project applies it to Take Order, but it is not verified for other documents, so keep the field and value configurable.
3. Grid rows are written only after the header lock is held.

## Delete

The old project deletes an order's header and detail rows **in one transaction**, under the edit lock above **[likely]**. The ERP's own delete behavior (hard delete, soft delete, a flow state, or a procedure) is still **[unknown]** until the Profiler trace is checked.

Default: **disabled** (`ENABLE_DELETE=false`, returns `501 not_implemented`). When enabled: take the row lock, check the edit lock, delete the saved grids' rows by parent id, then the header, in one transaction. Do not enable it in production before comparing with the old app's trace.

## Flow state and document numbers

`docflow_seq` and `doc_no` (prefix `doc_header`, for example `STO`) are probably produced by triggers, defaults or procedures **[unknown]**. The engine writes only what the config allows and returns what the database produced. Do not generate document numbers in Python. The old project's order service treats `docflow_seq == 0` as "still editable" (see Edit lock). How `doc_no` and the initial `docflow_seq` are set on create is unknown until the old `orders/service.py` is reviewed (`docs/08` Q1).

## Errors from the database

| SQL situation | API result |
|---|---|
| `THROW`/`RAISERROR` text raised on purpose (user-defined error numbers 50000+) | 409 or 422 with that message |
| Unique, foreign key or check constraint violation | 409 `conflict` with a generic message; log details |
| Deadlock (1205) | Retry the transaction once, then 409 |
| Timeout | 504 `query_timeout` |
| Anything else | 500 `internal_error`; log SQL error number and text with the request id |

## schemaVersion

A short hash identifying the config a screen was built from:

```
schemaVersion = first 8 hex chars of sha1(canonical JSON of:
   the header row,
   its child rows sorted by their order column and id,
   and for a form, the same for each embedded grid)
```

- Sent in every meta response and every form read.
- Required on save. A mismatch returns **409 `schema_stale`** so the app reloads the meta, and users never write against a form that changed under them.
- Config is cached with a short TTL, and `POST /v1/admin/cache/refresh` drops it (the portal could call this after a config save).

## Config linter (`GET /v1/admin/lint`)

Run on demand and nightly. For every screen it checks:

| Check | Level |
|---|---|
| Base table exists in the catalog | error |
| Every `col_update` field exists in the base table and is insertable | error |
| A form has exactly one `col_PK = 1` field | error |
| A grid has a parent column (`col_key = 2`) and a row id column (`col_key = 1`), both in its table | error |
| Picker, grid, form and `dtl_code` references resolve | error |
| NOT NULL columns without default are covered by an Update field | warning |
| Placeholders resolve to a variable, a session name or a field | warning |
| Placeholders are not inside string literals | error |
| Query can be wrapped (no stray `ORDER BY`, no duplicate column names) | warning |
| Formula and default functions are all in the helper library | warning |
| Role lists parse and contain known role names (for example `Acc_Mgr` is not a known name) | warning |
| Duplicate column names within a screen | warning |

The report lists `{ code, level, check, detail }`. Most portal mistakes then show up here instead of as a failed save.

## Tests

Per rule, one fixture under `tests/fixtures/crud/`:

```json
{
  "name": "create form with one grid",
  "config": { "header": {...}, "details": [...], "grids": {...}, "catalog": {...} },
  "input":  { "header": {...}, "grids": {...} },
  "expect": { "sql": ["INSERT INTO ..."], "params": [[...]], "response": {...} }
}
```

Also add cases for: unknown field rejected, identity column excluded, parent id forced on grid rows, stale schemaVersion, `hdr_addremove = 0` grid rejecting writes, rollback on a failing grid row.
