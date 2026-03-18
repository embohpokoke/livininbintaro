from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Lead, LeadActivity, WAMessage, WATemplate
from app.fonnte_service import send_wa_message, normalize_phone, OCHA_PHONE
from datetime import datetime
import json, logging

logger = logging.getLogger("webhook")
router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/fonnte")
async def fonnte_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive incoming WhatsApp messages from Fonnte."""
    try:
        body = await request.json()
    except Exception:
        body = dict(await request.form())

    logger.info(f"Fonnte webhook: {json.dumps(body, default=str)[:1000]}")

    sender = body.get("sender", "")
    name = body.get("name", body.get("pushname", ""))
    message = body.get("message", "")
    msg_type = body.get("type", "text")
    fonnte_id = body.get("id", "")
    is_group = body.get("isGroup", False)

    # Skip group messages
    if is_group:
        return {"status": "skipped", "reason": "group message"}

    if not sender or not message:
        return {"status": "ignored", "reason": "no phone or message"}

    phone = normalize_phone(sender)

    # Find or create lead
    lead = db.query(Lead).filter(Lead.phone == phone).first()
    is_new_lead = False

    if not lead:
        lead = Lead(
            name=name or f"WA-{phone[-4:]}",
            phone=phone,
            source="whatsapp",
            status="new",
            bucket="inbox",
            notes=f"Pesan pertama: {message[:500]}",
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        is_new_lead = True

    # Update last contacted
    lead.last_contacted_at = datetime.utcnow()
    if lead.name and lead.name.startswith("WA-") and name:
        lead.name = name

    # Store inbound message
    wa_msg = WAMessage(
        lead_id=lead.id,
        phone=phone,
        sender_name=name,
        message=message,
        direction="inbound",
        message_type=msg_type,
        fonnte_message_id=fonnte_id,
    )
    db.add(wa_msg)

    # Log activity
    activity = LeadActivity(
        lead_id=lead.id,
        activity_type="wa_message",
        description=f"WA inbound: {message[:500]}",
    )
    db.add(activity)
    db.commit()

    # Send welcome message if new lead
    if is_new_lead and not lead.welcome_sent:
        template = db.query(WATemplate).filter(
            WATemplate.trigger_type == "welcome",
            WATemplate.is_active == True
        ).first()

        if template:
            welcome_text = template.message_template.replace("{name}", name or "")
            await send_wa_message(phone, welcome_text)

            # Store outbound message
            out_msg = WAMessage(
                lead_id=lead.id,
                phone=phone,
                message=welcome_text,
                direction="outbound",
                message_type="text",
            )
            db.add(out_msg)
            lead.welcome_sent = True
            db.commit()

    # Notify Ocha about new lead
    if is_new_lead:
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        notification = f"""🏠 *Lead Baru!*

Nama: {lead.name}
HP: {phone}
Pesan: {message[:200]}
Waktu: {now_str}

Dashboard: https://livininbintaro.my.id/"""
        await send_wa_message(OCHA_PHONE, notification)

    return {"status": "ok", "lead_id": lead.id, "is_new": is_new_lead}
