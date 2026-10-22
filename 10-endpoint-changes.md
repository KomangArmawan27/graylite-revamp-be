# 10. Endpoint changes: menu from `Form.Headers`, and `hdr_id` in every path

**Status:** change request. Where this file differs from `docs/05-api-contract.md`, **this file wins**. It also resolves `docs/08` Q10 (menu source).

## Scope

This change is about **endpoints only**.

**Do not touch** (already done and working):

- configuration and settings: `app/core/config.py`, `.env` handling
- database layer: `app/core/db.py`
- authentication and authorization: `app/core/security.py`, `app/core/deps.py`, `app/modules/auth/*`, and the existing role-matching helper
- `app/modules/health/*`

If a task seems to need a change in those files, stop and ask. The only allowed edit outside the new work is **adding `include_router(...)` lines** in `app/main.py`. Reuse the existing dependencies for the current user and role checks; do not write a second role matcher.

## Change 1: the menu comes from `[System].[Form.Headers]`

No separate menu table is used. `GET /v1/menu` is derived from `Form.Headers` (read through the `meta` module, as `docs/02` requires).

### Which rows become menu items

| Rule | Detail |
|---|---|
| Type | `hdr_type = 'BROWSER'` only. Browsers are the entry points. |
| Has a data source | `hdr_expr` is not empty (1 browser has none). |
| Visible to the user | The existing role matcher applied to `hdr_level` (the Visible role list). Empty means denied. |
| Not a legacy copy | Exclude codes that match the patterns below. |

Not in the menu for now: MODULE (PHP routes the app cannot render), REPORTSTI and REPORT, PIVOT, DASHBOARD, TREE, IMPORT, and GRID/GridSA standalone grids. The response carries `type` so these can be added later without changing the shape.

**Default exclusion patterns** (after trimming the code, case-insensitive). Keep them as a module-level constant in `app/modules/menu/service.py`, **not** a new setting:

- contains `tidak dipakai` (unused)
- ends with `.` plus six digits, for example `.260416` (dated clones)
- has a segment `Dev`, for example `Browser.Sales.Order.Internal.Dev.260107`

On the current data this removes about 30 of 328 browsers and leaves about 298.

### Item fields

| Field | Source |
|---|---|
| `hdrId` | `hdr_id` |
| `code` | `hdr_code`, **trimmed** (some codes have leading spaces) |
| `caption` | `hdr_cap` trimmed. If empty (4 browsers), use the code without its first segment, dots replaced by spaces (`Browser.Sales.Market` becomes "Sales Market"). |
| `type` | always `"browser"` for now |
| `module` | the **2nd** segment of the code (`Browser.Sales.Order.Retail` gives `Sales`) |
| `group` | the **3rd** segment when the code has 4 or more segments (`Order`), otherwise `null` |
| `detailHdrId` | the `hdr_id` of the form named by `dtl_code`, or `null` if it does not resolve (5 browsers point to missing forms) |

Resolve codes by **trimming and comparing case-insensitively**. Sort by `module`, then `group` (nulls first), then `caption`, all case-insensitive.

About 273 of 328 browsers have a group; 55 have only module-level codes. Modules in the data: Accounting 131, Sales 79, Inventory 42, Purchase 32, HR 13, Production 7, System 5, and a few small ones.

### Response

```json
GET /v1/menu

{
  "count": 298,
  "items": [
    {
      "hdrId": 1422,
      "code": "Browser.Sales.Order.Retail",
      "caption": "Take Order",
      "type": "browser",
      "module": "Sales",
      "group": "Order",
      "detailHdrId": 1421
    }
  ]
}
```

The app builds the module and group tree from `module` and `group`. The API stays flat, which is also easier to port to PHP.

### How to build it

- Add to `meta`: `service.list_screens(types)` and, in `repository.py`, one `SELECT` on `[System].[Form.Headers]`. Do not load `hdr_expr` text. Ask only whether it is empty. Resolve `dtl_code` with a self-join on trimmed codes:

  ```sql
  SELECT h.hdr_id, LTRIM(RTRIM(h.hdr_code)) AS hdr_code, LTRIM(RTRIM(h.hdr_cap)) AS hdr_cap,
         h.hdr_type, h.hdr_level,
         CASE WHEN LEN(LTRIM(RTRIM(ISNULL(h.hdr_expr, '')))) > 0 THEN 1 ELSE 0 END AS has_expr,
         d.hdr_id AS detail_hdr_id
  FROM [System].[Form.Headers] h
  LEFT JOIN [System].[Form.Headers] d
         ON LTRIM(RTRIM(d.hdr_code)) = LTRIM(RTRIM(h.dtl_code))
  WHERE h.hdr_type = 'BROWSER';
  ```

- Cache this **unfiltered** list with the existing config cache TTL. Apply the role filter and exclusion patterns per request.
- Add `app/modules/menu/` with `router.py`, `service.py` and `schemas.py`. The menu module has **no `repository.py`**: it calls `meta.service.list_screens()` only (rule 5 of `docs/02`: `meta` is the only reader of the config tables).
- Use the read-only session. Menu code never writes.

## Change 2: every endpoint is addressed by `hdr_id`

All config tables hang off `hdr_id`, so every screen endpoint takes the **integer `hdr_id`** in the path. Codes stay in responses for display and debugging, but they are never used as path identifiers. Reasons: codes can contain spaces and slashes (`Report.Purchase.Order.1/2`) or leading spaces, and `hdr_id` is a single unique key.

