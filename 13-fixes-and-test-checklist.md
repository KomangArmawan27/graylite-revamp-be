# 13. Test review, fix list and test checklist

**Status:** review of `test_results.md` (real endpoint run) against `docs/12-backend-optimization.md`. Where this file differs from `docs/12`, **this file wins** for the items it lists.

## Scope

**Do not touch** (already done and working): `app/core/config.py` and `.env` handling, `app/core/db.py`, authentication and authorization (`app/core/security.py`, `app/core/deps.py`, `app/modules/auth/*`, the role matcher), and `app/modules/health/*`.

Allowed edits are the same as in `docs/12`.

## Summary

The write protections look done. The contract fixes (P1) do not show up in the samples yet. The performance work (P2) cannot be judged from this file.

The test database is **not** the one in the `Form.Headers` export: ids are 116, 128, 129, 132 and 803 (not 1422 or 1421), and the menu has 118 items (not about 298). The pilot is now **Sales Order**: browser 128, form 129, grid 132, picker 803 (items) and 131 (customers).

---

## 1. What looks done

| Item | Evidence |
|---|---|
| P0.1 Create permission | Browser 128 reports `canAdd: false`; `POST /v1/forms/129/records` returns `403 forbidden` ("Access denied (role or missing browser)"). Meta and endpoint agree. |
| P0.3 Idempotent replay | A successful replay returns the same body and the header `Idempotent-Replay: true`. The two 403 attempts show no replay header, which fits "only 2xx results are stored". |
| Menu | `count` equals the number of items (118); sorted by module, then group (nulls first), then caption, as specified. |

## 2. Needs a check before it can be trusted

1. **The successful create returned `doc_id: 222`**, the record the earlier test already created. The browser rows already list it. A real new create must return a new id. Either the "simulated `canAdd = true`" run mocked the write, or it matched the old record. **Compare the row count of `Sales.[Order.Header]` before and after the test.**
2. **The create response has only `doc_id` and `doc_no`.** `docs/12` (P1.4) says the response is the **full re-read record** (the earlier sample had `doc_grandtotal`, `doctype_id`, and so on). If the test script did not trim it, this is a regression: the app cannot refresh totals after saving.
3. **Readonly handling (P0.2) cannot be verified.** The file has no request bodies, and record 222 kept its `doc_no` from the earlier run, before the fix. Test with one create that sends a bogus `doc_no` and one that omits it.
4. **P0.4 (writes switch) and all of P2 are not verified.** The file has no response headers (`ETag`, `Server-Timing`, `Content-Encoding`) except the replay header.

## 3. P1 contract fixes: not visible in the samples

| Item | What the results show | Fix |
|---|---|---|
| **P1.1** Grid meta | Embedded (in form meta) and standalone grid meta are the same thin shape: no `widget`, `update`, `readonly`, `parentField`, `rowNumberField`, `canAddRemove`, `saveWithForm`, `variables`; `caption` is `""`. | One `build_grid_meta` for both, with the shape in `docs/12` P1.1. Use the form's grid field caption ("Sales Item") when the grid's own caption is empty. |
| **P1.2** Types | `trans_qty`, `trans_price`, `trans_total`, `trans_idx` and all ids are `"text"`. Every picker column is `"text"`. Form fields report `dataType: "text"` for `doc_date`. | The type mapping in `docs/12` P1.2, applied to grid, picker and form columns. Add a `type` to form fields beside `dataType`. |
| **P1.3** Variables | `docQty` and `docTotal` have `"from": ""`. | `kind: "aggregate"` with `gridHdrId`, `aggregate`, `column` (`docs/12` P1.3). Unresolved names are `kind: "unresolved"` plus a linter warning. |
| **P1.4** Numbers | Integers (numbers), decimals (strings) and ISO dates are right. **`doc_discfactor` is `"0E-17"`**: exponent notation from Python's `Decimal`. | Format every decimal with `format(value, "f")` in the single serializer, so output is always plain digits (`"0.00000000000000000"`). Add a test with `Decimal("0E-17")`, `Decimal("1E+2")` and `Decimal("-0.0000")`. |
| **P1.5** Filter defaults | Still raw: `"DATEADD(-360,TODAY())"` and `"EDOM(NOW())"`. | Resolve on the server to ISO dates; add `NOW()`; on failure return `default: null` plus `defaultExpression` (`docs/12` P1.5). |
| **P1.6** Cleanups | `/new` returns `grids: {}`; form meta still has `defaults`; `doc_id` is visible with no `isId`; rows still carry `total: null`. | `/new` returns every embedded grid key with empty rows (`"132": { "rows": [] }`); remove `defaults` from form meta; mark the id field `"isId": true, "hidden": true`; omit `total` unless `includeTotal=true`. |

## 4. New findings (not in `docs/12`)

