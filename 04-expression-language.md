# 04. Expressions, parameters and variables

Everything dynamic in the config is one of three things: a `::Param::` placeholder in SQL, a **variable**, or a **helper-language expression** (defaults, filter defaults, formulas). All three share one name space and one function library.

## 1. The `::Param::` engine (`app/shared/params.py`)

Placeholders look like `::Name::` (regex `::(\w+)::`). They appear inside `hdr_expr`, `cmd_controlexpr` and combo queries. In your pilot they are arguments of a table-valued function:

```sql
select * from [Sales].[Take.Order.Browser] (::ADate::, ::BDate::, ::_USERID::)
```

Rules:

1. **Never substitute text.** Replace each placeholder with `?` and bind the value as a parameter.
2. Matching is **case-insensitive** (`ADate`, `Adate`, `adate` are the same).
3. Bind in order of appearance. If a name appears twice, add its value twice.
4. A placeholder found inside a quoted SQL string literal is an error (the engine cannot bind it). Reject the config and let the linter report it.
5. A missing value for a **required** variable is a 422 error before any SQL runs. A missing non-required value binds `NULL`.
6. Values are converted using the variable's `var_datatype` (or the field's `col_datatype`): dates as `date`/`datetime` objects, numbers as `Decimal` or `int`, text as `str`.

Function signature:

```python
def bind(sql: str, values: Mapping[str, Any]) -> tuple[str, list[Any]]:
    """Return (sql_with_question_marks, params_in_order). Names are matched case-insensitively."""
```

### Resolution order for a placeholder value

1. **Session values** (always from the token, never from the request): `_USERID`, `_USERLOGIN`, `_CCID`, `_USERLEVEL` (and any other name starting with `_` that the server defines).
2. **Screen variables** (`Form.Variables` for that screen, plus the grid and form variables passed in). The value comes from user input, the default expression, a field value, or a grid aggregate.
3. **Fallback:** a field or column of that name in the request's field values (63 of 758 command placeholders resolve only this way, for example `doc_id`).

If nothing resolves, see rule 5 above.

A client may send values for kind-1 filter variables and for field values. A client value for a name that starts with `_` is **ignored**.

## 2. Variables

A variable is a named value on a screen. Kinds (from `docs/03`):

| Kind | Source of the value |
|---|---|
| Filter input (browser, report) | Client sends it; if missing, use the default expression in `var_aggr`. |
| Form field as variable | `var_controlexpr` names a field: value is that field. (`DocID` = `doc_id`.) |
| Grid aggregate | `var_aggr` = `sum`: sum of the column named in `var_controlexpr` over the grid's rows. |
| Passed-down | Same name as a form variable; the value arrives from the form. |
| Selection total | Sum over a checkbox column. |

**Name matching is case-insensitive across components.** Example chain from the pilot:

1. The grid declares `docqty` = sum(`trans_qty`).
2. The form declares `docQty` with expression `docqty`: it picks up the grid's value by name.
3. The form formula field `doc_qty` has expression `docQty`, and `doc_qty` has the Update flag, so it is saved with the header.

**Server vs app.** The Flutter app recomputes aggregates and formulas as the user edits, so the server need not. The server does need them when it resolves defaults and when it (optionally) revalidates totals on save. Both sides therefore implement the same evaluator (see section 4).

### Filter variables become the browser filter bar

For a browser, the filter bar comes from the variables that have `var_uitype`, ordered by `var_order`:

- `name`, `label` (`var_remark`), `type` (`var_uitype`), `default` (resolved by the API, see below), `required` (`var_nullable` is false), `hidden` (`var_hide`).
- Picker and combo filters carry their lookup source (picker code or options).
- **Fallback:** if a browser has no filter variables, scan its `hdr_expr` for placeholders and make one filter per distinct non-session name, with a type inferred from the name (`ADate`/`BDate` mean date).

