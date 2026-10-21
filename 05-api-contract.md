# 05. API contract (v1)

The contract is the product. FastAPI generates the OpenAPI spec from the Pydantic models in each module's `schemas.py`. Once a shape is published, only **add** fields; never rename or remove them without a new version.

Conventions:

- Base path `/v1`. JSON only. UTF-8.
- **Meta properties are camelCase. Row and field data use database column names verbatim** (`doc_id`, `trans_qty`).
- Dates are ISO strings: `2026-10-21` for date, `2026-10-21T14:05:00` for datetime. Decimals are JSON numbers (rounded to the column scale).
- Every endpoint except login needs `Authorization: Bearer <accessToken>`.
- Every response carries `X-Request-Id`.
- Lists use **keyset (cursor) paging** (`app/core/pagination.py`). Request `pageSize` and `cursor`; response `{ "items": [...], "pageSize": 50, "hasMore": true, "nextCursor": "..." }`. Browser rows are ordered by the date column and row key, descending, unless a validated `sort` is given. `total` is included only when cheap.

## Endpoints

| Method and path | Purpose |
|---|---|
| `POST /v1/auth/login` | Log in |
| `POST /v1/auth/refresh` | New access token |
| `POST /v1/auth/logout` | Invalidate the session |
| `GET /v1/me` | Current user and roles |
| `GET /v1/menu` | Navigation the user may see |
| `GET /v1/meta/browser/{code}` | Browser config |
| `GET /v1/meta/form/{code}` | Form config including embedded grids |
| `GET /v1/meta/grid/{code}` | Grid config (standalone grids) |
| `GET /v1/meta/picker/{code}` | Picker columns |
| `GET /v1/browsers/{code}/rows` | Browser rows (query: filters, `cursor`, `pageSize`, `q`, `sort`) |
| `GET /v1/forms/{code}/new` | Blank record with resolved defaults |
| `GET /v1/forms/{code}/{id}` | One record with its grids' rows |
| `POST /v1/forms/{code}` | Create |
| `PUT /v1/forms/{code}/{id}` | Update |
| `DELETE /v1/forms/{code}/{id}` | Delete (disabled until the behavior is verified; returns 501) |
| `GET /v1/grids/{code}/rows` | Standalone grid rows (`parentId` or filters) |
| `GET /v1/pickers/{code}/rows` | Picker search (`q`, `page`, `pageSize`, plus context values) |
| `GET /v1/forms/{code}/fields/{name}/options` | Options for combobox, comboquery or xcomboquery |
| `POST /v1/commands/{cmdId}/run` | Run a toolbar command |
| `GET /v1/admin/lint` | Config linter report (admin role) |
| `POST /v1/admin/cache/refresh` | Drop cached config (admin role) |
| `GET /health`, `GET /health/db` | Liveness and database check (no auth, outside `/v1`) |

## Auth

```json
// POST /v1/auth/login
{ "login": "nisaa", "password": "..." }

// 200
{
  "accessToken": "...", "refreshToken": "...", "expiresIn": 1800,
  "user": {
    "id": 22, "login": "nisaa", "name": "Sales Distri",
    "roles": ["Marketing"], "ccId": 1, "divId": 3, "wareId": 1
  }
}
```

Token claims: `sub` (user id), `login`, `roles` (list), `ccId`, `divId`, `wareId`, `sid` (session id), `exp`. Signed with RS256. Details in `docs/07`.

## Browser meta (pilot example)

