
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.modules.meta.service import clear_meta_cache
from app.shared.catalog import clear_catalog_cache

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/lint")
def lint_config(hdrId: int | None = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return {"reports": []}

@router.post("/cache/refresh")
def refresh_cache(user: dict = Depends(get_current_user)):
    clear_catalog_cache()
    clear_meta_cache()
    return {"ok": True, "message": "Cache cleared"}
