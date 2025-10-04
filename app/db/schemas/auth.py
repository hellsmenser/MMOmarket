from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    invite_code: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str


class InviteCodeResponse(BaseModel):
    invite_code: str
