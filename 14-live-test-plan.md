# 14. Live test plan: browser 128, form 129, grid 132

**Status:** change request and test specification. It follows `docs/12` and `docs/13`; where it differs from them, **this file wins**.

## Scope

**Do not touch** (already done and working): `app/core/config.py` and `.env` handling, `app/core/db.py`, authentication and authorization (`app/core/security.py`, `app/core/deps.py`, `app/modules/auth/*`, the role matcher), and `app/modules/health/*`.

Allowed edits are the same as in `docs/12`. New test code goes in `tests/live/`.

## Test targets

| What | `hdrId` | Code | Notes |
|---|---|---|---|
| Browser | **128** | `Browser.Sales.Order` | `detailHdrId` 129. Add/Remove list (`doc_header`) is set to **`General`** only. |
| Form | **129** | `Form.Sales.Order` | Header fields plus the embedded grid 132. Commands 252 (Print SO) and 340 (Create PL). |
| Grid | **132** | `Grid.Sales.Order.Detail` | `rowKey` `trans_id`, `parentField` `doc_id`, `rowNumberField` `trans_idx`. |
| Pickers | 131, 803 | `Picker.Sales.Customer`, `Picker.Inventory.Item.brgJadi` | Customer and item lookups. |

Do not generalize from these three screens. Every fix below must work for any screen; these are only the test data.

## Setup

### Users

| User | Roles | Purpose |
|---|---|---|
| **A** | `General` (and nothing that grants more) | Can open, add and delete on browser 128 |
| **B** | A role that can **see** screen 128 but is **not** `General` (for example `Marketing`) | Negative tests |

If there is no user B, run the negative cases as fixtures, or change `doc_header` of browser 128 temporarily on staging and restore it afterwards.

### Tokens and secrets

- **Do not paste access tokens into chat, tickets or the results file.** They expire (30 minutes) and give full access as that user.
- The live tests log in themselves with credentials from environment variables kept out of git: `TEST_BASE_URL`, `TEST_LOGIN_A`, `TEST_PASSWORD_A`, `TEST_LOGIN_B`, `TEST_PASSWORD_B`. A pre-issued token (`TEST_TOKEN_A`) is allowed for quick runs only.
- The results writer must replace the `Authorization` header with `Bearer <redacted>`.

### Environment

