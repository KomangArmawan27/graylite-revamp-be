from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.db import get_db
from app.core.deps import get_current_user
from app.modules.meta.service import MetaService

router = APIRouter(prefix="/meta", tags=["meta"])
service = MetaService()

@router.get("/browser/{code}")
def get_browser_meta(code: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return service.get_browser_meta(db, code, user.get("roles", []))

@router.get("/form/{code}")
def get_form_meta(code: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return service.get_form_meta(db, code, user.get("roles", []))

@router.get("/grid/{code}")
def get_grid_meta(code: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    # Placeholder or implementation for grid meta
    return {"code": code}

@router.get("/picker/{code}")
def get_picker_meta(code: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return {"code": code}