```json
{
  "code": "Browser.Sales.Order.Retail",
  "caption": "Take Order",
  "schemaVersion": "a41f09c2",
  "rowKey": "doc_id",
  "dateColumn": "doc_date",
  "detailCode": "Form.Sales.Order.Retail",
  "canAdd": true,
  "canRemove": false,
  "style": "Fit",
  "columns": [
    { "name": "doc_id",   "caption": "Doc Id",  "type": "integer", "hidden": true,  "scale": 0, "width": 100 },
    { "name": "doc_no",   "caption": "Doc No",  "type": "text",    "hidden": false, "scale": 0, "width": 100 },
    { "name": "doc_date", "caption": "Date",    "type": "date",    "hidden": false, "scale": 0, "width": 100 },
    { "name": "doc_total","caption": "Total",   "type": "money",   "hidden": true,  "scale": 0, "width": 100 }
  ],
  "filters": [
    { "name": "ADate", "label": "Date From", "type": "date", "default": "2026-09-21", "required": true, "hidden": false },
    { "name": "BDate", "label": "Date To",   "type": "date", "default": "2026-10-21", "required": true, "hidden": false }
  ],
  "layout": {
    "title": "doc_no", "date": "doc_date", "subtitle": "store_name",
    "badge": ["flow_state"], "metrics": ["doc_qty"], "details": ["salesman", "distri_desc", "doc_remark"]
  },
  "commands": []
}
```

Notes:

- `columns` are sorted by `col_order`; hidden columns are included.
- `canAdd`/`canRemove` come from the `doc_header` role list matched against the user's roles, and require a `detailCode` for add.
- `schemaVersion` is a hash of the screen's config (`docs/06`).
- `layout` is the computed hint from `docs/01`.
- `commands` lists toolbar buttons the user is allowed to see: `{ "id": 812, "name": "Print SO", "confirm": "Are you sure ...", "order": 1 }`.

## Browser rows

```
GET /v1/browsers/Browser.Sales.Order.Retail/rows?ADate=2026-09-21&BDate=2026-10-21&pageSize=50
```

The next page repeats the request with `&cursor=<nextCursor>`.

```json
{
  "items": [ { "doc_id": 900101, "doc_no": "STO26100001", "doc_date": "2026-10-20", "doc_total": 1250000, "...": "..." } ],
  "pageSize": 50, "hasMore": false, "nextCursor": null
}
```

Every result column is returned, including columns that are not configured. Unknown query parameters that are not declared filters are ignored; names starting with `_` are always ignored.

## Form meta (abridged)

```json
{
  "code": "Form.Sales.Order.Retail",
  "caption": "Take Order",
  "schemaVersion": "7be3d210",
  "idField": "doc_id",
  "titleFields": ["doc_no"],
  "docHeader": "STO",
  "canSave": true,
  "journalView": true,
  "tabs": [
    { "name": "General", "fields": [
      { "name": "doc_no", "caption": "Doc No", "widget": "text", "dataType": "string",
        "readonly": true, "hidden": false, "update": true, "inlineWithPrevious": false },
      { "name": "store_no", "caption": "Store", "widget": "picker", "pickerCode": "Picker.Sales.Store.Branch",
        "update": false, "readonly": false },
      { "name": "store_name", "caption": "", "widget": "text", "readonly": true, "update": false, "inlineWithPrevious": true },
      { "name": "cust_id", "widget": "integer", "hidden": true, "update": true },
      { "name": "doc_qty", "caption": "Total Qty", "widget": "formula", "expression": "docQty", "update": true },
      { "name": "", "widget": "grid", "gridCode": "Grid.Sales.Order.Retail.Detail", "caption": "Sales Item", "saveWithForm": true }
    ] }
  ],
  "variables": [ { "name": "DocID", "from": "doc_id" }, { "name": "docQty", "from": "docqty" } ],
  "grids": { "Grid.Sales.Order.Retail.Detail": { "...": "grid meta, see below" } },
  "defaults": { "doc_date": "2026-10-21", "doctype_id": 30, "user_id": 22 },
  "commands": [ { "id": 801, "name": "Print SO (1/2)", "confirm": null, "order": 1 } ]
}
```

`widget` is the normalized `col_uitype`. Picker field definitions also carry `controlColumns` (from `col_controlvalue`, if any). Combobox with inline options carries `options: [{ "value": 1, "label": "Memorial" }]`. Layout rows (hr, label, button) are included in order with no `name`.

## Grid meta

