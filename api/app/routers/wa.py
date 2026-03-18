import hmac
import hashlib
import json
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.fonnte_service import OCHA_PHONE, normalize_phone, send_wa_message
from app.models import Lead, LeadActivity, WAMessage, WATemplate
from app.presenters import paginate, wa_message_to_dict

logger = logging.getLogger("wa")
router = APIRouter(prefix="/wa", tags=["whatsapp"])
webhook_router = APIRouter(prefix="/webhook", tags=["webhooks"])


def verify_gowa_signature(secret: str, body: bytes, signature: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    sig_hex = signature.replace("sha256=", "")
    return hmac.compare_digest(expected, sig_hex)


def _load_lead_or_404(lead_id: int, db: Session) -> Lead:
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


async def _handle_gowa_payload(raw_body: bytes, request: Request, db: Session):
    signature = request.headers.get("X-Hub-Signature-256", "")
    if signature and not verify_gowa_signature(
        settings.GOWA_LIVININ_SECRET, raw_body, signature
    ):
        logger.warning("GOWA webhook: invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    logger.info("GOWA webhook payload: %s", json.dumps(data, default=str)[:1000])
    event = data.get("event")
    payload = data.get("payload", {})
    if event != "message":
        return {"status": "ignored", "event": event}

    from_jid = payload.get("from", "")
    sender = from_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")
    is_from_me = payload.get("fromMe", False)
    push_name = payload.get("pushName", "")
    msg_obj = payload.get("message", {})
    message_text = (
        msg_obj.get("conversation")
        or msg_obj.get("extendedTextMessage", {}).get("text")
        or payload.get("message")
        or "[media]"
    )
    media_url = payload.get("media_url")
    phone = normalize_phone(sender)
    direction = "outbound" if is_from_me else "inbound"

    lead = db.query(Lead).filter(Lead.phone == phone).first()
    is_new_lead = False
    if not lead and not is_from_me:
        lead = Lead(
            name=push_name or f"WA-{phone[-4:]}",
            phone=phone,
            source="whatsapp",
            status="new",
            bucket="inbox",
            notes=f"Pesan pertama via GOWA: {message_text[:500]}",
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        is_new_lead = True

    if lead:
        wa_message = WAMessage(
            lead_id=lead.id,
            phone=phone,
            sender_name=push_name if not is_from_me else None,
            message=message_text,
            direction=direction,
            message_type="text",
            media_url=media_url,
        )
        db.add(wa_message)
        db.add(
            LeadActivity(
                lead_id=lead.id,
                activity_type=f"wa_{direction}",
                description=f"GOWA {direction}: {message_text[:500]}",
            )
        )
        if not is_from_me:
            from datetime import datetime, timezone

            lead.last_contacted_at = datetime.now(timezone.utc)
        db.commit()

        if is_new_lead:
            notification = (
                "*Lead Baru (WA)!*\n\n"
                f"Nama: {lead.name}\n"
                f"HP: {phone}\n"
                f"Pesan: {message_text[:200]}\n\n"
                "Dashboard: https://livininbintaro.my.id/dashboard"
            )
            await send_wa_message(OCHA_PHONE, notification)

    return {"status": "ok", "direction": direction, "lead_id": lead.id if lead else None}


@webhook_router.post("/gowa")
async def gowa_webhook(request: Request, db: Session = Depends(get_db)):
    return await _handle_gowa_payload(await request.body(), request, db)


@router.post("/gowa-webhook", include_in_schema=False)
async def legacy_gowa_webhook(request: Request, db: Session = Depends(get_db)):
    return await _handle_gowa_payload(await request.body(), request, db)


@router.get("/messages/{lead_id}")
async def get_lead_messages(
    lead_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _load_lead_or_404(lead_id, db)
    query = db.query(WAMessage).filter(WAMessage.lead_id == lead_id)
    total = query.count()
    messages = (
        query.order_by(WAMessage.created_at.asc()).offset(offset).limit(limit).all()
    )
    db.query(WAMessage).filter(
        WAMessage.lead_id == lead_id,
        WAMessage.direction == "inbound",
        WAMessage.is_read.is_(False),
    ).update({"is_read": True})
    db.commit()
    return {
        "data": [wa_message_to_dict(message) for message in messages],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.post("/send")
async def send_message(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    lead_id = payload.get("lead_id")
    if not lead_id:
        raise HTTPException(status_code=422, detail="lead_id is required")
    lead = _load_lead_or_404(lead_id, db)
    message_text = payload.get("message") or payload.get("message_text")
    media_url = payload.get("media_url")
    if not message_text:
        raise HTTPException(status_code=400, detail="Message is required")

    result = await send_wa_message(lead.phone, message_text, media_url)
    wa_message = WAMessage(
        lead_id=lead.id,
        phone=lead.phone,
        message=message_text,
        direction="outbound",
        message_type="image" if media_url else "text",
        media_url=media_url,
    )
    db.add(wa_message)
    db.add(
        LeadActivity(
            lead_id=lead.id,
            activity_type="wa_outbound",
            description=f"WA sent: {message_text[:500]}",
            created_by=current_user.id,
        )
    )
    db.commit()
    db.refresh(wa_message)
    return {"status": "sent", "message": wa_message_to_dict(wa_message), "provider": result}


@router.post("/messages/{lead_id}", include_in_schema=False)
async def send_message_legacy(
    lead_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    payload["lead_id"] = lead_id
    return await send_message(payload, db, current_user)


@router.get("/templates")
async def get_templates(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    templates = db.query(WATemplate).all()
    return {
        "data": [
            {
                "id": template.id,
                "name": template.name,
                "trigger_type": template.trigger_type,
                "message_template": template.message_template,
                "is_active": template.is_active,
            }
            for template in templates
        ],
        "total": len(templates),
    }


@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    count = (
        db.query(WAMessage)
        .filter(WAMessage.direction == "inbound", WAMessage.is_read.is_(False))
        .count()
    )
    return {"unread": count}