- **Staging database only.** `ENABLE_WRITES=true` for the write tests. `ENABLE_DELETE=true` **only** for section I.
- Tag every record the tests create with `doc_remark` starting `[API-TEST]` so they can be found and removed.
- Use read-only SQL (through the API's read login) to check the database before and after writes. Names below use the expected base tables; confirm both from `hdr_basetable` of 129 and 132 (expected `Sales.[Order.Header]` and `Sales.[Order.Detail]`).

```sql
-- header count and test records
SELECT COUNT(*) FROM Sales.[Order.Header];
SELECT doc_id, doc_no, doc_remark, docflow_seq FROM Sales.[Order.Header] WHERE doc_remark LIKE '[[]API-TEST]%';
-- grid rows of one document
SELECT * FROM Sales.[Order.Detail] WHERE doc_id = @doc_id ORDER BY trans_idx;
-- configuration of the three screens
SELECT hdr_id, hdr_code, hdr_type, hdr_level, doc_header, hdr_basetable, hdr_addremove
FROM [System].[Form.Headers] WHERE hdr_id IN (128, 129, 132);
```

### Precondition P (must pass before any write test)

For user A, `GET /v1/me` shows `roles` containing exactly `General`, and `GET /v1/meta/browser/128` returns **`canAdd: true` and `canRemove: true`**.

The last run reported `canAdd: false`. If it is still false, find out why before continuing:

1. Check the token's roles (`/v1/me`).
2. Check the database values from the SQL above: `doc_header` of 128 must be exactly `General`, and `hdr_level` must allow user A.
3. The config cache (`CONFIG_CACHE_TTL_SEC`, default 60 s): call `POST /v1/admin/cache/refresh` or wait.
4. Form 129 may be referenced by **other browsers** (`dtl_code` pointing to it). The create rule needs at least one referencing browser that is visible to the user and allows adding. List the referencing browsers (`SELECT hdr_id, hdr_code, doc_header FROM [System].[Form.Headers] WHERE LTRIM(RTRIM(dtl_code)) = 'Form.Sales.Order'`).

---

## Fix first

These come from the last test run (`docs/13`). Fix them before the live tests, because the tests assert on them.

| # | Problem (seen in the last run) | Required result |
|---|---|---|
| F1 | **Regression:** every column of browser 128 meta is `type: "text"`, `widget: "text"` (last run: `doc_id` integer, `doc_date` date, `doc_grandtotal` money) | `doc_id` integer, `doc_date` date, `doc_grandtotal` money, `doc_no`, `doc_extern`, `cust_desc`, `flow_state` text. Browser, form, grid and picker meta share one type mapping. |
| F2 | `hidden` is `""` on the `label` and `grid` fields of form 129 | `hidden` is always a boolean |
| F3 | Grid variables `WareID` and `ProposalID` appear as `aggregate: "sum"` with an empty `column` | Variables without an aggregate expression have `kind: "passed"` and no `aggregate` or `column`. Sum variables keep `aggregate` and `column`. |
| F4 | Picker meta columns are all `text` (`item_id`, `trans_price`, `class_id`) | `item_id`, `class_id` integer; `trans_price` number (scale from config) |
| F5 | Menu captions still contain `<br/>` (hdr 480, 629, 511), duplicate captions, `.OFA` clone | One `clean_caption()` (strip tags, collapse whitespace) for menu, meta and command names |
| F6 | Embedded grid (inside form meta) and standalone grid meta differ in `caption` | Same builder; the embedded copy may take the form field's caption ("Sales Item"). The equality test ignores `caption`. |
| F7 | Grid 132 `trans_total` is a plain `number` (`update: false`, `readonly: false`). In another grid it was a formula. | Check its config row (`col_uitype`, `col_controlexpr`). If it is a formula, return `widget: "formula"` with `expression`. If it is a number computed by the database, mark it `readonly: true`. |
| F8 | `/new` returns only `doc_date` and `cust_id`; the hidden updatable field `cc_id` is missing | If the config has a default for `cc_id` (for example `_CCID`), `/new` resolves it. Otherwise document that it has none. |
| F9 | The 403 message "Access denied (role or missing browser)" cannot be told apart | Add `details[0].code`: `role_not_allowed`, `no_referencing_browser`, or `writes_disabled` (no other information) |
| F10 | `DELETE` success response is not specified | `200` with `{ "recordId": <id>, "deleted": true }` |

---

## Test cases

Record every call (section "Recording results"). IDs are stable so results can be compared between runs. "A" and "B" are the users above.

### A. Session

| ID | Call | Expect |
|---|---|---|
| A1 | `GET /v1/me` as A | 200; `roles` is `["General"]`; `ccId` set |
| A2 | `POST /v1/auth/refresh`, then `POST /v1/auth/logout`, then `GET /v1/me` with the old access token | refresh 200; after logout the old token is rejected (401) |

### B. Browser 128

| ID | Call | Expect |
|---|---|---|
| B1 | `GET /v1/meta/browser/128` as A | 200. After F1: typed columns as above. `rowKey` `doc_id`, `dateColumn` `doc_date`, `detailHdrId` 129, **`canAdd` true, `canRemove` true**. `filters` have ISO `default` values (`ADate` = today minus 360 days, `BDate` = end of this month). `layout` title `doc_no`, date `doc_date`. |
| B2 | `GET /v1/meta/browser/128` as B | 200; `canAdd` false, `canRemove` false; the `ETag` differs from A's |
| B3 | `GET /v1/browsers/128/rows?ADate=2025-01-01&BDate=2026-12-31&pageSize=1` as A | 200; one item; `hasMore` true; `nextCursor` set; **no `total` key** |
| B4 | The same with `&cursor=<nextCursor>` | 200; a different row; collecting all pages gives every row exactly once (compare with an unpaged run) |
| B5 | B3's cursor with `ADate=2025-06-01` | 400 `invalid_cursor` |
| B6 | Rows without `ADate` | 422 `invalid_filter`; `details[0].field` is `ADate`, `code` `required` |
| B7 | `&sort=nope:asc` | 422 `invalid_sort` |
| B8 | `&sort=doc_date:asc,doc_no:desc` | 200; ordered accordingly; the row key is the final tie-breaker |
| B9 | `&q=ABDUL` | 200; only matching rows (customer "ABDUL ROCHIM - Lamongan") |
| B10 | Decimals in rows | integers are JSON numbers; decimals are strings with no exponent (`"0.00000000000000000"`); dates ISO; `flow_state` is untouched HTML |
| B11 | `GET /v1/browsers/129/rows?...` (a form id) | 404 `wrong_screen_type` |
| B12 | `GET /v1/browsers/999999/rows?...` | 404 `not_found` |
| B13 | `GET /v1/browsers/abc/rows` | 422 `validation_failed` |

### C. Form 129 meta and `/new`

| ID | Call | Expect |
|---|---|---|
| C1 | `GET /v1/meta/form/129` as A | 200. `idField` `doc_id` with `isId: true`, `hidden: true`. `hidden` is a boolean everywhere (F2). No `defaults` key. The label field carries `text`. `variables`: `docQty` and `docTotal` are `kind: "aggregate"` with `gridHdrId` 132 and `sum`, `DocID` and `CustID` are `kind: "field"`. |
| C2 | Embedded `grids["132"]` against `GET /v1/meta/grid/132` | Deep-equal except `caption`; columns typed (`trans_qty` number scale 2, `trans_idx` integer, `trans_id` integer); `parentField` `doc_id`, `rowNumberField` `trans_idx`, `canAddRemove` true |
| C3 | `GET /v1/forms/129/new` as A | 200; `header` has `doc_date` = today and `cust_id`, plus `cc_id` if configured (F8); `grids` is `{"132": {"rows": []}}`; same `schemaVersion` as C1 |
| C4 | `GET /v1/meta/form/128` | 404 `wrong_screen_type` |

### D. Pickers and options

| ID | Call | Expect |
|---|---|---|
| D1 | `GET /v1/pickers/131/rows?q=ABDUL&pageSize=5` | 200; rows have `cust_id`, `cust_no`, `cust_desc` (or the picker's columns), paged with the standard shape |
| D2 | `GET /v1/pickers/803/rows?q=<part of an item code>&pageSize=5` | 200; rows include `item_id`, `item_no`, `item_desc`, `item_unit`, `trans_price` |
| D3 | `GET /v1/forms/129/fields/<a combo field>/options` | 200 with options, if form 129 has a combo field; otherwise record "no combo field" |
| D4 | `GET /v1/pickers/128/rows` (a browser id) | 404 `wrong_screen_type` |

Use one customer from D1 and one item from D2 for the create test.

### E. Create (user A, writes on, staging)

Payload (values from D1 and D2; tag the remark):

```json
{
  "schemaVersion": "<from C1>",
  "header": {
    "doc_no": "HACK-1",
    "doc_date": "2026-10-30",
    "cust_id": 1789,
    "cc_id": 1,
    "doc_qty": "10",
    "doc_total": "550000",
    "doc_remark": "[API-TEST] create 1"
  },
  "grids": {
    "132": { "rows": [
      { "item_id": 1234, "trans_qty": "10", "trans_price": "55000", "trans_discvalue": 0, "trans_remark": "t1" }
    ] }
  }
}
```

| ID | Call | Expect |
|---|---|---|
| E1 | `POST /v1/forms/129/records` with header `Idempotency-Key: e1-<random>` as A | 200. **`doc_id` is new (greater than 222, not an existing id).** The response is the **full re-read record**: all header columns (`doc_id`, `doctype_id`, `docflow_seq` 0, `doc_grandtotal`, ...), not just `doc_id` and `doc_no`. **`doc_no` is not `HACK-1`** (readonly input ignored; record the value the database assigned, probably `""`). `doc_qty` and `doc_total` are kept as sent (formula values are accepted). Grid `132` has one row with a new `trans_id`, `doc_id` equal to the new header id, `trans_idx` 1. Header count in the database is +1, grid row count +1. |
| E2 | The same payload as **B** | 403 `forbidden`, `details[0].code` `role_not_allowed`; database unchanged |
| E3 | A create without `doc_date` | 200; `doc_date` is today's resolved default (or whatever the config says) |
| E4 | Header contains `foo: 1` | 422 `validation_failed`, `details[0].code` `unknown_field` |
| E5 | Header contains `docflow_seq: 5` (field has `update: false`) | 422, `details[0].code` `not_allowed`; nothing stored |
| E6 | `trans_qty: "abc"` in a grid row | 422 `type_mismatch`, `path` `grids.132.rows[0].trans_qty` |
| E7 | `doc_date: "31-12-2026"` | 422 `type_mismatch`, field `doc_date` |
| E8 | `schemaVersion: "deadbeef"` | 409 `schema_stale`; nothing stored |
| E9 | A grid row that carries `doc_id: 1` (someone else's id) | The stored row's `doc_id` equals the new header id (the parent is forced); no change to document 1 |
| E10 | Create with 3 rows and no `trans_idx` | rows get `trans_idx` 1, 2, 3 in order |
| E11 | Create where one grid row is invalid | the whole request fails (422) and **nothing** is stored (no header, no rows) |

### F. Read

| ID | Call | Expect |
|---|---|---|
| F1 | `GET /v1/forms/129/records/<E1 doc_id>` as A | 200; the same record as E1's response, byte for byte (same serializer) |
| F2 | `GET /v1/forms/129/records/999999` | 404 `not_found` |
| F3 | `GET /v1/forms/129/records/abc` | 422 `validation_failed` |

### G. Grid 132 (standalone)

| ID | Call | Expect |
|---|---|---|
| G1 | `GET /v1/grids/132/rows?parentId=<E1 doc_id>` | 200; the grid rows of that document only, ordered by `trans_idx` then `trans_id`; paged shape |
| G2 | `GET /v1/grids/132/rows` (no parent) | 200 or 422 with a clear message; record which, and that it does not scan everything without a limit |
| G3 | `GET /v1/grids/129/rows?parentId=1` | 404 `wrong_screen_type` |

### H. Update

| ID | Call | Expect |
|---|---|---|
| H1 | `PUT /v1/forms/129/records/<E1 id>` as A: change `doc_remark`, change row 1 `trans_qty`, add a second row | 200; full re-read record; header changed; row 1 changed; a second row exists with a new `trans_id` and `trans_idx` 2; no other rows or documents touched |
| H2 | `PUT` with `deleted: [<trans_id of row 2>]` | 200; row 2 is gone; row 1 remains |
| H3 | `PUT` a payload that contains `doc_id: 1` in the header | 200 but the record updated is the one in the path; `doc_id` in the body is ignored |
| H4 | Create a second document X (same as E1). `PUT` document E1 with a row whose `trans_id` belongs to X | rejected (4xx); document X is unchanged |
| H5 | `PUT` on a document whose `docflow_seq` is not 0 (take one from the browser rows, if any) | 409 `conflict` (edit lock); nothing changes. If none exists, record "no flowed document" |
| H6 | `PUT` as **B** | 200 if B may see the form (update needs Visible only), otherwise 403. Record which. |
| H7 | `PUT` with a stale `schemaVersion` | 409 `schema_stale` |

### I. Delete

| ID | Call | Expect |
|---|---|---|
| I1 | `DELETE /v1/forms/129/records/<id>` as **B** | 403 `forbidden` (`role_not_allowed`) |
| I2 | `DELETE` as A with `ENABLE_DELETE=false` | 501 `not_implemented`; record unchanged |
| I3 | `DELETE` as A with `ENABLE_DELETE=true` on a test document (`docflow_seq` 0) | 200 `{ "recordId": <id>, "deleted": true }`; header **and** its grid rows are gone from the database |
| I4 | `DELETE` the same id again | 404 `not_found` |
| I5 | `DELETE` a document with `docflow_seq` not 0 | 409 `conflict`; nothing deleted |
| I6 | `DELETE` of a test document with 3 grid rows, with the grid delete failing (simulate or use a fixture) | all or nothing: the header is not deleted without its rows |

### J. Idempotency

| ID | Call | Expect |
|---|---|---|
| J1 | E1's request again, same `Idempotency-Key`, same body | 200 with `Idempotent-Replay: true`; the same body; **no new** header or grid rows in the database |
| J2 | Same key, **different** body | 409 `conflict`, `details[0].code` `key_reused` |
| J3 | Two parallel requests, same key, same body | one 200; the other is a replay (200 with the header) or 409 `in_progress`; **one** record in the database |
| J4 | A create that fails validation (422), then the corrected body with the same key | the second request succeeds and creates one record |
| J5 | Same key used by user B | does not replay A's result (keys are scoped by user) |
| J6 | Malformed key (`abc`) | 400 `bad_request` |

### K. Commands

| ID | Call | Expect |
|---|---|---|
| K1 | `GET /v1/meta/form/129`, then compare `commands` with `Form.Commands` for `hdr_id` 129 filtered by role | Commands 252 and 340 are listed for A only if their `cmd_privilege` allows A; `confirm` text present |
| K2 | `POST /v1/screens/129/commands/252/run` with `{ "values": { "DocID": <test id> } }` as A | 200; `actions` contains only whitelisted types; `dropped` recorded. Read-only command, safe to run. |
| K3 | `POST /v1/screens/128/commands/252/run` | 404 `not_found` (the command belongs to screen 129) |
| K4 | `POST /v1/screens/129/commands/252/run` with `values` containing `_USERID: 1` | the value is ignored; the session user is used (check in the procedure's effect or the log) |
| K5 | `POST /v1/screens/129/commands/340/run` (**Create PL**) | **Writes data.** Run only on staging, on a test document, with `ENABLE_WRITES` on, after the owner agrees. Record the result; check what it created. Otherwise skip. |
| K6 | Any writing command with `ENABLE_WRITES=false` | 403, `details[0].code` `writes_disabled` |

### L. Writes switch

With `ENABLE_WRITES=false`: E1, H1, I3 and K5 all return 403 (`writes_disabled`) and the database does not change. Reads still work. Restart or reload settings between the two modes.

### M. Performance headers (P2)

| ID | Call | Expect |
|---|---|---|
| M1 | `GET /v1/meta/browser/128`, `/meta/form/129`, `/meta/grid/132`, `/meta/picker/803`, `/menu` | each has an `ETag`, `Cache-Control: private, max-age=0, must-revalidate`, `Vary: Authorization` |
| M2 | The same with `If-None-Match: <ETag>` | 304, empty body, and no config SQL (check the log or `/v1/admin/metrics` query counter) |
| M3 | Browser 128 meta for A and for B | different ETags (roles differ) |
| M4 | Every response | `Server-Timing` with `db` and `total`; `X-Request-Id` |
| M5 | `GET /v1/menu` with `Accept-Encoding: gzip` | `Content-Encoding: gzip` |
| M6 | `GET /v1/admin/metrics` as an admin | cache hit and miss counts, slow-query count, p50 and p95 per route, pool status. As A: 403. |
| M7 | Cold start timing | the first request after a restart vs the second: the second runs no config SQL |

---

## Recording results

Write one section per test ID in `test_results.md`:

```markdown
## E1 Create record (user A)
- **Request:** `POST /v1/forms/129/records`
- **Request headers:** `Authorization: Bearer <redacted>`, `Idempotency-Key: e1-...`
- **Request body:** (JSON)
- **Status:** `200`
- **Response headers:** `X-Request-Id`, `ETag`, `Server-Timing`, `Content-Encoding`, `Idempotent-Replay`, `Retry-After` (those present)
- **Response body:** (JSON)
- **Database check:** header count before 224, after 225; grid rows for doc 225: 1
- **Result:** PASS / FAIL (reason)
```

Put a summary table at the top (ID, result, one-line note). Include failures and "not applicable" cases with the reason. Do not drop sections between runs; mark them SKIPPED with a reason instead.

## Implementation notes for the test code

- `tests/live/` with pytest marker `live`, skipped unless `TEST_BASE_URL` is set. Fixtures: login as A and B, create a tagged document with a cleanup that deletes it (if `ENABLE_DELETE`) or lists leftovers at the end.
- Database checks use the API's read login through `app.core.db` (read-only queries only). Never write test data with SQL.
- The runner must refuse to run when the database name looks like production (a setting `TEST_ALLOWED_DB` that must equal `settings.DB_NAME`).
- Run order: Precondition P, B, C, D, E, F, G, H, J, K, M, then I and L (they change switches).

## Done when

- Precondition P passes and F1 to F10 are fixed.
- Every test above is PASS or has a recorded reason (SKIPPED with an owner approval, or "not applicable").
- The results file includes request bodies, response headers and database counts.
- `docs/05` and `docs/06` are updated for the delete response and the new `details` codes.