import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from app.core.config import settings

ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: Any) -> bool:
    if not hashed_password:
        return False

    if isinstance(hashed_password, bytes):
        import hashlib
        if len(hashed_password) == 20:
            if hashlib.sha1(plain_password.encode("utf-8")).digest() == hashed_password:
                return True
        if len(hashed_password) == 16:
            if hashlib.md5(plain_password.encode("utf-8")).digest() == hashed_password:
                return True
        if plain_password.encode("utf-8") == hashed_password:
            return True
        return False

    if isinstance(hashed_password, str):
        if plain_password == hashed_password:
            return True

        if hashed_password.startswith("$argon2"):
            try:
                return ph.verify(hashed_password, plain_password)
            except (VerifyMismatchError, InvalidHashError):
                return False

        import hashlib
        if len(hashed_password) == 40:
            if hashlib.sha1(plain_password.encode("utf-8")).hexdigest().lower() == hashed_password.lower():
                return True

    return False

def _get_private_key() -> Optional[str]:
    path = settings.JWT_PRIVATE_KEY_PATH
    if os.path.exists(path):
        with open(path, "r") as f:
         return f.read()
    return None

def _get_public_key() -> Optional[str]:
    path = settings.JWT_PUBLIC_KEY_PATH
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return None

def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TTL_MIN))
    to_encode.update({"exp": expire})
    private_key = _get_private_key()
    if private_key:
        return jwt.encode(to_encode, private_key, algorithm="RS256")
    else:
        # Fallback secret for dev/testing if pem files don't exist yet
        return jwt.encode(to_encode, "dev-secret-key", algorithm="HS256")

def create_refresh_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    to_encode.update({"exp": expire})
    private_key = _get_private_key()
    if private_key:
        return jwt.encode(to_encode, private_key, algorithm="RS256")
    else:
        return jwt.encode(to_encode, "dev-secret-key", algorithm="HS256")

def verify_token(token: str) -> dict[str, Any]:
    public_key = _get_public_key()
    try:
        if public_key:
            return jwt.decode(token, public_key, algorithms=["RS256"], options={"verify_sub": False})
        else:
            return jwt.decode(token, "dev-secret-key", algorithms=["HS256"], options={"verify_sub": False})
    except jwt.PyJWTError as e:
        from app.core.errors import AppError
        raise AppError(status_code=401, code="unauthorized", message="Invalid or expired token")
