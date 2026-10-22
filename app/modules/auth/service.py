import uuid
from typing import Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.errors import AppError
from app.core.security import verify_password, create_access_token, create_refresh_token, verify_token
from app.modules.auth.repository import AuthRepository
from app.core.config import settings

repo = AuthRepository()

class AuthService:
    def login(self, db: Session, login_req: Any) -> Dict[str, Any]:
        user = repo.get_user_by_login(db, login_req.login)
        if not user or not user.get("is_active", True):
            raise AppError(status_code=401, code="unauthorized", message="Invalid login or password")

        stored_pw = user.get("user_password")
        if not verify_password(login_req.password, stored_pw):
            raise AppError(status_code=401, code="unauthorized", message="Invalid login or password")

        repo.update_last_login(db, user.get("user_id"))

        roles_str = user.get("user_level") or ""
        roles = [r.strip() for r in roles_str.split(",") if r.strip()]

        sid = str(uuid.uuid4())
        token_data = {
            "sub": user.get("user_id"),
            "login": user.get("user_login"),
            "roles": roles,
            "ccId": user.get("cc_id"),
            "divId": user.get("div_id"),
            "wareId": user.get("ware_id"),
            "sid": sid,
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": settings.JWT_ACCESS_TTL_MIN * 60,
            "user": {
                "id": user.get("user_id"),
                "login": user.get("user_login"),
                "name": user.get("user_name") or user.get("user_login"),
                "roles": roles,
                "ccId": user.get("cc_id"),
                "divId": user.get("div_id"),
                "wareId": user.get("ware_id"),
            }
        }

    def refresh(self, db: Session, refresh_token: str) -> Dict[str, Any]:
        payload = verify_token(refresh_token)
        user_id = payload.get("sub")
        
        # Verify user still active
        sql = "SELECT * FROM [System].[User.Management] WHERE user_id = :user_id"
        user = db.execute(text(sql), {"user_id": user_id}).mappings().first()
        if not user or not user.get("is_active", True):
            raise AppError(status_code=401, code="unauthorized", message="User inactive or removed")

        token_data = {
            "sub": payload.get("sub"),
            "login": payload.get("login"),
            "roles": payload.get("roles"),
            "ccId": payload.get("ccId"),
            "divId": payload.get("divId"),
            "wareId": payload.get("wareId"),
            "sid": payload.get("sid"),
        }
        access_token = create_access_token(token_data)
        return {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": settings.JWT_ACCESS_TTL_MIN * 60,
        }
