"""
Livininbintaro CRM — Background Schedulers
- SLA Checker: every 60 min, BATCH alert (1 message max)
- Follow-up Checker: every 60 min, BATCH reminder (1 message max)
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import get_db
from config import AGENT_PHONE
from gowa_client import send_message

logger = logging.getLogger("scheduler")
scheduler = AsyncIOScheduler()

# Track last alert time to prevent spam
_last_sla_alert = None
_last_followup_alert = None
SLA_COOLDOWN_HOURS = 4       # max 1 SLA alert per 4 hours
FOLLOWUP_COOLDOWN_HOURS = 4  # max 1 followup alert per 4 hours


async def check_sla():
    """Check SLA breaches — ONE batched WA message, max 1x per 4 hours."""
    global _last_sla_alert
    now = datetime.now(timezone.utc)

    # Cooldown check
    if _last_sla_alert and (now - _last_sla_alert).total_seconds() < SLA_COOLDOWN_HOURS * 3600:
        logger.debug("SLA check: cooldown active, skip")
        return

    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT id, name, phone, bucket, sla_deadline
            FROM crm.leads
            WHERE sla_deadline IS NOT NULL
              AND sla_deadline < ?
              AND bucket NOT IN ('closed', 'nurture')
            ORDER BY sla_deadline
        """, (now.isoformat(),)).fetchall()

        if not rows:
            return

        logger.info(f"SLA check: {len(rows)} leads breached")

        # ONE batched message
        lines = [f"⚠️ *SLA Alert — {len(rows)} leads perlu follow-up:*\n"]
        for i, lead in enumerate(rows[:10], 1):
            try:
                deadline = datetime.fromisoformat(str(lead["sla_deadline"]))
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                hours = round((now - deadline).total_seconds() / 3600, 1)
            except Exception:
                hours = "?"
            lines.append(f"{i}. {lead['name']} ({lead['phone'] or '-'}) — {hours}h overdue [{lead['bucket']}]")

        if len(rows) > 10:
            lines.append(f"...dan {len(rows) - 10} lead lainnya")

        await send_message(AGENT_PHONE, "\n".join(lines))
        _last_sla_alert = now

        # Clear SLA to avoid re-alert
        conn.execute(
            "UPDATE crm.leads SET sla_deadline = NULL WHERE sla_deadline IS NOT NULL AND sla_deadline < ?",
            (now.isoformat(),)
        )
        conn.commit()

    except Exception as e:
        logger.error(f"SLA check error: {e}")
    finally:
        conn.close()


async def check_followups():
    """Follow-up due reminder — ONE batched message, max 1x per 4 hours."""
    global _last_followup_alert
    now = datetime.now(timezone.utc)

    # Cooldown check
    if _last_followup_alert and (now - _last_followup_alert).total_seconds() < FOLLOWUP_COOLDOWN_HOURS * 3600:
        logger.debug("Follow-up check: cooldown active, skip")
        return

    conn = get_db()
    try:
        today = now.strftime("%Y-%m-%d")
        rows = conn.execute("""
            SELECT id, name, phone, bucket, next_follow_up_at, follow_up_reason, ai_score
            FROM crm.leads
            WHERE next_follow_up_at IS NOT NULL
              AND date(next_follow_up_at) <= ?
              AND bucket NOT IN ('closed', 'nurture')
            ORDER BY next_follow_up_at
        """, (today,)).fetchall()

        if not rows:
            return

        logger.info(f"Follow-up check: {len(rows)} leads due")

        lines = [f"📋 *Follow-up Hari Ini — {len(rows)} leads:*\n"]
        for i, lead in enumerate(rows[:10], 1):
            score = lead["ai_score"]
            score_tag = "🔥" if score and score >= 80 else ("⭐" if score and score >= 60 else "")
            lines.append(
                f"{i}. {score_tag} {lead['name']} ({lead['phone'] or '-'})\n"
                f"   [{lead['bucket']}] {lead['follow_up_reason'] or '-'}"
            )

            conn.execute("""
                INSERT INTO crm.lead_activities (lead_id, activity_type, description)
                VALUES (?, 'follow_up_reminder', ?)
            """, (lead["id"], f"Reminder dikirim untuk tanggal {today}"))

        if len(rows) > 10:
            lines.append(f"\n...dan {len(rows) - 10} lead lainnya")

        await send_message(AGENT_PHONE, "\n".join(lines))
        _last_followup_alert = now
        conn.commit()

    except Exception as e:
        logger.error(f"Follow-up check error: {e}")
    finally:
        conn.close()


def start_scheduler():
    """Start background scheduler."""
    scheduler.add_job(check_sla, "interval", hours=1, id="sla_checker", replace_existing=True)
    scheduler.add_job(check_followups, "interval", hours=1, id="followup_checker", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started: SLA (1h cooldown), Follow-up (1h cooldown)")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
