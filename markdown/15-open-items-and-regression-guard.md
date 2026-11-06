# 15. Open items and regression guard (after test run 2)

**Status:** change request. It follows `docs/12`, `docs/13` and `docs/14`; where it differs from them, **this file wins**.

## The most important rule: do not touch anything that already works

Run 2 (`test_results2.md`) showed that a large part of the API now behaves correctly. **Do not change, refactor, rename, reformat or "improve" any of it.** This change request is limited to the numbered items in section 3, and each item states the exact output that is allowed to change.

If a fix seems to require touching something in the "frozen" list below, or something not listed anywhere, **stop and ask**. Do not decide alone.

Also **do not touch** (as before): `app/core/config.py` and `.env` handling, `app/core/db.py`, authentication and authorization (`app/core/security.py`, `app/core/deps.py`, `app/modules/auth/*`, the role matcher), and `app/modules/health/*`.

## 1. Frozen: verified working in run 2

| Area | Verified behavior (do not change) |
|---|---|
| Permissions | General user: browser 128 returns `canAdd: true`, `canRemove: true`; create on form 129 succeeds. |
| Create with a grid | New `doc_id` (225), full re-read record, grid row with new `trans_id`, parent `doc_id` forced to the new header id, `trans_idx` auto-assigned, `doc_no` returned as the database set it, `trans_total` computed by the database. |
| Idempotent replay | Same key and body returns the same data with `Idempotent-Replay: true`, and does not create a second record. |
| Browser 128 meta | Typed columns (`doc_id` integer, `doc_date` date, `doc_grandtotal` money), `rowKey`, `dateColumn`, `detailHdrId`, `layout`, resolved filter defaults as ISO dates. |
| Form 129 meta | `idField` with `isId` and `hidden`, no `defaults` key, aggregate variables (`docTotal`, `docQty` with `gridHdrId`), `kind` on variables, label `text`, typed fields. |
| Grid 132 meta | Embedded and standalone copies equal except `caption`; typed columns; `parentField`, `rowNumberField`, `canAddRemove`, `saveWithForm`; passed variables (`WareID`, `ProposalID`) have `kind: "passed"`. |
| Picker 803 meta | Typed columns (`item_id`, `class_id` integer; `trans_price` money). |
| Browser rows | Integers as numbers, decimals as plain strings (no exponent), ISO dates, no `total` key unless requested, paging fields. |
| `/new` | `doc_date` default plus `cust_id`, and the grid key with empty rows. |
| `schemaVersion` | The same value in form meta, `/new` and the create response. |
| Menu | `{count, items}`, 118 items, order and fields as they are. |

### How to enforce it

1. **Before changing anything**, save the run-2 responses as golden files in `tests/golden/run2/` (menu, browser meta 128, form meta 129, grid meta 132, picker meta 803, browser rows, `/new`, create, replay).
2. Add a live test that calls the same endpoints and compares each response with its golden file after **masking volatile values**: `schemaVersion`, `x-request-id`, ids and timestamps of newly created records, today's dates, and row data that depends on the database contents.
3. After each item below, run the comparison. The only differences allowed are the ones listed under "Allowed diff" for that item. Any other difference is a regression: revert it.
4. Keep every existing unit and fixture test passing. Do not edit or delete an existing test to make a change pass.

---

## 2. Owner decisions

| # | Decision | Default until decided |
|---|---|---|
| D7 | Exclude `.OFA` and `.PLR` clones from the menu by default | **Not excluded** (no change) |
| D8 | Was the earlier "simulated canAdd" create real? | **Resolved:** run 2 created record 225 with a real General user |
| D9 | Header totals vs grid (item 7 below): **A** recompute on the server, **B** validate and reject mismatches, **C** trust the client | **C** (no change). Do not implement A or B until this row says so. |
| D10 | Records 220 and 222 disappeared from browser 128 between runs. Were they removed on purpose? | Not a code task. The owner confirms. |

Owner fills in: D9 = `____`.

---

## 3. Items

Each item lists the **allowed diff**: what may change in responses. Nothing else may change.

