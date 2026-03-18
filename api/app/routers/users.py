from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserOut
from app.auth import get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserOut)
def get_me(user=Depends(get_current_user)):
    return user

@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), user=Depends(require_admin)):
    return db.query(User).all()
