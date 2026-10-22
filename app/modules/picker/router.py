from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Any
from app.core.db import get_db
from app.core.deps import get_current_user
from app.shared.params import bind
from app.modules.meta.service import MetaService

router = APIRouter(prefix="/pickers", tags=["pickers"])
meta_service = MetaService()

@router.get("/{hdrId}/rows")
def get_picker_rows(
    hdrId: int,
    q: Optional[str] = None,
    page: int = 1,
    pageSize: int = 50,
    request: Request = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    header = meta_service.get_screen(db, hdrId)
    if (header.get("hdr_type") or "").upper() != "PICKER":
        from app.core.errors import AppError
        raise AppError(status_code=404, code="wrong_screen_type", message=f"Expected PICKER, got {header.get('hdr_type')}")

    expr = (header.get("hdr_expr") or "").strip()
    if not expr:
        return {"items": []}

    if not expr.lower().startswith("select"):
        expr = f"SELECT * FROM {expr}"

    param_values = {
        "_USERID": user.get("id"),
        "_USERLOGIN": user.get("login"),
        "_CCID": user.get("ccId"),
    }
    bound_sql, bound_params = bind(expr, param_values)
    
    try:
        rows = db.connection().exec_driver_sql(bound_sql, tuple(bound_params)).mappings().all()
        items = [dict(r) for r in rows]
        if q:
            q_lower = q.lower()
            items = [item for item in items if any(q_lower in str(v).lower() for v in item.values() if v is not None)]
        return {"items": items[:pageSize]}
    except Exception:
        return {"items": []}
