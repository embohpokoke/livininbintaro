#!/usr/bin/env python3
"""Auto follow-up messages via Fonnte — runs daily at 10:00 WIB (03:00 UTC)."""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(
    filename='/var/log/livininbintaro/follow_up.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://livin:L1v1n!B1nt4r0_2026@172.17.0.2:5432/livininbintaro"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

import sys
sys.path.insert(0, '/var/www/livininbintaro/api')
from app.fonnte_service import send_wa_message


async def run_follow_ups():
    session = Session()
    now = datetime.utcnow()
    total_sent = 0

    follow_up_rules = [
        {"days": 1, "type": "follow_up_d1", "flag": "follow_up_d1_sent"},
        {"days": 7, "type": "follow_up_d7", "flag": "follow_up_d7_sent"},
        {"days": 14, "type": "follow_up_d14", "flag": "follow_up_d14_sent"},
    ]

    for rule in follow_up_rules:
        cutoff = now - timedelta(days=rule["days"])
        cutoff_end = cutoff - timedelta(hours=24)

        leads = session.execute(text(f"""
            SELECT l.id, l.name, l.phone
            FROM leads l
            WHERE l.{rule['flag']} = FALSE
              AND l.welcome_sent = TRUE
              AND l.bucket IN ('inbox', 'follow_up')
              AND l.created_at BETWEEN :cutoff_end AND :cutoff
              AND l.phone IS NOT NULL
        """), {"cutoff": cutoff, "cutoff_end": cutoff_end}).fetchall()

        if not leads:
            continue

        template = session.execute(text("""
            SELECT message_template FROM wa_templates
            WHERE trigger_type = :type AND is_active = TRUE LIMIT 1
        """), {"type": rule["type"]}).fetchone()

        if not template:
            logger.warning(f"No active template for {rule['type']}")
            continue

        for lead in leads:
            try:
                msg = template.message_template.replace("{name}", lead.name or "")
                result = await send_wa_message(lead.phone, msg)

                if result.get("status"):
                    session.execute(text(f"""
                        UPDATE leads SET {rule['flag']} = TRUE, last_contacted_at = NOW()
                        WHERE id = :id
                    """), {"id": lead.id})

                    session.execute(text("""
                        INSERT INTO wa_messages (lead_id, phone, message, direction)
                        VALUES (:lead_id, :phone, :message, 'outbound')
                    """), {"lead_id": lead.id, "phone": lead.phone, "message": msg})

                    session.commit()
                    total_sent += 1
                    logger.info(f"Follow-up {rule['type']} sent to {lead.name} ({lead.phone})")

            except Exception as e:
                logger.error(f"Follow-up failed for lead {lead.id}: {e}")
                session.rollback()

    session.close()
    logger.info(f"Follow-up run complete. Total sent: {total_sent}")


if __name__ == "__main__":
    logger.info("Starting follow-up cron run...")
    asyncio.run(run_follow_ups())
