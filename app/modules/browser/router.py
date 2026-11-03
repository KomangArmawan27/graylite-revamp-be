
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.errors import (
    InvalidCursor,
    InvalidFilter,
    ValidationFailed,
)
from app.core.pagination import (
    BROWSER_DEFAULT_SIZE,
    BROWSER_MAX_SIZE,
    build_keyset_predicate,
    decode_cursor,
    escape_like_string,
    finish_page,
    make_fingerprint,
    resolve_sort,
)
from app.modules.meta.service import MetaService
from app.shared.params import bind
from app.shared.types import serialize_row

router = APIRouter(prefix="/browsers", tags=["browsers"])
meta_service = MetaService()


@router.get("/{hdrId}/rows")
def get_browser_rows(
    hdrId: int,
    request: Request,
    pageSize: int | None = None,
    cursor: str | None = None,
    q: str | None = None,
    sort: str | None = None,
    includeTotal: bool | None = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_roles = user.get("roles", [])
    try:
        browser_meta = meta_service.get_browser_meta(db, hdrId, user_roles)
    except Exception:
        browser_meta = {}

    header = meta_service.get_screen(db, hdrId)
    expr = (header.get("hdr_expr") or "").strip()
    if not expr:
        res = {
            "items": [],
            "pageSize": BROWSER_DEFAULT_SIZE,
            "hasMore": False,
            "nextCursor": None,
        }
        if includeTotal:
            res["total"] = 0
        return res

    if not expr.lower().startswith("select"):
        expr = f"SELECT * FROM {expr}"

    if pageSize is None:
        pageSize = BROWSER_DEFAULT_SIZE
    if pageSize < 1:
        raise ValidationFailed("pageSize must be at least 1", [{"field": "pageSize", "code": "out_of_range", "problem": "must be >= 1"}])
    pageSize = min(pageSize, BROWSER_MAX_SIZE)

    if q and len(q) > 100:
        raise ValidationFailed("Search query 'q' exceeds 100 characters", [{"field": "q", "code": "too_long", "problem": "max length 100"}])

    schema_version = browser_meta.get("schemaVersion", "1")
    row_key = browser_meta.get("rowKey")
    date_col = browser_meta.get("dateColumn")
    columns_meta = browser_meta.get("columns", [])
    known_columns = {c["name"].lower() for c in columns_meta if c.get("name")}

    default_order = []
    if date_col and date_col.lower() in known_columns:
        default_order.append((date_col, "desc"))
    elif row_key and row_key.lower() in known_columns:
        default_order.append((row_key, "desc"))
    elif known_columns:
        first_col = sorted(list(known_columns))[0]
        default_order.append((first_col, "asc"))

    if row_key and row_key.lower() not in known_columns and row_key:
        known_columns.add(row_key.lower())

    resolved_sort = resolve_sort(known_columns, sort, default_order, row_key)

    query_params = dict(request.query_params)
    filter_values = {}
    param_values = {
        "_USERID": user.get("id"),
        "_USERLOGIN": user.get("login"),
        "_CCID": user.get("ccId"),
        "_USERLEVEL": ",".join(user_roles),
    }

    filters_meta = browser_meta.get("filters", [])
    required_filters = {f["name"].lower() for f in filters_meta if f.get("required")}

    for f_meta in filters_meta:
        fname = f_meta.get("name")
        if not fname:
            continue
        fname_lower = fname.lower()
        val = query_params.get(fname) or query_params.get(fname_lower)
        if val is not None:
            filter_values[fname] = val
            param_values[fname] = val
            param_values[fname_lower] = val
        elif fname_lower in required_filters:
            raise InvalidFilter(f"Required filter '{fname}' is missing", [{"field": fname, "code": "required", "problem": "Required filter missing"}])

    for k, v in query_params.items():
        if not k.startswith("_") and k not in ("pageSize", "cursor", "q", "sort", "includeTotal"):
            if k not in filter_values:
                filter_values[k] = v
                param_values[k] = v

    fingerprint = make_fingerprint(hdrId, resolved_sort, filter_values, q, schema_version)

    cursor_data = decode_cursor(cursor)
    if cursor_data:
        if cursor_data.get("fp") != fingerprint:
            raise InvalidCursor("The list changed or filters differ, restart from the first page")
        last_values = cursor_data.get("last", [])
    else:
        last_values = []

    bound_sql, bound_params = bind(expr, param_values)

    where_clauses = []
    outer_params = list(bound_params)

    if cursor_data and last_values:
        keyset_sql, keyset_params = build_keyset_predicate(resolved_sort, last_values)
        if keyset_sql:
            where_clauses.append(keyset_sql)
            outer_params.extend(keyset_params)

    if q:
        visible_text_cols = [
            c["name"] for c in columns_meta
            if not c.get("hidden") and c.get("type") == "text" and c.get("name")
        ][:8]
        if visible_text_cols:
            escaped_q = f"%{escape_like_string(q)}%"
            q_clauses = []
            for col in visible_text_cols:
                q_clauses.append(f"x.[{col}] LIKE ? ESCAPE '\\'")
                outer_params.append(escaped_q)
            where_clauses.append(f"({' OR '.join(q_clauses)})")

    where_sql = ""
    if where_clauses:
        where_sql = f"WHERE {' AND '.join(where_clauses)}"

    order_parts = [f"x.[{col}] {direction}" for col, direction in resolved_sort]
    order_sql = f"ORDER BY {', '.join(order_parts)}" if order_parts else ""

    fetch_count = pageSize + 1
    query_sql = f"""
        SELECT TOP ({fetch_count}) *
        FROM ({bound_sql}) AS x
        {where_sql}
        {order_sql}
    """

    rows_result = db.connection().exec_driver_sql(query_sql, tuple(outer_params)).mappings().all()
    items = [serialize_row(dict(r)) for r in rows_result]

    page = finish_page(items, pageSize, resolved_sort, hdrId, fingerprint)
    res_dict = page.model_dump()
    if includeTotal:
        # Compute total count if requested
        count_sql = f"SELECT COUNT(*) FROM ({bound_sql}) AS x {where_sql}"
        total_count = db.connection().exec_driver_sql(count_sql, tuple(outer_params)).scalar()
        res_dict["total"] = total_count
    else:
        res_dict.pop("total", None)

    return res_dict
