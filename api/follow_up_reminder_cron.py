#!/usr/bin/env python3
"""Send daily follow-up reminders to Ocha via WA — runs at 08:00 WIB (01:00 UTC)."""

import asyncio
import logging
from datetime import datetime, date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(
    filename='/var/log/livininbintaro/follow_up_reminder.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://livin:L1v1n!B1nt4r0_2026@172.17.0.2:5432/livininbintaro"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

import sys
sys.path.insert(0, '/var/www/livininbintaro/api')
from app.fonnte_service import send_wa_message, OCHA_PHONE


async def send_reminders():
    session = Session()
    today = date.today()

    leads = session.execute(text("""
        SELECT name, phone, follow_up_reason, ai_score, bucket
        FROM leads
        WHERE DATE(next_follow_up_at) <= :today
          AND bucket IN ('inbox', 'active', 'follow_up')
        ORDER BY ai_score DESC NULLS LAST
        LIMIT 10
    """), {"today": today}).fetchall()

    if not leads:
        logger.info("No follow-ups needed today")
        return

    lines = [f"*Follow Up Hari Ini ({today.strftime('%d %b %Y')})*\n"]
    for i, l in enumerate(leads, 1):
        score = l.ai_score or 0
        score_emoji = "H" if score >= 80 else "W" if score >= 60 else "-"
        lines.append(f"{i}. [{score_emoji}{score}] *{l.name}* ({l.phone or '-'})")
        if l.follow_up_reason:
            lines.append(f"   > {l.follow_up_reason}")

    lines.append(f"\nTotal: {len(leads)} leads perlu follow up")
    lines.append(f"Cek detail: https://livininbintaro.my.id")

    message = "\n".join(lines)
    result = await send_wa_message(OCHA_PHONE, message)
    logger.info(f"Reminder sent to Ocha: {result}")

    session.close()


if __name__ == "__main__":
    logger.info("Starting follow-up reminder cron...")
    asyncio.run(send_reminders())
