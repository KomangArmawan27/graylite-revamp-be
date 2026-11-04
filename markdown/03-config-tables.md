# 03. Config tables reference

Tags: **[confirmed]**, **[likely]**, **[unknown]**. Table names for Grids, Variables and Commands are taken from the exported file names (`Form.Grids`, `Form.Variables`, `Form.Commands`); verify them against the database.

General loading rules (the `meta` module does these once, so everything else sees clean objects):

- Sort child rows by their order column, never by id.
- Lowercase and normalize type strings (`STRING` becomes `text`).
- Empty or null captions fall back to a title-cased column name (`doc_id` becomes "Doc Id").
- Duplicate column names within one screen get a numeric suffix and a warning.
- Orphan references (a code that does not resolve) are skipped and logged, never fatal.

---

## `[System].[Form.Headers]`: screen registry

| Column | Meaning |
|---|---|
| `hdr_id` | Primary key. All child tables reference it. |
| `hdr_code` | Unique code. Prefix follows type. |
| `hdr_expr` | Data source. Either a full `SELECT`, a bare table, view or function name (for example `[Accounting].[CC.Master]`, wrap as `select * from <name>`), or non-SQL text on MODULE (a PHP route) and REPORT rows (XSL) **[confirmed]**. |
| `hdr_basetable` | Table that saves write to. Set on 179 of 193 forms and 152 of 179 grids. The 14 forms without one are parameter or action forms that never save **[confirmed]**. |
| `hdr_cap` | Caption. |
| `hdr_type` | `BROWSER`, `DETAIL` (form), `GRID`, `PICKER`, `REPORTSTI`, `MODULE`, `PIVOT`, `IMPORT`, `REPORT`, `DASHBOARD`, `TREE`. |
| `dtl_type` | The portal's **"Stand Alone"** flag (0 or 1). Effect **[unknown]**. Seems to mark non-document screens (master data, pending lists). Ignore for now. |
| `dtl_code` | On a browser: code of the form opened on row tap **[confirmed]** (180 of 328 browsers; 5 point to missing forms). |
| `hdr_level` | The portal's **"Visible"** role list **[confirmed]**. |
| `hdr_remark` | Free-text notes (field lists, SQL, report codes). Treat as notes only. |
| `doc_header` | On a **browser**: the portal's **"Add/Remove"** role list **[confirmed]**. On a **form**: the document type code (`STO`, `SO`; trim trailing spaces), the portal's "Doc. Header" **[confirmed]**. |
| `hdr_addremove` | On a **grid**: 1 means rows can be added and removed, 0 means read-only **[confirmed]**. On a browser the meaning is **[unknown]**; ignore it there. |
| `cc_link` | True on all rows. Meaning **[unknown]**. |
| `hdr_report` | Report renderer name on REPORTSTI (`HTML5`, `HTML5V1`). Mostly empty on browsers. |
| `dtl_journal` | The portal's **"Journal View"** flag: show the Journal toolbar button **[confirmed]**. |
| `hdr_callback` | Legacy Ext JS code. **Not executable by us.** 37 rows, 33 depend on the old UI. Port by hand per screen **[confirmed]**. |
| `param1`..`param5` | Misc. `param1` is probably the browser **Style** (`Frame`; `Fit` is the default when empty) **[likely]**. Others **[unknown]**. |
| `created_date` | Informational. |

Counts: BROWSER 328, DETAIL 193, PICKER 185, REPORTSTI 180, GRID 179, MODULE 41, other 9.

---

## `[System].[Form.Browsers]`: columns of BROWSER, PICKER and TREE screens

Only these three screen types use this table (325 browsers, 28 pickers, 1 tree). 157 of 185 pickers and 3 browsers have **no rows**: build their columns from the query result (`SELECT TOP 0 * FROM (<expr>) x` with null parameters, then read the cursor description) and infer types **[confirmed]**.

| Column | Meaning |
|---|---|
| `col_id`, `hdr_id` | Row id; owning screen. |
| `col_order` | Display order. Unique per screen, starts at 1. Sort by this. |
| `col_name` | Column name in the query result. |
| `col_cap` | Caption (29 empty, mostly hidden columns). |
| `col_type` | `text`, `money`, `integer`, `number`, `date`, `datetime`, `boolean`; rare: `list`, `image`, `document`, `balance`. Pickers use upper-case `STRING`/`NUMBER`. 12 are null: default to text. |
| `col_scale` | Decimal places for `money`/`number` (money 0 or 2; number 0, 1, 2 or 4). |
| `col_width` | Desktop pixels (1 to 700, median 100). On mobile use only as a relative hint. |
| `col_hide` | True on 21%. Hidden columns carry ids and state. **Still send them in every row.** |
| `col_key` | **1** = row identity (one per screen, usually `doc_id`, mostly hidden) **[confirmed]**. **4** = the date column (mostly `doc_date`) **[likely]**; probably default sort or the date range. **3, 7, 2** **[unknown]**. Treat 1 as the row key and 4 as the date column, ignore the rest. |
| `col_readonly` | True on all but 12 rows. Treat everything as read-only. |
| `col_lock`, `col_preview` | Always false. Ignore. |

