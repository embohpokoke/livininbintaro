from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import build_login_response, find_user_by_login, get_current_user, serialize_user
from app.database import get_db
from app.schemas import LoginRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    login_value = data.email or data.username
    user = find_user_by_login(db, login_value)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    from app.auth import verify_password

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return build_login_response(user)


@router.get("/me")
def me(current_user=Depends(get_current_user)):
    return serialize_user(current_user)
