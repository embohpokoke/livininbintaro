"""
Livininbintaro CRM — GOWA WhatsApp API Client
Sends messages via GOWA at port 3004 (Ocha device)
"""

import httpx
import logging
from config import GOWA_URL, GOWA_AUTH

logger = logging.getLogger("gowa")

GOWA_DEVICE_ID = "d30842fa-1688-49a8-be58-ca7587c3c8ba"  # Ocha


async def send_message(phone: str, message: str) -> dict:
    """Send a WhatsApp text message via GOWA API."""
    url = f"{GOWA_URL}/send/message"
    payload = {"phone": phone, "message": message}
    headers = {"X-Device-Id": GOWA_DEVICE_ID}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers, auth=GOWA_AUTH)
            result = resp.json()
            logger.info(f"GOWA send to {phone}: status={resp.status_code} result={result}")
            return {"status": "sent", "gowa_response": result}
    except Exception as e:
        logger.error(f"GOWA send error to {phone}: {e}")
        return {"status": "error", "error": str(e)}