### 1. `hidden` must be a boolean (F2)

**Seen:** `hidden: ""` on the `label` and `grid` fields of form 129.

**Fix:** coerce `hidden` (and `readonly`, `update`, `inlineWithPrevious`) to booleans in the field builder, for every field including layout rows (`label`, `grid`, `hr`, `button`).

**Allowed diff:** `hidden` changes from `""` to `false` (or `true` if the config says hidden) on layout fields in form meta.

**Acceptance:** a schema test that every `hidden` in form meta is a boolean; golden comparison shows only those changes.

### 2. `trans_total` is a computed column (F7)

**Seen:** grid 132 `trans_total` has `widget: "number"`, `readonly: false`, `update: false`, and `expression: "(trans_qty*trans_price)-trans_discvalue"`. The database computes it (the create returned `"550000.00000000"`).

**Fix:** in the one grid-column builder (used for embedded and standalone grids):

- a column that has an `expression` and is not a picker or combo gets `widget: "formula"`;
- a column with `update: false` and a formula gets `readonly: true`.

Leave the `expression` on picker columns as it is (it repeats `pickerCode`; the front end ignores it when `pickerCode` is present).

**Allowed diff:** only the `trans_total` column in the embedded grid (form meta) and in `GET /v1/meta/grid/132`: `widget` becomes `formula`, `readonly` becomes `true`. Same for any other column in other grids that meets the rule.

**Acceptance:** fixture test for the rule (formula with update true stays `readonly` as configured; formula with update false becomes readonly); golden diff limited to that column.

### 3. Strip HTML from captions (F5)

**Seen:** menu captions with `<br/>` (hdr 480, 629, 511).

**Fix:** one `clean_caption()` (remove tags, replace `<br>` with a space, collapse whitespace, trim), used for menu captions, meta captions and command names.

**Allowed diff:** only the three captions above (and any other containing tags) change. `count`, order, ids, codes, modules and groups stay identical. Duplicate captions and the `.OFA` clone stay as they are (D7).

**Acceptance:** no caption contains `<` or `>`; menu count is still 118; golden diff limited to those captions.

### 4. `cc_id` default in `/new` (F8)

**Seen:** the hidden updatable field `cc_id` is not in the `/new` header.

**Fix:** first **check the config** for form 129 (`col_defaultvalue` of `cc_id`).
- If it has a default (for example `_CCID`), resolve it in `/new` like the other defaults.
- If it has none, change nothing and report that in the PR.

**Allowed diff:** `header.cc_id` appears in `/new` only if the config has a default.

### 5. Form read must return the picker display columns

**Seen:** the header returned by the create response (and so by the form read) has `cust_id` and `cust_name` (null) but no `cust_no`, so the app cannot show the customer text for the picker field `cust_no`. The header also contains base-table columns such as `coba_total`, `grpDoc` and `doc_id_si`, which suggests the read is a plain base-table read.

**Fix:** check how the header read is built. `docs/06` says it wraps the form's `hdr_expr` (`SELECT * FROM (<hdr_expr>) x WHERE x.[<pk>] = ?`).
- If the read does **not** use `hdr_expr`, change it to do so.
- If it does and `hdr_expr` for `Form.Sales.Order` has no `cust_no`, make no code change and report it.

**Allowed diff:** **additive only**: extra display columns from `hdr_expr` appear in the header of the form read, the create response and the update response. Existing keys and values stay the same. Saving still writes only to the base table through the Update-flagged fields.

**Acceptance:** for a record with a real customer, the form read contains the picker display column; the key set is a superset of the golden create response.

### 6. `doc_qty` is null: find out why

**Seen:** the create response has `doc_qty: null` although the grid quantity is 10. Run 2 did not record the request body, so it is not known whether the client sent it.

**Do:**
1. Create a record that sends `"doc_qty": "10"` (a formula field with `update: true`).
2. If the response shows `10.0000`, there is no bug.
3. If it shows `null`, the formula exception in the readonly rule (`docs/12` P0.2) is not working. Fix that exception only.

**Allowed diff:** none unless the bug is confirmed.

