from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db

router = APIRouter(tags=["health"])

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/health/db")
def db_health_check(db: Session = Depends(get_db)):
    try:
        db.connection().exec_driver_sql("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
