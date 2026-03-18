from math import ceil
from typing import Any

from app.models import Lead, LeadActivity, LeadNote, Listing, WAMessage

PIPELINE_BUCKETS = ("inbox", "active", "follow_up", "non_lead", "closed")
STATUS_TO_BUCKET = {
    "new": "inbox",
    "contacted": "follow_up",
    "appointment": "active",
    "showing": "active",
    "negotiation": "active",
    "closed_won": "closed",
    "closed_lost": "closed",
}


def serialize_datetime(value):
    return value.isoformat() if value else None


def normalize_listing_type(value: str | None) -> str | None:
    if value in {"jual", "dijual"}:
        return "dijual"
    if value in {"sewa", "disewa"}:
        return "disewa"
    return value


def get_listing_district(listing: Listing) -> str | None:
    return listing.area_location or listing.cluster or listing.sektor


def listing_to_dict(listing: Listing, include_internal: bool = False) -> dict[str, Any]:
    data = {
        "id": listing.id,
        "slug": listing.slug,
        "listing_code": listing.cpa_code or listing.slug or str(listing.id),
        "property_name": listing.title,
        "property_type": listing.property_type,
        "transaction_type": normalize_listing_type(listing.listing_type),
        "price": listing.price,
        "price_label": listing.price_label,
        "bedrooms": listing.bedrooms,
        "bathrooms": listing.bathrooms,
        "land_area": listing.land_area,
        "building_area": listing.building_area,
        "address": listing.address,
        "district": get_listing_district(listing),
        "city": None,
        "province": None,
        "description": listing.description,
        "facilities": [],
        "images": listing.images or [],
        "drive_folder_id": listing.drive_folder_id,
        "drive_link": listing.drive_link,
        "is_active": listing.is_active,
        "is_hot": listing.is_hot,
        "created_at": serialize_datetime(listing.created_at),
        "updated_at": serialize_datetime(listing.updated_at),
    }
    if include_internal:
        data.update(
            {
                "title": listing.title,
                "area_location": listing.area_location,
                "cluster": listing.cluster,
                "sektor": listing.sektor,
                "summary_client": listing.summary_client,
                "summary_ma": listing.summary_ma,
                "hot_reason": listing.hot_reason,
                "hot_note": listing.hot_note,
                "hot_date": serialize_datetime(listing.hot_date),
            }
        )
    return data


def get_lead_pipeline_status(lead: Lead) -> str:
    if lead.bucket in PIPELINE_BUCKETS:
        return lead.bucket
    return STATUS_TO_BUCKET.get(lead.status or "new", "inbox")


def lead_to_dict(lead: Lead, interested_properties: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "id": lead.id,
        "name": lead.name,
        "phone": lead.phone,
        "email": lead.email,
        "source": lead.source,
        "status": get_lead_pipeline_status(lead),
        "workflow_status": lead.status,
        "requirement_text": lead.requirement_text,
        "budget_min": lead.budget_min,
        "budget_max": lead.budget_max,
        "preferred_type": lead.preferred_type,
        "preferred_area": lead.preferred_area,
        "assigned_to": lead.assigned_to,
        "notes": lead.notes,
        "ai_score": lead.ai_score,
        "ai_reasoning": lead.ai_score_reason,
        "ai_scored_at": serialize_datetime(lead.ai_scored_at),
        "ai_summary": lead.ai_summary,
        "last_contacted_at": serialize_datetime(lead.last_contacted_at),
        "next_follow_up_at": serialize_datetime(lead.next_follow_up_at),
        "follow_up_reason": lead.follow_up_reason,
        "interested_properties": interested_properties or [],
        "created_at": serialize_datetime(lead.created_at),
        "updated_at": serialize_datetime(lead.updated_at),
    }


def activity_to_dict(activity: LeadActivity) -> dict[str, Any]:
    return {
        "id": activity.id,
        "lead_id": activity.lead_id,
        "activity_type": activity.activity_type,
        "description": activity.description,
        "created_by": activity.created_by,
        "created_at": serialize_datetime(activity.created_at),
    }


def note_to_dict(note: LeadNote) -> dict[str, Any]:
    return {
        "id": note.id,
        "lead_id": note.lead_id,
        "user_id": note.user_id,
        "content": note.content,
        "note_type": note.note_type,
        "created_at": serialize_datetime(note.created_at),
    }


def wa_message_to_dict(message: WAMessage) -> dict[str, Any]:
    return {
        "id": message.id,
        "lead_id": message.lead_id,
        "phone": message.phone,
        "sender_name": message.sender_name,
        "message_text": message.message,
        "message": message.message,
        "direction": message.direction,
        "message_type": message.message_type,
        "media_url": message.media_url,
        "is_read": message.is_read,
        "timestamp": serialize_datetime(message.created_at),
        "created_at": serialize_datetime(message.created_at),
    }


def paginate(data: list[Any], total: int, page: int, limit: int) -> dict[str, Any]:
    total_pages = ceil(total / limit) if limit else 1
    return {
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
    }
