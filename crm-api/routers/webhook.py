"""
Livininbintaro CRM — GOWA Webhook Receiver
POST /webhook/wa-incoming
Handles incoming WhatsApp messages from GOWA at port 3002.
"""

from fastapi import APIRouter, Request, BackgroundTasks
from datetime import datetime, timedelta
import json
import hmac
import hashlib
import logging

from db import get_db, normalize_phone
from config import GOWA_WEBHOOK_SECRET, AGENT_PHONE
from ai_scoring import score_lead
from gowa_client import send_message

logger = logging.getLogger("webhook")
router = APIRouter(tags=["webhook"])


def verify_signature(secret: str, body: bytes, signature: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    sig_hex = signature.replace("sha256=", "")
    return hmac.compare_digest(expected, sig_hex)


@router.post("/webhook/wa-incoming")
async def wa_incoming(request: Request, background_tasks: BackgroundTasks):
    raw_body = await request.body()

    # Verify signature if provided
    signature = request.headers.get("X-Hub-Signature-256", "")
    if signature:
        if not verify_signature(GOWA_WEBHOOK_SECRET, raw_body, signature):
            logger.warning("Webhook: invalid signature")
            return {"status": "unauthorized"}

    try:
        data = json.loads(raw_body)
    except Exception:
        return {"status": "error", "reason": "invalid json"}

    logger.info(f"Webhook received: {json.dumps(data, default=str)[:1000]}")

    event = data.get("event")
    payload = data.get("payload", {})

    if event == "message":
        from_jid = payload.get("from", "")
        chat_jid = payload.get("chat_id", from_jid)
        is_from_me = payload.get("is_from_me", False)
        push_name = payload.get("from_name", "")
        # GOWA payload: text is in payload.body
        message_text = (
            payload.get("body")
            or payload.get("caption")
            or "[media]"
        )

        # outbound: log ke recipient (chat_id), inbound: log ke sender (from)
        target_jid = chat_jid if is_from_me else from_jid
        sender = target_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")
        phone = normalize_phone(sender)
        if not phone:
            return {"status": "ignored", "reason": "no phone"}

        direction = "outbound" if is_from_me else "inbound"

        conn = get_db()
        try:
            lead = conn.execute("SELECT * FROM leads WHERE phone = ?", (phone,)).fetchone()
            is_new_lead = False
            lead_id = None

            if lead:
                lead_id = lead["id"]
                # Update last activity
                now = datetime.utcnow().isoformat()
                conn.execute(
                    "UPDATE leads SET last_contacted_at = ?, updated_at = ? WHERE id = ?",
                    (now, now, lead_id),
                )
            elif not is_from_me:
                # Auto-create lead for new inbound sender
                now = datetime.utcnow().isoformat()
                sla_deadline = (datetime.utcnow() + timedelta(hours=1)).isoformat()
                cur = conn.execute("""
                    INSERT INTO leads (name, phone, source, bucket, status,
                        notes, sla_deadline, created_at, updated_at)
                    VALUES (?, ?, 'whatsapp', 'inbox', 'new', ?, ?, ?, ?)
                """, (
                    push_name or f"WA-{phone[-4:]}",
                    phone,
                    f"Pesan pertama via GOWA: {message_text[:500]}",
                    sla_deadline,
                    now, now,
                ))
                conn.commit()
                lead_id = cur.lastrowid
                is_new_lead = True

                # Log creation activity
                conn.execute("""
                    INSERT INTO lead_activities (lead_id, activity_type, description)
                    VALUES (?, 'lead_created', ?)
                """, (lead_id, f"Auto-created from WhatsApp message: {push_name or phone}"))

            if lead_id:
                # Store WA message
                conn.execute("""
                    INSERT INTO wa_messages (lead_id, phone, sender_name, message, direction, message_type)
                    VALUES (?, ?, ?, ?, ?, 'text')
                """, (lead_id, phone, push_name if not is_from_me else None, message_text, direction))

                # Log activity
                conn.execute("""
                    INSERT INTO lead_activities (lead_id, activity_type, description)
                    VALUES (?, ?, ?)
                """, (lead_id, f"wa_{direction}", f"GOWA {direction}: {message_text[:500]}"))

                conn.commit()

            # Background tasks for new leads
            if is_new_lead and lead_id:
                # AI score
                lead_data = {
                    "name": push_name or f"WA-{phone[-4:]}",
                    "phone": phone, "source": "whatsapp", "status": "new",
                    "notes": message_text[:500], "message": message_text,
                }
                background_tasks.add_task(_bg_score_new_lead, lead_id, lead_data)

                # Notify agent
                background_tasks.add_task(_notify_agent_new_lead, push_name or phone, phone, message_text)

            return {
                "status": "ok", "direction": direction,
                "lead_id": lead_id, "is_new": is_new_lead,
            }

        finally:
            conn.close()

    if event in ("message.ack", "message.revoked", "message.edited"):
        return {"status": "ok", "event": event}

    return {"status": "ignored", "event": event}


async def _bg_score_new_lead(lead_id: int, lead_data: dict):
    """Background: AI-score new lead and auto-qualify."""
    try:
        result = await score_lead(lead_data)
        conn = get_db()
        now = datetime.utcnow().isoformat()

        updates = {
            "ai_score": result["score"],
            "ai_score_reason": result["reason"],
            "ai_scored_at": now,
            "updated_at": now,
        }
        if result["score"] >= 70:
            updates["bucket"] = "qualified"

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(
            f"UPDATE leads SET {set_clause} WHERE id = ?",
            list(updates.values()) + [lead_id],
        )
        conn.execute("""
            INSERT INTO lead_activities (lead_id, activity_type, description)
            VALUES (?, 'ai_scored', ?)
        """, (lead_id, f"AI Score: {result['score']} ({result['tier']}). {result['reason']}"))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"BG scoring error for lead {lead_id}: {e}")


async def _notify_agent_new_lead(name: str, phone: str, message: str):
    """Background: notify agent of new WhatsApp lead."""
    try:
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        notification = (
            f"*Lead Baru (WA)!*\n\n"
            f"Nama: {name}\n"
            f"HP: {phone}\n"
            f"Pesan: {message[:200]}\n"
            f"Waktu: {now_str}\n"
            f"SLA: 1 jam\n\n"
            f"Segera follow-up!"
        )
        await send_message(AGENT_PHONE, notification)
    except Exception as e:
        logger.error(f"Notify agent error: {e}")
