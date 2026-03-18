"""
Livininbintaro CRM — WA Messages Router
GET  /wa/messages/{lead_id}?limit=100  → fetch chat history
POST /wa/messages/{lead_id}            → send WA message to lead via GOWA
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import logging

from db import get_db, normalize_phone
from gowa_client import send_message

logger = logging.getLogger("wa_messages")
router = APIRouter(prefix="/wa/messages", tags=["wa"])

GOWA_DEVICE_ID = "d30842fa-1688-49a8-be58-ca7587c3c8ba"  # Ocha's device


@router.get("/{lead_id}")
async def get_wa_messages(lead_id: int, limit: int = 100):
    """Fetch WA chat history for a lead."""
    conn = get_db()
    try:
        lead = conn.execute(
            "SELECT id, name, phone FROM crm.leads WHERE id = ?", (lead_id,)
        ).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        messages = conn.execute(
            """SELECT id, message, direction, message_type, media_url, created_at
               FROM crm.wa_messages
               WHERE lead_id = ?
               ORDER BY created_at ASC
               LIMIT ?""",
            (lead_id, limit),
        ).fetchall()

        return {
            "lead_id": lead_id,
            "lead_name": lead["name"],
            "lead_phone": lead["phone"],
            "messages": [
                {
                    "id": m["id"],
                    "message": m["message"],
                    "direction": m["direction"],
                    "message_type": m["message_type"] or "text",
                    "media_url": m["media_url"],
                    "created_at": str(m["created_at"]),
                }
                for m in messages
            ],
            "total": len(messages),
        }
    finally:
        conn.close()


@router.post("/{lead_id}")
async def send_wa_message(lead_id: int, body: dict):
    """Send a WA message to a lead via GOWA."""
    message = (body.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    conn = get_db()
    try:
        lead = conn.execute(
            "SELECT id, name, phone FROM crm.leads WHERE id = ?", (lead_id,)
        ).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        phone = lead["phone"]
        if not phone:
            raise HTTPException(status_code=400, detail="Lead has no phone number")

        phone = normalize_phone(phone)

        # Send via GOWA
        gowa_result = await send_message(phone, message)

        if gowa_result.get("status") == "error":
            logger.error(f"GOWA send failed for lead {lead_id}: {gowa_result}")
            raise HTTPException(status_code=502, detail="GOWA send failed: " + gowa_result.get("error", "unknown"))

        # Log to DB
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT INTO crm.wa_messages
               (lead_id, phone, message, direction, message_type, created_at)
               VALUES (?, ?, ?, 'outbound', 'text', ?)""",
            (lead_id, phone, message, now),
        )
        conn.commit()

        return {
            "status": "sent",
            "lead_id": lead_id,
            "phone": phone,
            "gowa": gowa_result,
        }
    finally:
        conn.close()
