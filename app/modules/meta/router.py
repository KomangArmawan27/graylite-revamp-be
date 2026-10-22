from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_user
from app.modules.meta.service import MetaService

router = APIRouter(prefix="/meta", tags=["meta"])
service = MetaService()

@router.get("/browser/{hdrId}")
def get_browser_meta(hdrId: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return service.get_browser_meta(db, hdrId, user.get("roles", []))

@router.get("/form/{hdrId}")
def get_form_meta(hdrId: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return service.get_form_meta(db, hdrId, user.get("roles", []))

@router.get("/grid/{hdrId}")
def get_grid_meta(hdrId: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return service.get_grid_meta(db, hdrId, user.get("roles", []))

@router.get("/picker/{hdrId}")
def get_picker_meta(hdrId: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return service.get_picker_meta(db, hdrId, user.get("roles", []))
