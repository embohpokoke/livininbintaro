from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def derive_email(username: str | None) -> str | None:
    if not username:
        return None
    return f"{username}@livininbintaro.my.id"


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": derive_email(user.username),
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
    }


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def build_login_response(user: User) -> dict:
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role,
        },
        expires_delta=expires_delta,
    )
    expires_at = datetime.now(timezone.utc) + expires_delta
    return {
        "token": token,
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user),
        "expires_at": expires_at.isoformat(),
    }


def find_user_by_login(db: Session, login: str | None) -> User | None:
    if not login:
        return None

    candidates = {login.strip()}
    if "@" in login:
        candidates.add(login.split("@", 1)[0])

    query = db.query(User).filter(or_(*(User.username == candidate for candidate in candidates)))
    return query.first()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise credentials_error
    except JWTError as exc:
        raise credentials_error from exc

    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def require_roles(allowed_roles: list[str]):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return dependency


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user
