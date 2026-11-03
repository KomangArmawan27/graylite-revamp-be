
from pydantic import BaseModel


class LoginRequest(BaseModel):
    login: str
    password: str

class RefreshRequest(BaseModel):
    refreshToken: str

class UserInfo(BaseModel):
    id: int
    login: str
    name: str
    roles: list[str]
    ccId: int | None = None
    divId: int | None = None
    wareId: int | None = None

class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int
    user: UserInfo
