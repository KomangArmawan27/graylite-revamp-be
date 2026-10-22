from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Any
from app.core.db import get_db
from app.core.deps import get_current_user
from app.modules.meta.service import MetaService

router = APIRouter(prefix="/grids", tags=["grids"])
meta_service = MetaService()

@router.get("/{hdrId}/rows")
def get_grid_rows(
    hdrId: int,
    parentId: Optional[Any] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    header = meta_service.get_screen(db, hdrId)
    if (header.get("hdr_type") or "").upper() != "GRID":
        from app.core.errors import AppError
        raise AppError(status_code=404, code="wrong_screen_type", message=f"Expected GRID, got {header.get('hdr_type')}")

    expr = (header.get("hdr_expr") or "").strip()
    if not expr:
        return {"items": []}

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
