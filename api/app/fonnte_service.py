import httpx
import os
import logging

FONNTE_TOKEN = os.getenv("FONNTE_TOKEN", "bhBk3VPqvr5MWT1Lb4QV")
FONNTE_SEND_URL = "https://api.fonnte.com/send"
OCHA_PHONE = "62811309991"

logger = logging.getLogger(__name__)


async def send_wa_message(phone: str, message: str, media_url: str = None) -> dict:
    """Send WhatsApp message via Fonnte API."""
    headers = {"Authorization": FONNTE_TOKEN}
    payload = {
        "target": phone,
        "message": message,
        "countryCode": "62",
    }
    if media_url:
        payload["url"] = media_url
        payload["type"] = "image"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(FONNTE_SEND_URL, headers=headers, data=payload)
            result = response.json()
            logger.info(f"Fonnte send to {phone}: {result}")
            return result
    except Exception as e:
        logger.error(f"Fonnte send failed: {e}")
        return {"status": False, "reason": str(e)}


def send_wa_message_sync(phone: str, message: str) -> bool:
    """Synchronous version for use in cron jobs."""
    import requests
    try:
        headers = {"Authorization": FONNTE_TOKEN}
        data = {"target": phone, "message": message, "countryCode": "62"}
        resp = requests.post(FONNTE_SEND_URL, headers=headers, data=data, timeout=10)
        logger.info(f"Fonnte sync send to {phone}: {resp.status_code}")
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"Fonnte sync send failed: {e}")
        return False


def normalize_phone(phone: str) -> str:
    """Normalize phone number to 628xxx format."""
    phone = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    if phone.startswith("08"):
        phone = "628" + phone[2:]
    elif phone.startswith("8") and not phone.startswith("62"):
        phone = "628" + phone[1:]
    elif not phone.startswith("62"):
        phone = "62" + phone
    return phone
