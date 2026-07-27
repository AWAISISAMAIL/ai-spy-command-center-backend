from pydantic import BaseModel, Field, field_validator
import re
from datetime import datetime

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, example="agent007")
    password: str = Field(..., min_length=6, max_length=100, example="secret123")

    @field_validator("username")
    def username_must_be_alphanumeric(cls, v):
        if not re.match("^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username mein sirf letters, numbers aur underscore allowed hain")
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str = Field(..., example="agent007")
    password: str = Field(..., example="secret123")

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., example="your-refresh-token-here")