### 7. Totals can disagree with the grid (decision D9)

**Seen:** `doc_total` is 840000 but the grid sums to 550000, and `doc_grandtotal` followed the header. The server stores formula totals exactly as the client sends them.

**Do nothing until D9 is set.** If the owner chooses:

- **A (recompute):** for each form field with `widget: "formula"` whose `expression` is a variable of `kind: "aggregate"`, compute it from the submitted grid rows: sum the column, evaluating the column's own `expression` when the column is not saved (for example `trans_total`), round to the field's scale, and **override** the client value on create and update. Log a warning when the client value differed.
- **B (validate):** compute the same value and reject a difference larger than one unit of the scale with `422 validation_failed` (`details[0].code` `total_mismatch`, `field` set).

**Acceptance (only if A or B is chosen):** fixtures with matching and mismatching totals; docs for the helper evaluator updated; existing create and update tests still pass.

### 8. Replay must be byte-identical

**Seen:** the replay's JSON equals the original, but the body length is 1255 bytes against 1144.

**Fix:** store the serialized response bytes of the first successful create and return exactly those bytes on replay, with `Idempotent-Replay: true`.

**Allowed diff:** the replay body becomes byte-identical to the original. Headers stay the same.

**Acceptance:** `replay.content == original.content` and equal `content-length`.

### 9. Performance headers are missing (`docs/12` P2.1 to P2.4)

**Seen:** responses carry only `content-length`, `content-type` and `x-request-id` (plus the replay header). There is no `ETag`, `Cache-Control`, `Vary`, `Server-Timing` or `Content-Encoding`.

**Do:** implement P2.1 to P2.4 exactly as specified in `docs/12`. These are **additive** (middleware and response headers). Response bodies must not change.

**Allowed diff:** new headers only. A matching `If-None-Match` returns `304` after authentication and permission checks.

**Acceptance:** the M1 to M6 tests in `docs/14`; golden comparison shows no body difference.

### 10. Check F9 and F10

Not tested in run 2. Run the cases from `docs/14` (E2, I1 to I5) and fix only what fails:
- **F9:** a 403 on a write has `details[0].code` of `role_not_allowed`, `no_referencing_browser` or `writes_disabled`.
- **F10:** a successful delete returns `200` with `{ "recordId": <id>, "deleted": true }`.

---

## 4. Test harness changes

The results file from run 2 had no request bodies. Change the results writer so that **every section records**: the request method and URL, request headers (with `Authorization` as `Bearer <redacted>`), the **request body**, the status, **all** response headers, the response body, and the database check where relevant. Do not drop sections between runs; mark them SKIPPED with a reason.

Follow section names and IDs from `docs/14`.

## 5. Next test run (run 3), in this order

1. **Update** (H1, H2, H3, H4, H7): change the header, change a row, add a row, delete a row with `deleted`, try another document's `trans_id`, and a stale `schemaVersion`.
2. **Validation** (E4, E5, E6, E7, E8): `unknown_field`, `not_allowed`, `type_mismatch`, `schema_stale`.
3. **User B** (B2, E2, I1): `canAdd: false`, create 403, delete 403.
4. **Create variants** (E3, E9, E10, E11) and item 6 above (`doc_qty`).
5. **Browser** (B3 to B13): paging, `invalid_cursor`, `invalid_filter`, `invalid_sort`, search, wrong screen type.
6. **Idempotency** (J2 to J6): key reuse, parallel requests, failed-then-corrected.
7. **Commands** (K1 to K4, K6) and the writes switch (L). K5 (**Create PL**) only with the owner's approval.
8. **Delete** (I2 to I6) with `ENABLE_DELETE` on, on staging test records only.
9. **Pickers and options** (D1 to D4) and the **performance headers** (M1 to M7).

Use only records tagged `[API-TEST]`. Do not modify or delete any other record.

## Done when

- Every item above is done, or explicitly left as "no change" with the reason.
- The golden comparison shows only the allowed diffs.
- All existing tests still pass, unchanged.
- Run 3 results include request bodies and all response headers, and every test is PASS or has a recorded reason.