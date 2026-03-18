#!/usr/bin/env python3
"""Batch AI scoring for leads — runs every 6 hours via cron."""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(
    filename='/var/log/livininbintaro/ai_scoring.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Also log to stdout for manual runs
if sys.stdout.isatty():
    logging.getLogger().addHandler(logging.StreamHandler())

DATABASE_URL = "postgresql://livin:L1v1n!B1nt4r0_2026@localhost:5432/livininbintaro"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


async def run_batch_scoring():
    """Score unscored leads or leads scored more than 7 days ago."""
    sys.path.insert(0, '/var/www/livininbintaro/api')
    from app.ai_scoring import score_lead

    session = Session()
    try:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        result = session.execute(text("""
            SELECT id, name, phone, budget_min, budget_max, preferred_area,
                   preferred_type, status, source, notes, bucket
            FROM leads
            WHERE (ai_scored_at IS NULL OR ai_scored_at < :cutoff)
              AND bucket NOT IN ('non_lead', 'closed')
            ORDER BY created_at DESC
            LIMIT 50
        """), {"cutoff": seven_days_ago})

        leads = result.fetchall()
        logging.info(f"Found {len(leads)} leads to score")

        scored = 0
        for lead in leads:
            try:
                lead_data = {
                    "name": lead.name,
                    "phone": lead.phone,
                    "budget_min": lead.budget_min,
                    "budget_max": lead.budget_max,
                    "preferred_area": lead.preferred_area,
                    "preferred_type": lead.preferred_type,
                    "status": lead.status,
                    "source": lead.source,
                    "notes": lead.notes,
                }

                ai_result = await score_lead(lead_data)

                update_query = text("""
                    UPDATE leads
                    SET ai_score = :score,
                        ai_score_reason = :reason,
                        ai_scored_at = :scored_at,
                        bucket = CASE
                            WHEN bucket = 'inbox' AND :score >= 60 THEN 'active'
                            ELSE bucket
                        END,
                        updated_at = NOW()
                    WHERE id = :id
                """)
                session.execute(update_query, {
                    "score": ai_result["score"],
                    "reason": ai_result["reason"],
                    "scored_at": datetime.utcnow(),
                    "id": lead.id
                })
                session.commit()
                scored += 1
                logging.info(f"Scored lead {lead.id} ({lead.name}): {ai_result['score']} ({ai_result['tier']})")

            except Exception as e:
                logging.error(f"Failed to score lead {lead.id}: {e}")
                session.rollback()
                continue

        logging.info(f"Batch scoring complete: {scored}/{len(leads)} leads scored")

    except Exception as e:
        logging.error(f"Batch scoring failed: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(run_batch_scoring())
