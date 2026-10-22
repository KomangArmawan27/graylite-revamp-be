from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Any
from app.core.db import get_db
from app.core.deps import get_current_user

router = APIRouter(prefix="/grids", tags=["grids"])

@router.get("/{code}/rows")
def get_grid_rows(
    code: str,
    parentId: Optional[Any] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    # Get grid query from Form.Headers
    sql = "SELECT hdr_expr FROM [System].[Form.Headers] WHERE hdr_code = :code"
    res = db.execute(text(sql), {"code": code}).mappings().first()
    if not res or not res.get("hdr_expr"):
        return {"items": []}

    expr = res.get("hdr_expr").strip()
    if not expr.lower().startswith("select"):
        expr = f"SELECT * FROM {expr}"

    query = expr
    params = {}
    if parentId is not None:
        query = f"SELECT * FROM ({expr}) x WHERE x.doc_id = :parentId"
        params = {"parentId": parentId}

    try:
        rows = db.execute(text(query), params).mappings().all()
        return {"items": [dict(r) for r in rows]}
    except Exception:
        return {"items": []}
