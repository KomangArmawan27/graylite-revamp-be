from typing import Any, Callable, List, Optional
from fastapi import Depends, Header, Request
from app.core.security import verify_token
from app.core.errors import AppError
from app.shared.roles import allowed

def get_current_user(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError(status_code=401, code="unauthorized", message="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    return {
        "id": payload.get("sub"),
        "login": payload.get("login"),
        "roles": payload.get("roles", []),
        "ccId": payload.get("ccId"),
        "divId": payload.get("divId"),
        "wareId": payload.get("wareId"),
        "sid": payload.get("sid"),
    }

def require_roles(role_list: Optional[str]) -> Callable:
    def dependency(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        user_roles = user.get("roles", [])
        if not allowed(role_list, user_roles):
            raise AppError(status_code=403, code="forbidden", message="Insufficient permissions")
        return user
    return dependency
