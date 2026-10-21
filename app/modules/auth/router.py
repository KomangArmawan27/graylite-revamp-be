from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_user
from app.modules.auth.schemas import LoginRequest, RefreshRequest, TokenResponse
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
service = AuthService()

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    return service.login(db, req)

@router.post("/refresh")
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    return service.refresh(db, req.refreshToken)

@router.post("/logout")
def logout(user: dict = Depends(get_current_user)):
    return {"ok": True}

@router.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    return user
