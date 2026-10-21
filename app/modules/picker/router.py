from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, Any
from app.core.db import get_db
from app.core.deps import get_current_user
from app.shared.params import bind

router = APIRouter(tags=["pickers"])

@router.get("/v1/pickers/{code}/rows")
def get_picker_rows(
    code: str,
    q: Optional[str] = None,
    page: int = 1,
    pageSize: int = 50,
    request: Request = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    sql = "SELECT hdr_expr FROM [System].[Form.Headers] WHERE hdr_code = :code"
    res = db.connection().exec_driver_sql(sql, {"code": code}).mappings().first()
    if not res or not res.get("hdr_expr"):
        return {"items": []}

    expr = res.get("hdr_expr").strip()
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

@router.get("/v1/forms/{code}/fields/{name}/options")
def get_field_options(
    code: str,
    name: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    # Retrieve field definition for combobox or comboquery
    sql = """
    SELECT d.col_uitype, d.col_controlexpr 
    FROM [System].[Form.Details] d
    JOIN [System].[Form.Headers] h ON h.hdr_id = d.hdr_id
    WHERE h.hdr_code = :code AND d.col_name = :name
    """
    res = db.connection().exec_driver_sql(sql, {"code": code, "name": name}).mappings().first()
    if not res:
        return {"options": []}
    
    uitype = res.get("col_uitype")
    expr = res.get("col_controlexpr")
    
    if uitype == "combobox":
        # parse options
        return {"options": []}
    elif uitype in ("comboquery", "xcomboquery") and expr:
        try:
            rows = db.connection().exec_driver_sql(expr).mappings().all()
            return {"options": [dict(r) for r in rows]}
        except Exception:
            return {"options": []}
            
    return {"options": []}
