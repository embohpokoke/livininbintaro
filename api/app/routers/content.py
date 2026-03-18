from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import ContentCalendar
from app.presenters import serialize_datetime

router = APIRouter(prefix="/content", tags=["content"])


def _content_to_dict(item: ContentCalendar) -> dict:
    return {
        "id": item.id,
        "post_type": item.post_type,
        "content": item.content,
        "scheduled_date": item.scheduled_date.isoformat() if item.scheduled_date else None,
        "status": item.status,
        "created_at": serialize_datetime(item.created_at),
        "updated_at": serialize_datetime(item.updated_at),
    }


def _parse_scheduled_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


@router.get("/")
def list_content(
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(ContentCalendar)
    if status:
        query = query.filter(ContentCalendar.status == status)
    items = query.order_by(ContentCalendar.scheduled_date.asc()).all()
    return {"data": [_content_to_dict(item) for item in items], "total": len(items)}


@router.post("/")
def create_content(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = ContentCalendar(
        post_type=payload["post_type"],
        content=payload["content"],
        scheduled_date=_parse_scheduled_date(payload.get("scheduled_date")),
        status=payload.get("status", "draft"),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _content_to_dict(item)


@router.put("/{content_id}")
def update_content(
    content_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = db.query(ContentCalendar).filter(ContentCalendar.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    for key in {"post_type", "content", "status"}:
        if key in payload:
            setattr(item, key, payload[key])
    if "scheduled_date" in payload:
        item.scheduled_date = _parse_scheduled_date(payload["scheduled_date"])
    db.commit()
    db.refresh(item)
    return _content_to_dict(item)