1. **Label fields have no content.** In form meta, `widget: "label"` entries have an empty `name` and `caption`, and the label text (stored in the field's expression, often HTML) is not returned. Add a `text` property (raw text; the app sanitizes). Do the same for `hr`.
2. **HTML in captions.** Three menu captions contain `<br/>` (`Item AccInv<br/>Monitor`, `Menu Mobile <br/>Configuration`, `Closed Period<br/>Management`). Add one `clean_caption()` (strip tags, collapse whitespace) used for menu captions, meta captions and command names.
3. **Duplicate captions.** "Sales Order" appears 6 times, "Inventory" 3, and five others twice. The app will show the group as a subtitle, and the menu already returns `module` and `group`. `Browser.HR.Employee.Master.OFA` (same caption as `Browser.HR.Employee.Master`) is still in the menu. **Owner decision:** also exclude `.OFA` and `.PLR` clones by default?
4. **Group spellings** differ (`Financial` and `Finansial`, plus `Finish`). They come from the code names, so fix them in the config, not in code.
5. **31 of 118 menu items have no `detailHdrId`.** They are read-only listings (ledgers, aging, reports). The app must hide Add and row navigation for them.
6. **Unresolved `flow_state` HTML** (`<div style='color:red'>New Entry</div>`) in browser rows is handled by the front end. Do not change the backend for it.

## 5. Fix order

1. Resolve the create anomaly (section 2, items 1 and 2), because it touches data.
2. P1.1, P1.2, P1.3: forms and grids are blocked on them.
3. P1.4 decimal formatting (small and safe).
4. P1.5, P1.6, then findings 1 and 2 in section 4.
5. Re-run the tests below and re-share the results with request bodies and headers.

## 6. Test checklist (what is missing from `test_results.md`)

Record **request bodies and response headers** for every call. Run writes only against staging with `ENABLE_WRITES` on there.

**Auth and session**
- [ ] `GET /v1/me`
- [ ] `POST /v1/auth/refresh` and `POST /v1/auth/logout`, then a call with the old token

**Browser**
- [ ] A second page of rows using `nextCursor` (with `pageSize=1`), then the same cursor with a different `ADate` (expect `400 invalid_cursor`)
- [ ] A request without `ADate` (expect `422 invalid_filter` with `details`)
- [ ] `q` search, and `sort` with an unknown column (expect `422 invalid_sort`)
- [ ] A form id sent to `/v1/browsers/{hdrId}/rows` (expect `404 wrong_screen_type`)

**Forms and grids**
- [ ] `GET /v1/forms/129/records/{id}` for a record with grid rows
- [ ] `GET /v1/grids/132/rows?parentId=...`
- [ ] `GET /v1/pickers/803/rows?q=...` and `GET /v1/pickers/131/rows?q=...`
- [ ] `GET /v1/forms/{hdrId}/fields/{name}/options` for a combobox or comboquery field
- [ ] Create with grid rows: check `doc_id` is **new**, the full header comes back, and grid rows have ids and `trans_idx`
- [ ] Update: change a grid row, add a row, delete a row (`deleted`); confirm other documents' rows are untouched
- [ ] Update with a stale `schemaVersion` (expect `409 schema_stale`)
- [ ] Create with a bogus `doc_no` (ignored), with a formula value (kept), with an unknown field (expect `422 validation_failed`)
- [ ] Update on a document whose `docflow_seq` is not 0 (expect `409 conflict`)
- [ ] `DELETE` with `ENABLE_DELETE` off (expect `501 not_implemented`)

**Idempotency**
- [ ] Same key, same body, after success: replay header, no second record
- [ ] Same key, different body: `409 conflict` (`key_reused`)
- [ ] Same key while the first request is still running: `409 conflict` (`in_progress`)
- [ ] A failed create (4xx) retried with the same key succeeds when the cause is fixed

**Commands**
- [ ] `POST /v1/screens/129/commands/252/run` (Print SO): the response and its actions
- [ ] A command from another screen under `{hdrId}` (expect `404 not_found`)
- [ ] A user without the command's privilege (expect `403 forbidden`)

**Performance and headers (P2)**
- [ ] `ETag` on `GET /v1/meta/browser/128`, then a repeat with `If-None-Match` (expect `304` and no config SQL)
- [ ] A user with different roles gets a different `ETag`
- [ ] `Server-Timing` on every response; `Content-Encoding: gzip` on a large response
- [ ] `GET /v1/admin/metrics` (admin only): cache hits, slow queries, p95 per route, pool status

**Writes switch**
- [ ] With `ENABLE_WRITES=false`, every write endpoint returns `403` and the database is unchanged

## 7. Front-end handling already planned

These are handled in the front end and need no backend change until the fixes land: raw filter defaults, the HTML `flow_state` badge, 4-decimal strings, and hiding Add and row taps when `detailHdrId` is null. Once P1 is done, the adapters can be simplified.

## 8. Owner decisions

| # | Decision | Default until decided |
|---|---|---|
| D7 | Exclude `.OFA` and `.PLR` clones from the menu by default | Not excluded |
| D8 | Confirm whether the test "simulated `canAdd`" wrote to the database | Treat the create as unverified |