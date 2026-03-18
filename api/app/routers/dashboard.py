from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Lead, LeadActivity, Listing, WAMessage
from app.presenters import activity_to_dict, lead_to_dict

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    total_listings = db.query(Listing).count()
    active_listings = db.query(Listing).filter(Listing.is_active.is_(True)).count()
    hot_listings = db.query(Listing).filter(Listing.is_hot.is_(True)).count()
    total_rumah = (
        db.query(Listing)
        .filter(Listing.is_active.is_(True), Listing.property_type == "rumah")
        .count()
    )
    listings_jual = (
        db.query(Listing)
        .filter(Listing.is_active.is_(True), Listing.listing_type.in_(["jual", "dijual"]))
        .count()
    )
    listings_sewa = (
        db.query(Listing)
        .filter(Listing.is_active.is_(True), Listing.listing_type.in_(["sewa", "disewa"]))
        .count()
    )
    total_leads = db.query(Lead).count()
    pipeline = {
        "inbox": db.query(Lead).filter(Lead.bucket == "inbox").count(),
        "active": db.query(Lead).filter(Lead.bucket == "active").count(),
        "follow_up": db.query(Lead).filter(Lead.bucket == "follow_up").count(),
        "non_lead": db.query(Lead).filter(Lead.bucket == "non_lead").count(),
        "closed": db.query(Lead).filter(Lead.bucket == "closed").count(),
    }
    unread_messages = (
        db.query(WAMessage)
        .filter(WAMessage.direction == "inbound", WAMessage.is_read.is_(False))
        .count()
    )

    due_today = datetime.now(timezone.utc).date()
    tasks = (
        db.query(Lead)
        .filter(
            Lead.next_follow_up_at.isnot(None),
            func.date(Lead.next_follow_up_at) <= due_today,
        )
        .order_by(Lead.next_follow_up_at.asc())
        .limit(10)
        .all()
    )
    recent_activity = (
        db.query(LeadActivity)
        .order_by(LeadActivity.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "summary": {
            "total_listings": total_listings,
            "active_listings": active_listings,
            "hot_listings": hot_listings,
            "total_rumah": total_rumah,
            "listings_jual": listings_jual,
            "listings_sewa": listings_sewa,
            "total_leads": total_leads,
            "unread_messages": unread_messages,
        },
        "pipeline": pipeline,
        "today_tasks": [lead_to_dict(lead) for lead in tasks],
        "recent_activity": [activity_to_dict(activity) for activity in recent_activity],
    }