---

## `[System].[Form.Details]`: fields of a form (DETAIL)

One form is one header row plus its field rows here (3,941 rows, about 20 fields per form, about 11 visible).

| Column | Meaning |
|---|---|
| `hdr_id`, `col_id` | Owning form; row id. |
| `tab_name` | Tab group (mostly "General"; 26 forms have 2 or 3 tabs). |
| `col_order` | Field order. |
| `col_caption` | Label. |
| `col_name` | Database column and variable name. Empty on layout rows (grid, hr, label, button). |
| `col_uitype` | The widget; see the table below. |
| `col_datatype` | SQL-side type: `number`, `string`, `date`, `datetime`, `integer`. Null on layout rows. Drives parameter typing. |
| `col_length` | Input width in desktop pixels (the portal's "UI Wd"). Ignore on mobile. |
| `col_labelwidth` | Label width. 0 means no label. Ignore on mobile except "0 = no label". |
| `col_prec`, `col_scale` | Precision and decimals. |
| `col_offset` | **-1** means "same row as the previous field" (for example `store_name` beside `store_no`) **[confirmed]**. Other values are pixel nudges: ignore. |
| `col_PK` | **1** = the record id (exactly one per form) **[confirmed]**. **4** = the human document number (`doc_no`), good form title **[confirmed]**. **5** = a name **[likely]**. |
| `col_update` | **Saved to the database when true [confirmed].** Only meaningful when `col_name` is set. Readonly fields can still be saved (683 are, for example `doc_no`, `doc_date`). Pickers' display fields are false; the hidden id they fill is true. On a form's **grid** row, true means "save this grid's rows with the form" **[likely]**. |
| `col_readonly` | User cannot edit. Says nothing about saving. |
| `col_hide` | Not displayed. Value is still loaded, held in the form state, and saved if `col_update`. |
| `col_defaultvalue` | Default for new records: constants (`1`, `IDR`), helper calls (`TODAY()`, `DATEADD(12,TODAY())`), session names (`_USERID`, `_USERLOGIN`, `_CCID`). Resolved by the helper language in `docs/04`. |
| `col_controlexpr` | Depends on `col_uitype`; see below. |
| `col_controlvalue` | Depends on `col_uitype`; see below. |
| `object_id` | Always empty. Ignore. |

### `col_uitype` families

| uitype | Rows | `col_controlexpr` | `col_controlvalue` |
|---|---|---|---|
| text, textarea, integer, number, money, date, datetime, boolean, file, image | about 2,500 | empty | empty |
| **picker** | 259 | A PICKER `hdr_code`. 254 of 259 resolve. | Rarely a column list like `supl_no,supl_desc` (8 rows). Trim spaces. |
| **combobox** | 133 | Inline options as a JS array text: `[1,\'Memorial\'],[2,\'Adjustment\']` (escaped quotes). Parse to `[value, label]` pairs. | |
| **comboquery** | 100 | SQL; first column is the label, second the value, a single column serves as both. | |
| **xcomboquery** | 39 | Like comboquery, but the extra returned columns fill other fields by name (for example `doc_currency` also fills `doc_currate`). | A parent variable name this query depends on (for example `ware_id`, `LocID`). |
| **formula** | 464 | A JS-style expression over field names and variables (see `docs/04`). 311 are saved, 153 display-only. | |
| **grid** | 171 | A GRID `hdr_code` (131 distinct, 24 shared by several forms; 3 unresolved). `col_name` is empty. | |
| **button** | 25 | `exec <proc> ::Var::, ...`, may chain `; select 'REFRESHFORM();'`. Placeholders are variables. | |
| **hr**, **label** | 123, 81 | label: HTML text. | |
| import, listener | 3, 2 | | |

Null `col_uitype` (32 rows) behaves like layout filler. Skip.

---

## `[System].[Form.Grids]`: columns of a GRID

2,615 rows, 178 of 179 grids (`Grid.Sales.Order.Header.Pending` has none: auto-generate). About 15 columns per grid, 39% hidden. Same fields as the form table minus layout items: `col_order`, `col_cap`, `col_name`, `col_datatype`, `col_uitype`, `col_uiwidth`, `col_scale`, `col_readonly`, `col_hide`, `col_update`, `col_defaultvalue`, `col_controlexpr`, `col_controlvalue`. Widgets: text, integer, money, number, picker (199), formula (110), date, boolean, comboquery, xcomboquery, combobox, document, datetime. Picker and combo rules are the same as for forms.

**`col_key` in grids [confirmed]** (exactly one column of each per grid):

| Key | Meaning | Example |
|---|---|---|
| 1 | The row's own id (hidden) | `trans_id` |
| 2 | **Foreign key to the parent record** (162 grids). Filter rows by this; set it on insert. | `doc_id` |
| 3 | Row number (137 grids), visible as "No" | `trans_idx` |

Other behavior:

- Update flag works as in forms. Pickers' `item_no`/`item_desc` are display-only; hidden `item_id` is saved.
- Formulas: 52 saved, 58 display-only. Example: `(trans_qty*trans_price)-trans_discvalue`.
- The grid's query often returns **more columns than are configured** (for example `item_price_ms`, `item_price_ws`). Send every result column; configured ones carry display metadata.
- Header flag `hdr_addremove` = 1 allows adding and removing rows; 0 means a read-only grid (pending lists, WIP, COGS).
- Of 179 grids, 51 are never referenced by any form (12 are `GridSA.*` standalone editable grids).

---

## `[System].[Form.Variables]`: named values

2,083 rows, 658 screens (BROWSER 256, DETAIL 145, GRID 123, REPORTSTI 134). Names match **case-insensitively**.

| Column | Meaning |
|---|---|
| `var_name` | Variable name, used as `::Name::` in SQL and as an identifier in formulas. |
| `var_order` | Order in the filter bar. |
| `var_remark` | Label for filter inputs (for example "Date From"); a note elsewhere. |
| `var_controlexpr` | Where the value comes from: a field or column name on this screen. |
| `var_aggr` | Overloaded **[confirmed]**: on grids, `sum` (aggregate of the column in `var_controlexpr`; 176 rows). On browsers and reports, the **default value expression** (`TODAY()`, `DATEADD(-30,TODAY())`, `FDOM(TODAY())`, `EDOM(TODAY())`, `YEAR(TODAY())`, or constants like `0`, `-`). |
| `var_uitype` | Input widget for filter variables: date (422), text (178), integer (159), picker (119), comboquery (44), combobox (24), number. |
| `var_datatype` | SQL-side type. |
| `var_nullable` | False (967 rows) means required. |
| `var_hide`, `var_readonly` | Hidden or fixed filters. |
| `var_scale`, `var_flag`, `var_labelwidth`, `var_uiwidth`, `var_offset` | Unused or desktop layout. Ignore. |

Five kinds of variable (see `docs/04` for how they resolve):

1. **Filter input** on browsers and reports (has `var_uitype`).
2. **Form field exposed as a variable** (`var_controlexpr` is a field: `DocID` = `doc_id`, `CustID`, `DoctypeID`).
3. **Grid aggregate** (`var_aggr` = `sum`).
4. **Passed-down variable**: a grid variable with no expression and remark "variable from Form".
5. **Selection total**: sum over a checkbox column (for example `sumSelected`).

---

## `[System].[Form.Commands]`: toolbar buttons

528 rows on 162 screens: 117 forms (434 commands) and 45 browsers (94). Up to 14 per screen. Refresh, Save and Journal are built into the app and are not rows here.

| Column | Meaning |
|---|---|
| `cmd_name` | Button label. |
| `cmd_order` | Order. |
| `cmd_controlexpr` | SQL to run: 443 `exec` calls and 84 `select`s; 110 have several statements separated by `;`. Placeholders are variables. |
| `cmd_privilege` | Role list: `All` (276), roles, or null (184). Null meaning **[unknown]**; treat as denied. |
| `cmd_type` | `OKCANCEL` (356) shows a confirmation with `cmd_message`. Numeric 0 to 3 **[unknown]**: default to "confirm if `cmd_message` is set". |
| `cmd_message` | Confirmation text ("Are you sure you want to process this operation?", 401 rows). |
| `cc_id` | 1 or 0. Meaning **[unknown]**. Ignore. |

Command output is often **client JavaScript text** (`REFRESHFORM();`, `OPENREPORT(...)`, `OPENREPORTNEWTAB(...)`, `alert(...)`). Parse into whitelisted actions (`docs/05`). Printing calls `System.[Form.Print] 'SOA5', ::DocID::`; logs and journal call `System.[Form.Openlink] '<TARGET>', ::DocID::, ...`.

---

## Users and roles

`[System].[User.Level]` (`lvl_id`, `lvl_idx`, `user_group`): the role names (for example Director, Finance, General, HRD, and about 25 in total).

`[System].[User.Management]` columns that matter:

| Column | Use |
|---|---|
| `user_id` | `_USERID` |
| `user_login` | Login name (can contain spaces, for example "IT Staff"); `_USERLOGIN` |
| `user_name`, `user_email` | Display |
| `user_password` | 20-byte hash, looks like unsalted SHA-1 **[unknown method]**. See `docs/07`. |
| `old_password`, `new_password`, `user_passlastupdate` | Password history; an expiry rule may exist **[unknown]** |
| `user_level` | **Comma-separated role names** (single value for some users, 19 roles for another) **[confirmed]** |
| `cc_id`, `cc_strid` | Cost center: `_CCID` |
| `div_id`, `ware_id`, `branch_id`, `empl_id` | Defaults and scoping |
| `is_active` | Must be 1 to log in |
| `is_login1device`, `login_session` | Single-device rule: a new login replaces the session id **[likely]** |
| `user_lastlogin`, `user_lastactive` | Update on login and activity |
| `token_no`, `token_date`, `menu_type`, `web_type`, `is_dashboard`, `mapp_accesslimit`, `user_emergency`, `user_public` | **[unknown]** |

**Never log or return** `user_password`, `old_password`, `new_password`, `token_no` or `login_session`.
