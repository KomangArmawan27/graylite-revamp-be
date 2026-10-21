# 01. How the ERP works

Confidence tags used in all docs: **[confirmed]** seen in data or the portal, **[likely]** strongly inferred, **[unknown]** not yet known.

## The idea

All data lives in SQL Server: master data, transactions and system configuration. Every transaction has a **header table** and a **detail (line) table**. Screens are not coded. They are rows in the `[System]` config tables, edited in a "Module Configuration" portal, and a generic PHP/JS front end renders them. To add a screen, someone creates a table-valued function or stored procedure and configures it in the portal.

Our API does the same job for a Flutter app: read the config, serve it as JSON, and run generic CRUD and commands from it.

## Screen types

All screens are rows in `[System].[Form.Headers]` (1,115 rows). `hdr_type` says what kind:

| hdr_type | Rows | Meaning | API treatment |
|---|---|---|---|
| BROWSER | 328 | A list of rows with filters | meta + rows endpoints |
| DETAIL | 193 | A form (one record, header fields) | meta + read + save + delete |
| GRID | 179 | Line items embedded in a form (or standalone) | served inside the form |
| PICKER | 185 | Lookup list used by form and grid fields | search endpoint |
| REPORTSTI | 180 | HTML5 report | later |
| MODULE | 41 | Legacy PHP route (not config-driven) | link out or skip |
| PIVOT, IMPORT, REPORT, DASHBOARD, TREE | 9 | Special widgets | later |

`hdr_code` is unique and its prefix matches the type (`Browser.`, `Form.`, `Grid.`, `GridSA.`, `Picker.`, `Report.`, `Module.`, and so on). Many codes are clones (`.OFA`, `.PLR`, dated copies, "tidak dipakai" for unused). Migrate by usage, not by count.

## Child tables

Everything else is keyed by `hdr_id` (foreign key to `Form.Headers`):

| Table | Holds |
|---|---|
| `Form.Browsers` | column definitions for BROWSER, PICKER and TREE screens |
| `Form.Details` | fields of a form (DETAIL) |
| `Form.Grids` | columns of a GRID |
| `Form.Variables` | named values for any screen type |
| `Form.Commands` | toolbar buttons that run stored procedures |
| `User.Management`, `User.Level` | users and the role names |

Full column reference: `docs/03-config-tables.md`.

## The main flow

```
Browser (list)  --dtl_code-->  Form (header fields)  --grid field-->  Grid (lines)
      |                              |                                     |
  filters = variables           commands (toolbar)                 sums become variables
```

1. A browser's SQL (`hdr_expr`) returns rows. Filters come from its variables (for example `ADate`, `BDate`). `dtl_code` names the form to open when a row is tapped.
2. A form's SQL returns one header record. Its fields (`Form.Details`) say how to edit it. Fields of type `grid` embed a grid by code.
3. A grid's rows are filtered by the parent id column (grid column with `col_key = 2`).
4. Commands run stored procedures with bound variables.

## Conventions that make it work

1. **Names are the glue [confirmed].** A picker's SQL aliases its columns to the *target field names*, and picking a row copies each returned column into the field with the same name. Example: `Picker.Sales.Store.Branch` returns `store_id as cust_id, store_no, store_name`, which fill the form's hidden `cust_id` plus `store_no` and `store_name`.
2. **Update flag = saved [confirmed].** A form field or grid column with `col_update` true is written to the database. Unchecked fields are display-only (for example `store_name`). The hidden id field is what is actually saved.
3. **`::Param::` placeholders** in SQL resolve through variables [confirmed]. See `docs/04`.
4. **Variables carry data between components [confirmed].** A grid declares a variable that is the sum of a column (`docqty` = sum of `trans_qty`). The form declares a variable of the same name (case-insensitive), and a formula field uses it (`doc_qty` = `docQty`).
5. **Procedures can return client instructions [confirmed].** Many commands `select 'REFRESHFORM();'` or `OPENREPORT(...)` and the old front end executes the text. We parse these into a safe action list.
6. **Roles are comma-separated lists of exact names [confirmed]**, or `All`. See `docs/07`.
7. **One helper language** is shared by formulas, defaults and filter defaults [confirmed]: `TODAY()`, `DATEADD(days, date)`, `FDOM`, `EDOM`, `ISNA`, and others in `docs/04`.
8. **Header and grid rows save together [likely].** The form's grid field has the Update flag set when the grid is saved with the form.

## Pilot walk-through: Take Order

1. `Browser.Sales.Order.Retail` runs `select * from [Sales].[Take.Order.Browser] (::ADate::, ::BDate::, ::_USERID::)`. Its variables: `ADate` default `DATEADD(-30,TODAY())`, `BDate` default `TODAY()`, both required. `dtl_code` is `Form.Sales.Order.Retail`.
2. The form (24 fields in 2 tabs, base table `Sales.[Order.Retail.Header]`, `doc_header` = `STO`) shows document number and date, two pickers with inline description fields, a grid field, a formula total, a remark, and a "Sent" tab.
3. The grid `Grid.Sales.Order.Retail.Detail` (13 columns, base table `Sales.[Order.Retail.Detail]`) has key columns `trans_id` (key 1), `doc_id` (key 2) and `trans_idx` (key 3, shown as "No").
4. The grid's `docqty` variable feeds the form's `doc_qty` formula, which is saved with the header.
5. The form has 4 toolbar commands (print, print, print, document logs) that run with `::DocID::` bound.

## Browser layout hints (computed by the API)

Browser configs describe columns, not phone layouts. The API computes **layout hints** so the Flutter app does not have to guess, using only column data. Rules (in `app/modules/browser/layout.py`):

- **title**: the first visible column named like `doc_no` or `*_no`/`*_code`, else the first visible text column.
- **date**: the `col_key = 4` column, else the first visible date or datetime.
- **subtitle**: the widest visible text column (by `col_width`) not already used.
- **badge**: visible columns named like `state`, `status` or `flow`, and booleans (up to 2).
- **metrics**: visible money, number and integer columns that are not ids (up to 3).
- **details**: all other visible columns, in `col_order`.
- Hidden columns are never shown, but **always sent in the data**: the row key, state values and ids are needed by the app.

A future optional column `mobile_role` on `Form.Browsers` (title, subtitle, badge, metric, detail, hidden) would override the heuristics. If it exists and is set, it wins.
