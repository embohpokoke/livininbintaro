#!/usr/bin/env python3
"""
Livininbintaro CRM — Content Reminder Cron
Sends WhatsApp reminders to Ocha about scheduled content
Runs daily at 08:00 WIB and 14:00 WIB (for late posting check)
"""

import asyncio
import sys
from datetime import date, datetime

# Add app directory to path
sys.path.insert(0, '/var/www/livininbintaro/crm-api')

from db import get_db
from gowa_client import send_message
from config import AGENT_PHONE

# Ocha's phone number (using agent phone from config)
OCHA_PHONE = AGENT_PHONE


def format_time(time_str: str) -> str:
    """Format time string to HH:MM."""
    if isinstance(time_str, str):
        return time_str[:5]  # Get HH:MM from HH:MM:SS
    return str(time_str)


async def send_content_reminders():
    """Send content posting reminders for today's scheduled content."""

    db = get_db()
    today = date.today()

    # Get today's scheduled content that hasn't been reminded
    cursor = db.execute(
        """
        SELECT cc.id, cc.platform, cc.content_pillar, cc.caption, cc.post_time,
               cc.media_notes, cc.status,
               l.title as property_name
        FROM crm.content_calendar cc
        LEFT JOIN public.listings l ON cc.property_id = l.id
        WHERE cc.post_date = ?
          AND cc.status = 'scheduled'
          AND cc.reminder_sent = FALSE
        ORDER BY cc.post_time
        """,
        (today,)
    )

    entries = cursor.fetchall()

    if not entries:
        print(f"No content reminders for {today}")
        db.close()
        return

    # Platform emojis
    platform_emoji = {
        "instagram": "📸",
        "tiktok": "🎬",
        "facebook": "📘",
        "wa_status": "📱"
    }

    # Build reminder message
    lines = [f"📅 *Content Plan Hari Ini ({today.strftime('%d %b %Y')})*\n"]

    for i, entry in enumerate(entries, 1):
        emoji = platform_emoji.get(entry["platform"], "📝")
        post_time = format_time(entry["post_time"])

        lines.append(f"{i}. {emoji} *{entry['platform'].upper()}* jam {post_time}")

        if entry["property_name"]:
            lines.append(f"   Properti: {entry['property_name']}")

        if entry["content_pillar"]:
            pillar_name = entry["content_pillar"].replace("_", " ").title()
            lines.append(f"   Pillar: {pillar_name}")

        if entry["caption"]:
            preview = entry["caption"][:100] + "..." if len(entry["caption"]) > 100 else entry["caption"]
            lines.append(f"   Caption: _{preview}_")

        if entry["media_notes"]:
            lines.append(f"   Media: {entry['media_notes']}")

        lines.append("")

    lines.append(f"📋 Total: {len(entries)} post hari ini")
    lines.append(f"✏️ Edit caption: https://livininbintaro.my.id/crm")

    message = "\n".join(lines)

    # Send WhatsApp message
    print(f"Sending reminder to {OCHA_PHONE} for {len(entries)} content items")
    result = await send_message(OCHA_PHONE, message)

    if result.get("status") == "sent":
        print("✅ Reminder sent successfully")

        # Mark reminders as sent
        for entry in entries:
            db.execute(
                "UPDATE crm.content_calendar SET reminder_sent = TRUE WHERE id = ?",
                (entry["id"],)
            )

        db.commit()
    else:
        print(f"❌ Failed to send reminder: {result.get('error')}")

    db.close()


async def send_late_posting_check():
    """Check for content that should have been posted by now."""

    db = get_db()
    today = date.today()
    now = datetime.now().time()

    # Get scheduled content from today that should have been posted
    cursor = db.execute(
        """
        SELECT cc.id, cc.platform, cc.content_pillar, cc.post_time,
               l.title as property_name
        FROM crm.content_calendar cc
        LEFT JOIN public.listings l ON cc.property_id = l.id
        WHERE cc.post_date = ?
          AND cc.status = 'scheduled'
          AND cc.post_time < ?
        ORDER BY cc.post_time
        """,
        (today, now.strftime("%H:%M:%S"))
    )

    late_entries = cursor.fetchall()
    db.close()

    if not late_entries:
        print(f"No late content for {today}")
        return

    # Build late posting alert
    lines = [f"⚠️ *Content Belum Dipost*\n"]
    lines.append(f"Ada {len(late_entries)} content yang harusnya sudah dipost:\n")

    for entry in late_entries:
        post_time = format_time(entry["post_time"])
        lines.append(f"• {entry['platform'].upper()} jam {post_time}")
        if entry["property_name"]:
            lines.append(f"  ({entry['property_name']})")

    lines.append(f"\n📱 Check https://livininbintaro.my.id/crm")

    message = "\n".join(lines)

    # Send alert
    print(f"Sending late posting alert to {OCHA_PHONE} for {len(late_entries)} items")
    result = await send_message(OCHA_PHONE, message)

    if result.get("status") == "sent":
        print("✅ Late posting alert sent")
    else:
        print(f"❌ Failed to send alert: {result.get('error')}")


def main():
    """Main function to run appropriate reminder based on time."""

    current_hour = datetime.now().hour

    if current_hour < 12:
        # Morning reminder (08:00 WIB)
        print("Running morning content reminder...")
        asyncio.run(send_content_reminders())
    else:
        # Afternoon check (14:00 WIB)
        print("Running late posting check...")
        asyncio.run(send_late_posting_check())


if __name__ == "__main__":
    main()
