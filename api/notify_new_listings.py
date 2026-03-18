#!/usr/bin/env python3
"""
notify_new_listings.py - Send daily notification of new listings to WhatsApp + Telegram.
Runs at 09:00 WIB every morning.
Fetches listings created in last 24h and sends summary to:
  - Ocha LivininBintaro (WhatsApp: 62811309991)
  - Erik Mahendra (Telegram: 5309429603)

Usage:
  python notify_new_listings.py         # Send morning notification
  python notify_new_listings.py --test  # Test without actually sending
"""

import os
import sys
import json
import subprocess
import argparse
import logging
from datetime import datetime, timedelta
from urllib.parse import quote

# ─── Configuration ───────────────────────────────────────────────────────────

# Notification Recipients
NOTIFY_TARGETS = [
    ("whatsapp", "62811309991", "Ocha LivininBintaro (WhatsApp)"),
    ("telegram", "5309429603", "Erik Mahendra (Telegram)"),
]

LOG_FILE = "/var/www/livininbintaro/api/notify.log"

# ─── Logging Setup ───────────────────────────────────────────────────────────

def setup_logging():
    """Configure logging to both file and console."""
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger("notify_listings")
    logger.setLevel(logging.DEBUG)

    # File handler
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler (stderr only, to avoid doubling with cron >> redirect)
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

# ─── Database Operations ─────────────────────────────────────────────────────

def run_sql(sql):
    """Run SQL via podman exec psql, return stdout."""
    cmd = [
        "docker", "exec", "-i", "livininbintaro-db",
        "psql", "-U", "livin", "-d", "livininbintaro",
        "-t", "-A", "-c", sql
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise Exception(f"SQL ERROR: {result.stderr.strip()}")
    return result.stdout.strip()

# ─── Message Formatting ─────────────────────────────────────────────────────

def format_price(price):
    """Format price as human-readable (Rp 1.6 M, Rp 90 Jt, etc)."""
    if not price:
        return "N/A"
    
    price = int(price)
    if price >= 1_000_000_000:
        return f"Rp {price / 1_000_000_000:.1f} Mly"
    elif price >= 1_000_000:
        return f"Rp {price / 1_000_000:.0f} Jt"
    else:
        return f"Rp {price / 1_000:,.0f}K"


def format_listing_summary(listing):
    """Format listing: CPA | Location | Type | Price + Search Link"""
    cpa = listing[0].strip()
    title = listing[1]
    listing_type = listing[2]
    price = listing[3]
    cluster = listing[4]

    # Use cluster as location, fallback to title
    location = cluster if cluster else title

    # listing_type: dijual / disewa
    type_label = "DIJUAL" if listing_type in ["dijual", "jual"] else "DISEWA"
    price_str = format_price(price) if price else "Harga nego"

    # Format: CPA | Location | Type | Price
    line = f"{cpa} | {location} | {type_label} | {price_str}"

    # Add search link (URL encoded CPA)
    search_url = f"https://livininbintaro.my.id/?search={quote(cpa)}"
    line += f"\n{search_url}"

    return line


def build_notification_message(new_listings):
    """Build the WhatsApp notification message."""
    if not new_listings:
        return "Pagi Ocha! Tidak ada listing baru hari ini."
    
    count = len(new_listings)
    lines = [f"🌅 *Pagi Ocha!* Ada {count} listing baru hari ini:\n"]
    
    for i, listing in enumerate(new_listings[:10], 1):  # Show top 10
        summary = format_listing_summary(listing)
        lines.append(f"{i}. {summary}")
    
    if count > 10:
        lines.append(f"\n... dan {count - 10} listing lainnya")
    
    lines.append("\n📊 Cek dashboard untuk detail lengkap!")
    return "\n".join(lines)

# ─── Notification Delivery ──────────────────────────────────────────────────

def send_notification(message, test_mode=False):
    """Send notification via OpenClaw message tool to all configured recipients.
    
    Args:
        message: Message text to send
        test_mode: If True, log but don't send
    
    Returns:
        True if sent to all recipients successfully or test_mode, False otherwise
    """
    if test_mode:
        print("\n" + "=" * 70)
        print("[TEST MODE] Notification would be sent to:")
        for channel, target, label in NOTIFY_TARGETS:
            print(f"  ✓ {label}")
        print("=" * 70)
        print("\nMessage Content:")
        print(message)
        print("=" * 70 + "\n")
        return True
    
    try:
        all_sent = True
        print("\n[INFO] Sending notification to all recipients...")
        
        for channel, target, label in NOTIFY_TARGETS:
            try:
                # Add prefix for WhatsApp (+ sign), not for Telegram
                prefix = "+" if channel == "whatsapp" else ""
                target_with_prefix = f"{prefix}{target}"
                
                cmd = [
                    "/usr/local/bin/openclaw", "message", "send",
                    "--channel", channel,
                    "--target", target_with_prefix,
                    "--message", message
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print(f"  ✅ {label} — Message sent successfully")
                else:
                    print(f"  ❌ {label} — Send failed: {result.stderr.strip()}")
                    all_sent = False
                    
            except Exception as e:
                print(f"  ❌ {label} — Error: {e}")
                all_sent = False
        
        return all_sent
    
    except Exception as e:
        print(f"[ERROR] Notification delivery failed: {e}")
        return False

# ─── Main Function ──────────────────────────────────────────────────────────

def notify(test_mode=False):
    """Main notification function."""
    logger = setup_logging()
    logger.info("=" * 70)
    logger.info(f"NOTIFICATION CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    try:
        # Query new listings from last 24 hours
        now = datetime.utcnow()
        yesterday = now - timedelta(hours=24)
        yesterday_str = yesterday.isoformat()
        
        logger.info(f"Checking for listings created after {yesterday_str}...")
        
        sql = (
            "SELECT cpa_code, title, listing_type, price, cluster "
            "FROM listings "
            "WHERE created_at > NOW() - INTERVAL '24 hours' "
            "AND is_active = true "
            "ORDER BY created_at DESC"
        )
        
        raw = run_sql(sql)
        
        if not raw:
            logger.info("No new listings found in the last 24 hours.")
            message = "Pagi Ocha! Tidak ada listing baru hari ini."
        else:
            # Parse results
            new_listings = []
            for line in raw.split("\n"):
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) >= 5:
                    new_listings.append(parts)
            
            logger.info(f"Found {len(new_listings)} new active listings")
            message = build_notification_message(new_listings)
        
        # Send notification to all configured recipients
        logger.info("Sending notification to all recipients...")
        if send_notification(message, test_mode=test_mode):
            logger.info("✅ All notifications sent successfully")
        else:
            logger.error("❌ Failed to send one or more notifications")
        
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    return True


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send daily new listings notification")
    parser.add_argument("--test", action="store_true", help="Test mode (don't actually send)")
    
    args = parser.parse_args()
    success = notify(test_mode=args.test)
    sys.exit(0 if success else 1)