**The API resolves defaults** and sends the resolved values (for example `2026-09-21` and `2026-10-21`), so the app does not need the date helper functions for filters.

## 3. Helper-language functions

Used in `col_defaultvalue`, `var_aggr` defaults and formulas. They appear in JavaScript-like syntax (ternaries, `Math.round`, `Math.floor`, arithmetic). **Implement them in `app/shared/expr/functions.py` and mirror them in the Flutter app** (the app needs them for formulas and new-record defaults).

| Function | Behavior | Status |
|---|---|---|
| `TODAY()` | Current date (server date) | [confirmed] |
| `DATEADD(n, date)` | Add `n` **days** to `date`. `DATEADD(-30,TODAY())` is 30 days ago. | [likely] |
| `FDOM(date)` | First day of the month | [likely] |
| `EDOM(date)` | End (last day) of the month | [likely] |
| `YEAR(date)`, `MONTH(date)` | Year or month number of a date; also `YEAR(TODAY())` as a filter default | [likely] |
| `ISNA(x, d)` | `d` if `x` is null, empty or NaN, otherwise `x` (134 uses in formulas) | [likely] |
| `MULTIDISC(s)` | Combines a multi-level discount string such as `"10+5"` into one factor or percent | **[unknown]**: derive from the old JS or sample data before implementing |
| `VATPERCENT(date)` | VAT percentage valid on a date | **[unknown]**: likely a database lookup; the API must provide the rate |
| `Math.round`, `Math.floor`, `Math.max`, `Math.min` | As in JavaScript | [confirmed] |
| Session names `_USERID`, `_USERLOGIN`, `_CCID` | In defaults, replaced by session values | [confirmed] |

Constants in defaults: numbers (`1`, `0`, `111.01`) and plain text (`IDR`, `Kas`, `-`).

If an expression uses a function that is not in this table, the config loader reports it and treats the value as empty (never fails the screen).

## 4. Formulas

A formula field (`col_uitype = 'formula'`) has an expression over **field names and variable names** of the same record (and, in grids, the same row):

- Single name: `docQty` (a variable, usually a grid aggregate).
- Arithmetic: `(trans_qty*trans_price)-trans_discvalue`, `doc_total*doc_discfactor`.
- Calls: `ISNA(x,0)`, `MULTIDISC(trans_discremark)`, `VATPERCENT(doc_date)`, `Math.round(...)`, ternaries `a ? b : c`.

Rules:

1. **Never use `eval`/`exec` or any dynamic code execution.** Use a small parser (for example the `jsep`-style approach: tokenize, build an AST, evaluate nodes) that supports only literals, names, unary and binary operators, ternary, member access to `Math`, and calls to the whitelisted functions above.
2. Names resolve case-insensitively against the current record, then variables.
3. Division by zero or a missing name yields null and a logged warning, not an exception.
4. 311 of 464 form formulas are **saved** (Update flag). By default the server **trusts the value sent by the client** and validates only its type and range. Server-side recomputation for totals is optional and an open question (`docs/08`).

## 5. Command output (client instructions)

Commands may return strings of the old front end's JavaScript. **Never run or forward them.** Parse each returned value with a strict pattern list into JSON actions (`docs/05`):

| Pattern (case-insensitive) | Action |
|---|---|
| `REFRESHFORM();` | `{"type": "refresh"}` |
| `SAVEFORM();` | `{"type": "save"}` |
| `OPENREPORT('<code>', ...);` | `{"type": "openReport", "code": "<code>", "args": [...], "newTab": false}` |
| `OPENREPORTNEWTAB('<code>', ...);` | same with `"newTab": true` |
| `alert('<text>');` | `{"type": "alert", "message": "<text>"}` |
| `System.[Form.Openlink]` target results | `{"type": "openLink", "target": "<TARGET>", "args": [...]}` |

Anything else is dropped and logged with the screen code and a truncated copy of the text. Add patterns only after seeing real output samples.
