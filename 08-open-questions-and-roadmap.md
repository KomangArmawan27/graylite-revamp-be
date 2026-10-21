# 08. Open questions, safe defaults and roadmap

## Open questions

Use the **default** until the question is answered, and mark the code with `# TODO(question): <id>`.

| ID | Question | Blocks | Safe default meanwhile |
|---|---|---|---|
| Q1 | How does the old PHP save? The old FastAPI project (`orders/service.py`) already INSERTs and UPDATEs `Sales.[Order.Retail.Header]` and `Detail` directly, so direct writes are accepted by the database. How are `doc_no` and the initial `docflow_seq` set on create (defaults, triggers, or that service)? | Save engine | Generic INSERT/UPDATE on staging only; for the pilot copy the old service's behavior after reviewing it; generate no numbers otherwise |
| Q2 | How does delete work in the ERP? The old project deletes header and detail rows in one transaction when `docflow_seq = 0`. | Delete | Disabled (`ENABLE_DELETE=false`); when enabled, use the old project's rule |
| Q3 | How does the old PHP wrap form and grid queries by id? How does it page browsers? | Read, paging | Derived-table wrapper with `ORDER BY` stripped; page in the API when SQL paging is not possible |
| Q4 | Old password hash method, password expiry, token fields | Real login | Dev-only login stub behind `ENV=dev`; no production login until answered |
| Q5 | Null role list: everyone or nobody? Exact or substring matching? | Permissions | Empty means denied; exact names only |
| Q6 | Meaning of `cmd_type` 0 to 3, `cmd.cc_id`, `col_key` 3 and 7, `dtl_type` (Stand Alone), `cc_link`, `hdr_addremove` on browsers | Minor UX | Ignore them; confirm if `cmd_message` is set |
| Q7 | Is `_CCID` (user cost center) used to scope data in queries beyond the explicit `::_CCID::` uses (about 27 expressions)? | Row scoping | Bind `_CCID` from the user; add no extra filtering |
| Q8 | How does Take Order set `trans_price` from the price tier (a command like "Refresh Price", a callback, a trigger)? | Pilot form | Leave `trans_price` to the client and the database |
| Q9 | What do `MULTIDISC` and `VATPERCENT` compute exactly? | Formulas | Skip those formulas and log |
| Q10 | Menu source: `Tree.Menu` rows (`object_id`, `object_parent`, `object_command`) and how MODULE rows relate | Menu | Build the menu from Tree rows and Visible roles; hide MODULE entries |
| Q11 | What do `Security Override` and `System.[Flow.Security]` hold (probably per-flow permissions)? | Flow rules | Not enforced; note it as a gap |
| Q12 | One database or several (customers, environments)? Same config tables in each? | Deployment | One database from `.env` |
| Q13 | Should the server recompute saved formula totals, or trust the client? | Save validation | Trust the client, validate type and range |
| Q14 | Real examples of command output text beyond `REFRESHFORM`, `OPENREPORT`, `OPENREPORTNEWTAB`, `alert` | Action parser | Whitelist only the known patterns |
| Q15 | How does the old project implement idempotency for order creation (a key column such as `doc_extern`, a table, memory)? | Retry safety on mobile | Accept `Idempotency-Key` and ignore it |
| Q16 | Is the Azure VM database production or a staging copy? | All writes | Treat as production: `ENABLE_WRITES=false` |
| Q17 | Exact object names of the Grids, Variables and Commands config tables (inferred from file names) | Config loader | Use `[System].[Form.Grids]`, `[System].[Form.Variables]`, `[System].[Form.Commands]` and verify with `check_db.py` |

**Best single action to settle Q1, Q2, Q3 and part of Q8:** run SQL Profiler or an Extended Events session on the staging database while someone saves, edits and deletes a Take Order and a Sales Order in the old app. Compare the captured statements with what the engine would produce.

