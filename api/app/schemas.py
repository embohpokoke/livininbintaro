from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator


class AuthUserOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    is_active: bool = True


class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

    @model_validator(mode="after")
    def validate_login(self):
        if not self.email and not self.username:
            raise ValueError("Either email or username is required")
        return self


class Token(BaseModel):
    token: str
    access_token: str
    token_type: str = "bearer"
    user: AuthUserOut
    expires_at: str


class DashboardStats(BaseModel):
    total_listings: int
    active_listings: int
    hot_listings: int
    total_rumah: int = 0
    listings_jual: int = 0
    listings_sewa: int = 0
    total_leads: int
    pipeline: dict


class UserOut(AuthUserOut):
    created_at: Optional[datetime] = None