Path parameters are validated as integers (`>= 1`). Add one helper in `meta`:

```python
def get_screen(hdr_id: int) -> Screen   # trimmed code, type, roles, ids; cached
```

Every endpoint calls it first and then checks:

1. the screen exists, else `404 not_found`
2. the screen type matches the endpoint, else `404 wrong_screen_type` (for example a form id sent to `/browsers/...`)
3. the user may open it (existing role matcher on `hdr_level`), else `403 forbidden`

### Endpoint list (replaces the table in `docs/05`)

| Method and path | Purpose |
|---|---|
| `GET /v1/menu` | Menu items (Change 1) |
| `GET /v1/meta/browser/{hdrId}` | Browser config |
| `GET /v1/meta/form/{hdrId}` | Form config including embedded grids |
| `GET /v1/meta/grid/{hdrId}` | Grid config (standalone use) |
| `GET /v1/meta/picker/{hdrId}` | Picker columns |
| `GET /v1/browsers/{hdrId}/rows` | Browser rows (filters, `cursor`, `pageSize`, `q`, `sort`) |
| `GET /v1/forms/{hdrId}/new` | Blank record with resolved defaults |
| `GET /v1/forms/{hdrId}/records/{recordId}` | One record with its grids' rows |
| `POST /v1/forms/{hdrId}/records` | Create |
| `PUT /v1/forms/{hdrId}/records/{recordId}` | Update |
| `DELETE /v1/forms/{hdrId}/records/{recordId}` | Delete (still disabled by default, `docs/06`) |
| `GET /v1/grids/{hdrId}/rows` | Standalone grid rows (`parentId` or filters) |
| `GET /v1/pickers/{hdrId}/rows` | Picker search (`q`, `cursor`, `pageSize`, context values) |
| `GET /v1/forms/{hdrId}/fields/{name}/options` | Options for combobox, comboquery, xcomboquery |
| `POST /v1/screens/{hdrId}/commands/{cmdId}/run` | Run a toolbar command of that screen (browser or form) |
| `GET /v1/admin/lint` | Config linter report (optional `?hdrId=`) |
| `POST /v1/admin/cache/refresh` | Drop cached config |

Two points to note:

- **`/records/` in form paths.** It separates the record id from `new` and from `fields/...`, so `recordId` can never collide with a keyword.
- **Commands are nested under the screen.** `cmdId` is a row of `Form.Commands`. Before running, check that the command's `hdr_id` equals `{hdrId}` (else `404 not_found`), then the screen's Visible roles, then the command's `cmd_privilege`.

## Change 3: JSON shape deltas

Nothing here is released yet, so these are not breaking changes. Update `schemas.py` and fixtures accordingly.

- **Every meta response** gets `hdrId` next to `code`.
- **Cross-references carry both the id and the code**, resolved by the loader (trim, case-insensitive):
  - browser meta: `detailCode` plus `detailHdrId`
  - form meta fields: `pickerCode` plus `pickerHdrId`; grid fields `gridCode` plus `gridHdrId`
  - grid columns and filters with lookups: `pickerHdrId`
  - an unresolved reference gives `null` for the id (and a linter warning), never an error
- **Maps keyed by screen are keyed by `hdrId` as a string**, not by code:
  - form meta: `"grids": { "1425": { ... } }`
  - form read response: `"grids": { "1425": { "rows": [ ... ] } }`
  - save payload:

    ```json
    {
      "schemaVersion": "7be3d210",
      "header": { "doc_id": null, "cust_id": 120 },
      "grids": { "1425": { "rows": [ { "trans_id": null, "item_id": 5001, "trans_qty": 10 } ], "deleted": [ 88123 ] } }
    }
    ```

- **Command entries in meta** stay `{ "id", "name", "confirm", "order" }`. The run path is the only thing that changes.
- **Errors:** add `wrong_screen_type` (404) to the table in `docs/05`.

## Tests and acceptance

Add fixtures under `tests/fixtures/menu/` and `tests/fixtures/endpoints/` (config rows in, expected response out):

1. Menu: a role that matches `hdr_level` sees the item, one that does not, does not; an empty `hdr_level` hides it.
2. Menu: the three exclusion patterns, caption fallback, module and group derivation (3-segment and 4-segment codes), trimmed codes with a leading space, an item with no `hdr_expr` omitted.
3. Menu: `detailHdrId` resolves with trimming and null for an orphan `dtl_code`.
4. Endpoints: a non-integer `hdrId` gives 422; an unknown id gives 404; a form id on a browser endpoint gives `wrong_screen_type`; a screen the user cannot open gives 403.
5. Commands: a command of another screen under `{hdrId}` gives 404.

Staging data check: for a user whose roles match, `GET /v1/menu` returns about 298 items. It includes `hdrId` 1422 (`Browser.Sales.Order.Retail`, caption "Take Order", `detailHdrId` 1421).

## After implementing

Update `docs/05-api-contract.md` (endpoint table, path examples, payload shapes) and mark `docs/08` Q10 as resolved.

## Not decided here

- **Legacy menu order and grouping.** `Form.Headers` has a TREE row `Tree.Menu` whose expression selects `object_id` and `object_caption` from a menu table. It is not used now (module and group come from code segments). It can be added later as an optional source if you want the old menu's order and grouping.
- **Reports and standalone grids.** They are not in the menu until the old app's way of opening them is confirmed.
- **Ordering of modules.** They sort alphabetically.