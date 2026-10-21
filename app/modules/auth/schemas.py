from typing import List, Optional
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
    roles: List[str]
    ccId: Optional[int] = None
    divId: Optional[int] = None
    wareId: Optional[int] = None

class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int
    user: UserInfo
