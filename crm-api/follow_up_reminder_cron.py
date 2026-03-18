#!/usr/bin/env python3
"""
Livininbintaro CRM — Follow-up Reminder Cron (Phase C)
Send daily follow-up reminders to Ocha via WhatsApp
Runs at 08:00 WIB (01:00 UTC)
"""

import asyncio
import sys
from datetime import datetime, date
from pathlib import Path

# Add project path
sys.path.insert(0, '/var/www/livininbintaro/crm-api')

from db import get_db
from gowa_client import send_message

# Ocha's WhatsApp number
OCHA_PHONE = "628118606999"


async def send_reminders():
    """Send follow-up reminder to Ocha."""
    conn = get_db()
    
    try:
        today = date.today()
        
        # Get leads that need follow-up today
        leads = conn.execute("""
            SELECT name, phone, follow_up_reason, ai_score, bucket, status
            FROM leads
            WHERE DATE(next_follow_up_at) <= ?
              AND bucket IN ('inbox', 'qualified', 'showing', 'negotiation')
            ORDER BY ai_score DESC NULLS LAST, next_follow_up_at
            LIMIT 10
        """, (today.strftime('%Y-%m-%d'),)).fetchall()
        
        if not leads:
            print(f"[{datetime.now()}] No follow-ups for today")
            return
        
        # Build message
        lines = [f"📋 *Follow Up Hari Ini ({today.strftime('%d %b %Y')})*\n"]
        
        for i, lead in enumerate(leads, 1):
            # Score emoji
            score = lead["ai_score"] or 0
            if score >= 80:
                score_emoji = "🔥"
            elif score >= 60:
                score_emoji = "🟢"
            else:
                score_emoji = "🟡"
            
            # Lead info
            lines.append(f"{i}. {score_emoji} *{lead['name']}* ({lead['phone']})")
            lines.append(f"   Status: {lead['status']} | Bucket: {lead['bucket']}")
            
            if lead["follow_up_reason"]:
                lines.append(f"   → {lead['follow_up_reason']}")
            
            lines.append("")  # Empty line between leads
        
        lines.append(f"\n*Total: {len(leads)} leads perlu follow up*")
        lines.append(f"Cek detail: https://livininbintaro.my.id")
        
        message = "\n".join(lines)
        
        # Send via GOWA
        result = await send_message(OCHA_PHONE, message)
        
        if result.get("status") == "sent":
            print(f"[{datetime.now()}] ✅ Follow-up reminder sent to Ocha: {len(leads)} leads")
        else:
            print(f"[{datetime.now()}] ❌ Failed to send reminder: {result}")
    
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(send_reminders())
