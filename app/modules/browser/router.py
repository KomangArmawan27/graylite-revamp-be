from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.db import get_db
from app.core.deps import get_current_user
from app.shared.params import bind
from app.modules.meta.service import MetaService
from app.core.config import settings

router = APIRouter(prefix="/browsers", tags=["browsers"])
meta_service = MetaService()

@router.get("/{code}/rows")
def get_browser_rows(
    code: str,
    request: Request,
    pageSize: int = Query(50, ge=1, le=1000),
    cursor: Optional[str] = None,
    q: Optional[str] = None,
    sort: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_roles = user.get("roles", [])
    # Validate browser meta and role
    browser_meta = meta_service.get_browser_meta(db, code, user_roles)
    
    # Get header expression
    sql_meta = "SELECT hdr_expr FROM [System].[Form.Headers] WHERE hdr_code = :code"
    res = db.connection().exec_driver_sql(sql_meta, {"code": code}).mappings().first()
    if not res or not res.get("hdr_expr"):
        return {"items": [], "pageSize": pageSize, "hasMore": False, "nextCursor": None}

    expr = res.get("hdr_expr").strip()
    # If expr is bare table/view/function name without SELECT
    if not expr.lower().startswith("select"):
        expr = f"SELECT * FROM {expr}"

    # Build session values and request filter query params
    query_params = dict(request.query_params)
    param_values = {
        "_USERID": user.get("id"),
        "_USERLOGIN": user.get("login"),
        "_CCID": user.get("ccId"),
        "_USERLEVEL": ",".join(user_roles),
    }
    # Add query params (filters)
    for k, v in query_params.items():
        if not k.startswith("_") and k not in ("pageSize", "cursor", "q", "sort"):
            param_values[k] = v

    bound_sql, bound_params = bind(expr, param_values)

    # Wrap with row cap and pagination
    wrapped_sql = f"SELECT TOP {min(pageSize + 1, settings.ROW_CAP)} * FROM ({bound_sql}) x"
    
    try:
        rows_result = db.connection().exec_driver_sql(wrapped_sql, tuple(bound_params)).mappings().all()
        items = [dict(r) for r in rows_result]
        
        has_more = len(items) > pageSize
        if has_more:
            items = items[:pageSize]

        return {
            "items": items,
            "pageSize": pageSize,
            "hasMore": has_more,
            "nextCursor": None,
        }
    except Exception as e:
        from app.core.errors import AppError
        raise AppError(status_code=500, code="internal_error", message=str(e))
