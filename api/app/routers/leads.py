from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.ai_recommendations import match_properties
from app.ai_scoring import score_lead
from app.auth import get_current_user
from app.database import get_db
from app.models import Lead, LeadActivity, LeadNote, Listing, WAMessage
from app.presenters import (
    STATUS_TO_BUCKET,
    activity_to_dict,
    lead_to_dict,
    note_to_dict,
    paginate,
    wa_message_to_dict,
)

router = APIRouter(prefix="/leads", tags=["leads"])
PIPELINE_STATUSES = {"inbox", "active", "follow_up", "non_lead", "closed"}


def _lead_queryset(db: Session):
    return db.query(Lead)


def _find_interested_properties(lead: Lead, db: Session) -> list[dict]:
    query = db.query(Listing).filter(Listing.is_active.is_(True))
    if lead.preferred_area:
        term = f"%{lead.preferred_area}%"
        query = query.filter(
            or_(
                Listing.area_location.ilike(term),
                Listing.cluster.ilike(term),
                Listing.sektor.ilike(term),
            )
        )
    if lead.preferred_type:
        query = query.filter(Listing.property_type == lead.preferred_type)
    if lead.budget_min is not None:
        query = query.filter(Listing.price >= lead.budget_min)
    if lead.budget_max is not None:
        query = query.filter(Listing.price <= lead.budget_max)

    listings = query.order_by(Listing.is_hot.desc(), Listing.updated_at.desc()).limit(3).all()
    return [
        {
            "id": listing.id,
            "property_name": listing.title,
            "price": listing.price,
            "district": listing.area_location or listing.cluster or listing.sektor,
        }
        for listing in listings
    ]


def _load_lead_or_404(lead_id: int, db: Session) -> Lead:
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


def _sync_bucket_from_status(lead: Lead):
    if lead.status in STATUS_TO_BUCKET:
        lead.bucket = STATUS_TO_BUCKET[lead.status]