```json
{
  "code": "Grid.Sales.Order.Retail.Detail",
  "rowIdField": "trans_id",
  "parentField": "doc_id",
  "rowNumberField": "trans_idx",
  "canAddRemove": true,
  "columns": [
    { "name": "item_no", "caption": "Code", "widget": "picker", "pickerCode": "Picker.Inventory.Item.brgJadi.Retail", "update": false },
    { "name": "item_id", "widget": "integer", "hidden": true, "update": true },
    { "name": "trans_qty", "caption": "Qty", "widget": "number", "scale": 2, "update": true },
    { "name": "trans_total", "caption": "Total", "widget": "formula", "expression": "trans_qty*trans_price", "update": false }
  ],
  "variables": [ { "name": "docqty", "aggregate": "sum", "column": "trans_qty" } ]
}
```

## Form read

`GET /v1/forms/{code}/{id}` returns:

```json
{
  "header": { "doc_id": 900101, "doc_no": "STO26100001", "cust_id": 120, "store_no": "S01", "store_name": "Branch A" },
  "grids": { "Grid.Sales.Order.Retail.Detail": { "rows": [ { "trans_id": 1, "doc_id": 900101, "item_id": 5001, "trans_qty": 10 } ] } },
  "schemaVersion": "7be3d210"
}
```

`GET /v1/forms/{code}/new` returns the same shape with defaults filled and empty grids.

## Save payload (create and update)

```json
{
  "schemaVersion": "7be3d210",
  "header": { "doc_id": null, "doc_date": "2026-10-21", "cust_id": 120, "doc_qty": 10, "doc_remark": "..." },
  "grids": {
    "Grid.Sales.Order.Retail.Detail": {
      "rows": [ { "trans_id": null, "item_id": 5001, "trans_qty": 10, "trans_price": 55000 } ],
      "deleted": [ 88123 ]
    }
  }
}
```

- The header carries **only Update-flagged fields**; unknown keys are rejected with 422.
- Rows with a null or missing row id are inserted; rows with an id are updated; ids in `deleted` are removed (only when the grid allows it).
- A `schemaVersion` that no longer matches is rejected with **409 `schema_stale`**, and the app reloads the meta.
- Response: the saved record in the **form read** shape (with generated ids and document number).
- Optional header `Idempotency-Key` on `POST` (create), so a retry from a poor mobile connection does not create a duplicate. How the old project stores idempotency is unknown (`docs/08` Q15); until it is reviewed the header is accepted and ignored.
- When `ENABLE_WRITES` is false, `POST`, `PUT`, `DELETE` and writing commands return 403 `forbidden`.

## Command run

```json
// POST /v1/commands/801/run
{ "values": { "DocID": 900101 } }

// 200
{ "ok": true, "message": null, "actions": [ { "type": "refresh" } ], "dropped": 0 }
```

Only the allowed variables are read from `values` (matched by name); `_`-prefixed names are ignored. Allowed action types:

| type | Fields |
|---|---|
| `refresh` | none |
| `save` | none |
| `openReport` | `code`, `args` (list), `newTab` (bool) |
| `openLink` | `target`, `args` |
| `alert` | `message` |

`dropped` counts returned instructions that did not match the whitelist.

## Errors

```json
{ "error": { "code": "validation_failed", "message": "Invalid payload", "requestId": "c1f2...",
             "details": [ { "field": "trans_qty", "problem": "must be a number" } ] } }
```

| HTTP | `code` | When |
|---|---|---|
| 400 | `bad_request` | Malformed request |
| 401 | `unauthorized` | Missing, expired or invalid token |
| 403 | `forbidden` | Role not allowed |
| 404 | `not_found` | Unknown screen code or record |
| 409 | `schema_stale` | Config changed since the app loaded it |
| 409 | `conflict` | Data conflict (for example a database rule rejected the save) |
| 422 | `validation_failed` | Payload failed validation |
| 501 | `not_implemented` | For example delete before it is verified |
| 500 | `internal_error` | Unexpected; details only in the server log |
| 504 | `query_timeout` | Config SQL exceeded the time limit |

Messages that come from the database (for example a `RAISERROR` text raised on purpose by a trigger) may be returned as `message` in a 409 or 422. Other SQL errors are logged and returned as `internal_error` without SQL text.