**Needed before the first real run:** the old project's `orders/service.py` and `models.py` (to settle Q1, Q2 and Q15), the answer to Q16, a staging copy or a SQL Server container for write tests, the DDL of the pilot tables (`Sales.[Order.Retail.Header]`, `Sales.[Order.Retail.Detail]`, `Sales.[Order.Header]`), the code of `[Sales].[Take.Order.Browser]`, and one test user per role family. Connectivity is already solved by the old project's `scripts/check_db.py`.

## Build order

Each phase ends with a milestone that can be demonstrated.

### Phase 1: Foundation

- Copy the old project's core and tooling (`app/core/config.py`, `db.py`, `errors.py`, `pagination.py`, `modules/health`, `scripts/check_db.py`, `sql/001_permissions.sql`, `pyproject.toml`, Docker files; see `docs/09`), then add the `.venv` workflow, the module folders, `/v1` routing and request id logging.
- `core/db.py`: add the write engine and `get_db_write` beside the old `engine` and `get_db`; add a query-timeout helper. Add `scripts/gen_grants.py`.
- `shared/params.py`, `shared/roles.py`, `shared/types.py`, `shared/expr/` (functions that are confirmed), `shared/catalog.py`.
- `modules/meta`: loader and normalizer for all config tables, caching, `schemaVersion`.
- `modules/admin`: config linter and cache refresh.
- Dev login stub; `GET /v1/me`.
- **Milestone:** `GET /v1/meta/browser/Browser.Sales.Order.Retail` and the linter report run against staging.

### Phase 2: Browsers and menu

- `GET /v1/meta/browser/{code}` with filters from variables (fallback: placeholder scan), column fallback from result metadata, `canAdd`/`canRemove`, layout hints.
- `GET /v1/browsers/{code}/rows` with param binding, paging, row cap and timeout.
- Menu endpoint from the Tree rows (Q10).
- **Milestone:** the Take Order list returns the same rows as the old app for the same dates and user.

### Phase 3: Forms and grids

- `GET /v1/meta/form/{code}` with tabs, widgets, variables, defaults, embedded grids.
- Form read, new record, grid rows, picker and combo options.
- Save engine (create and update) after the trace review (Q1); delete only after Q2.
- **Milestone:** create and edit a Take Order on staging; saved rows match an order created in the old app.

### Phase 4: Commands

- Command list per screen with role filtering; `POST /v1/commands/{id}/run` with whitelisted variables and action parsing.
- **Milestone:** the Take Order toolbar commands run with `::DocID::` and return actions.

### Phase 5: Real login and hardening

- Real login after Q4, RS256 tokens, refresh rotation, rate limiting, single-device rule.
- Audit log, caching policy, load test with real data volume.

### Phase 6: Expansion

- More screens by usage (clones last), master-data forms, reports, pivots, trees, imports.
- Port to PHP only if needed, using the shared fixtures.

## Test strategy

1. **Fixtures first.** `tests/fixtures/` holds JSON cases: config rows, catalog rows, inputs, and the expected SQL, bound params and response. They are language-neutral so a later PHP port can reuse them.
2. **Unit tests** for `params`, `roles`, `expr`, `types`, `layout`, action parsing and `schemaVersion`. These need no database.
3. **Contract tests** that validate every response against the generated OpenAPI schema.
4. **Integration tests** need SQL Server, because the engine uses T-SQL features (`sys.columns`, `OUTPUT ... INTO`, table locks) that SQLite does not have. Use a staging database or a SQL Server container, mark them (`pytest -m integration`) and skip them when no database is configured. Fixtures that check SQL text, params and responses need no database.
5. **Golden comparisons** for the pilot: same inputs in the old app and the API, compare rows (browser) and stored rows (save).
6. **Security tests:** a client-supplied `_USERID` is ignored; a manager-only user is denied a screen that lists only the base role; unknown payload keys are rejected; a grid row from another document cannot be updated.
7. Every bug fix adds a fixture.

## Document maintenance

When you learn something new about the config tables or the old app, update `docs/03` (with a confidence tag) and remove the matching row from the table above. Keep `docs/05` in step with the generated OpenAPI spec.