@router.get("/")
def list_leads(
    status: str | None = None,
    source: str | None = None,
    min_score: int | None = Query(None, ge=0, le=100),
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = _lead_queryset(db)

    if status:
        if status in PIPELINE_STATUSES:
            query = query.filter(Lead.bucket == status)
        else:
            query = query.filter(Lead.status == status)
    if source:
        query = query.filter(Lead.source == source)
    if min_score is not None:
        query = query.filter(Lead.ai_score >= min_score)
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Lead.name.ilike(term),
                Lead.phone.ilike(term),
                Lead.email.ilike(term),
                Lead.preferred_area.ilike(term),
            )
        )

    total = query.count()
    leads = (
        query.order_by(
            case((Lead.ai_score.isnot(None), 0), else_=1),
            Lead.ai_score.desc(),
            Lead.created_at.desc(),
        )
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return paginate([lead_to_dict(lead) for lead in leads], total, page, limit)


@router.get("/counts")
def get_lead_counts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    counts = {"inbox": 0, "active": 0, "follow_up": 0, "non_lead": 0, "closed": 0}
    rows = db.query(Lead.bucket, func.count(Lead.id)).group_by(Lead.bucket).all()
    for bucket, count in rows:
        if bucket in counts:
            counts[bucket] = count
    return counts


@router.get("/follow-up-today")
def get_follow_up_today(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    today = datetime.now(timezone.utc).date()
    leads = (
        db.query(Lead)
        .filter(
            Lead.next_follow_up_at.isnot(None),
            func.date(Lead.next_follow_up_at) <= today,
        )
        .order_by(Lead.next_follow_up_at.asc())
        .all()
    )
    return {"data": [lead_to_dict(lead) for lead in leads], "total": len(leads)}


@router.get("/{lead_id}")
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    lead = _load_lead_or_404(lead_id, db)
    interested_properties = _find_interested_properties(lead, db)
    activities = (
        db.query(LeadActivity)
        .filter(LeadActivity.lead_id == lead_id)
        .order_by(LeadActivity.created_at.desc())
        .limit(20)
        .all()
    )
    notes = (
        db.query(LeadNote)
        .filter(LeadNote.lead_id == lead_id)
        .order_by(LeadNote.created_at.desc())
        .limit(20)
        .all()
    )
    messages = (
        db.query(WAMessage)
        .filter(WAMessage.lead_id == lead_id)
        .order_by(WAMessage.created_at.asc())
        .limit(100)
        .all()
    )
    response = lead_to_dict(lead, interested_properties=interested_properties)
    response["activities"] = [activity_to_dict(activity) for activity in activities]
    response["notes_list"] = [note_to_dict(note) for note in notes]
    response["messages"] = [wa_message_to_dict(message) for message in messages]
    return response


@router.post("/")
def create_lead(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    lead = Lead(
        name=payload["name"],
        phone=payload.get("phone"),
        email=payload.get("email"),
        source=payload.get("source", "manual"),
        requirement_text=payload.get("requirement_text"),
        budget_min=payload.get("budget_min"),
        budget_max=payload.get("budget_max"),
        preferred_type=payload.get("preferred_type"),
        preferred_area=payload.get("preferred_area"),
        status=payload.get("status", "new"),
        bucket=payload.get("status") if payload.get("status") in PIPELINE_STATUSES else "inbox",
        notes=payload.get("notes"),
        next_follow_up_at=payload.get("next_follow_up_at"),
    )
    if lead.status not in PIPELINE_STATUSES:
        _sync_bucket_from_status(lead)

    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead_to_dict(lead)


@router.put("/{lead_id}")
def update_lead(
    lead_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    lead = _load_lead_or_404(lead_id, db)
    allowed_fields = {
        "name",
        "phone",
        "email",
        "source",
        "requirement_text",
        "budget_min",
        "budget_max",
        "preferred_type",
        "preferred_area",
        "status",
        "assigned_to",
        "notes",
        "next_follow_up_at",
        "follow_up_reason",
    }
    for key, value in payload.items():
        if key in allowed_fields:
            setattr(lead, key, value)

    if payload.get("status") in PIPELINE_STATUSES:
        lead.bucket = payload["status"]
    else:
        _sync_bucket_from_status(lead)

    lead.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(lead)
    return lead_to_dict(lead)


@router.put("/{lead_id}/bucket")
def update_lead_bucket(
    lead_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    new_bucket = payload.get("bucket")
    if new_bucket not in PIPELINE_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid bucket")

    lead = _load_lead_or_404(lead_id, db)
    lead.bucket = new_bucket
    lead.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(lead)
    return lead_to_dict(lead)


@router.post("/{lead_id}/score")
@router.post("/{lead_id}/ai-score")
async def trigger_ai_score(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    lead = _load_lead_or_404(lead_id, db)
    result = await score_lead(
        {
            "name": lead.name,
            "phone": lead.phone,
            "email": lead.email,
            "budget_min": lead.budget_min,
            "budget_max": lead.budget_max,
            "preferred_area": lead.preferred_area,
            "preferred_type": lead.preferred_type,
            "status": lead.status,
            "source": lead.source,
            "notes": lead.notes,
        }
    )
    lead.ai_score = result["score"]
    lead.ai_score_reason = result["reason"]
    lead.ai_scored_at = datetime.now(timezone.utc)
    lead.updated_at = datetime.now(timezone.utc)
    if lead.ai_score >= 60 and lead.bucket == "inbox":
        lead.bucket = "active"
    db.commit()
    db.refresh(lead)
    return {
        "id": lead.id,
        "ai_score": lead.ai_score,
        "ai_reasoning": lead.ai_score_reason,
        "scored_at": lead.ai_scored_at.isoformat() if lead.ai_scored_at else None,
    }


@router.post("/{lead_id}/activities")
def add_activity(
    lead_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _load_lead_or_404(lead_id, db)
    activity = LeadActivity(
        lead_id=lead_id,
        activity_type=payload.get("activity_type", "note"),
        description=payload.get("description", ""),
        created_by=current_user.id,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity_to_dict(activity)


@router.get("/{lead_id}/notes")
def get_lead_notes(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notes = (
        db.query(LeadNote)
        .filter(LeadNote.lead_id == lead_id)
        .order_by(LeadNote.created_at.desc())
        .all()
    )
    return {"data": [note_to_dict(note) for note in notes], "total": len(notes)}


@router.post("/{lead_id}/notes")
def add_lead_note(
    lead_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _load_lead_or_404(lead_id, db)
    note = LeadNote(
        lead_id=lead_id,
        user_id=current_user.id,
        content=payload.get("content", ""),
        note_type=payload.get("note_type", "manual"),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note_to_dict(note)


@router.delete("/notes/{note_id}")
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    note = db.query(LeadNote).filter(LeadNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"status": "deleted"}


@router.post("/{lead_id}/ai-summary")
async def generate_summary(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    lead = _load_lead_or_404(lead_id, db)
    messages = (
        db.query(WAMessage)
        .filter(WAMessage.lead_id == lead_id)
        .order_by(WAMessage.created_at.asc())
        .all()
    )
    notes = (
        db.query(LeadNote)
        .filter(LeadNote.lead_id == lead_id)
        .order_by(LeadNote.created_at.asc())
        .all()
    )
    from app.ai_recommendations import generate_lead_summary

    result = await generate_lead_summary(
        {
            "name": lead.name,
            "budget_min": lead.budget_min,
            "budget_max": lead.budget_max,
            "preferred_area": lead.preferred_area,
            "preferred_type": lead.preferred_type,
            "status": lead.status,
            "source": lead.source,
        },
        [
            {
                "direction": message.direction,
                "message": message.message or "",
                "created_at": str(message.created_at),
            }
            for message in messages
        ],
        [
            {"content": note.content, "created_at": str(note.created_at)}
            for note in notes
        ],
    )
    lead.ai_summary = result.get("summary", "")
    lead.ai_summary_at = datetime.now(timezone.utc)
    if result.get("follow_up_days") is not None:
        lead.next_follow_up_at = datetime.now(timezone.utc) + timedelta(
            days=result["follow_up_days"]
        )
        lead.follow_up_reason = result.get("recommended_action")
    db.commit()
    return result


@router.post("/{lead_id}/ai-recommend")
async def get_recommendations(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    lead = _load_lead_or_404(lead_id, db)
    return {
        "lead_id": lead.id,
        "recommendations": await match_properties(
            {
                "preferred_areas": [lead.preferred_area] if lead.preferred_area else [],
                "property_types": [lead.preferred_type] if lead.preferred_type else [],
                "budget_min": lead.budget_min,
                "budget_max": lead.budget_max,
            },
            db,
        ),
    }


@router.get("/{lead_id}/timeline")
def get_timeline(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _load_lead_or_404(lead_id, db)
    timeline = []
    notes = db.query(LeadNote).filter(LeadNote.lead_id == lead_id).all()
    messages = db.query(WAMessage).filter(WAMessage.lead_id == lead_id).all()
    activities = db.query(LeadActivity).filter(LeadActivity.lead_id == lead_id).all()

    for note in notes:
        item = note_to_dict(note)
        item["type"] = "note"
        timeline.append(item)
    for message in messages:
        item = wa_message_to_dict(message)
        item["type"] = "message"
        timeline.append(item)
    for activity in activities:
        item = activity_to_dict(activity)
        item["type"] = "activity"
        timeline.append(item)

    timeline.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return {"data": timeline, "total": len(timeline)}
