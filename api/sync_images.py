#!/usr/bin/env python3
"""
sync_images.py - Download property images from Google Drive and cache locally.
Runs in 50-minute batches with 10-minute cooldowns to avoid Google rate limits.
Skips listings that already have images (DB + local filesystem double-check).

Usage:
  python sync_images.py              # Smart mode: only new/updated in last 24h
  python sync_images.py --all        # All listings without images (batched)
  python sync_images.py 100          # First 100 listings without images
  python sync_images.py --hours 48   # New/updated in last 48 hours
"""

import os
import sys
import json
import time
import re
import requests
import subprocess
from PIL import Image
from io import BytesIO

# Load OAuth credentials
CREDENTIALS_FILE = "/root/.secrets/livininbintaro-google.json"
TOKEN_FILE = "/var/www/livininbintaro/api/.google_token.json"

if not os.path.exists(CREDENTIALS_FILE):
    print(f"[ERROR] Credentials file not found: {CREDENTIALS_FILE}")
    print("Please create the file with your Google OAuth2 credentials.")
    sys.exit(1)

with open(CREDENTIALS_FILE) as f:
    creds = json.load(f)["installed"]
    CLIENT_ID = creds["client_id"]
    CLIENT_SECRET = creds["client_secret"]


# --- Config ---

IMAGES_BASE = "/var/www/livininbintaro/images"
WEB_PREFIX = "/images"
MAX_IMAGES_PER_LISTING = 5
API_SLEEP = 0.3  # seconds between Drive API calls
MAX_IMAGE_WIDTH = 1200  # Max width for optimized images
JPEG_QUALITY = 85  # JPEG quality for compression

# Batch timing
BATCH_DURATION = 50 * 60   # 50 minutes of work per batch
COOLDOWN_DURATION = 10 * 60  # 10 minutes cooldown between batches

# Parse arguments
SMART_MODE = True  # Default: only sync new/updated listings
HOURS_BACK = 24    # Default: last 24 hours
LIMIT = 0          # 0 = no limit

if len(sys.argv) > 1:
    if sys.argv[1] == "--all":
        SMART_MODE = False
        LIMIT = 0
    elif sys.argv[1] == "--hours" and len(sys.argv) > 2:
        HOURS_BACK = int(sys.argv[2])
    elif sys.argv[1].isdigit():
        LIMIT = int(sys.argv[1])
        SMART_MODE = False


TOKEN_LIFETIME = 2700  # Refresh after 45 minutes (token valid 60 min, safe margin)
_token_cache = {"token": None, "fetched_at": 0}


def load_token():
    """Load saved token from file."""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def save_token(token_data):
    """Save token to file."""
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)


def get_access_token(force=False):
    """Get access token, auto-refresh if expired or about to expire."""
    now = time.time()
    
    # Use cached token if still valid
    if not force and _token_cache["token"] and (now - _token_cache["fetched_at"]) < TOKEN_LIFETIME:
        return _token_cache["token"]
    
    # Load saved token
    token_data = load_token()
    
    if not token_data or "refresh_token" not in token_data:
        print("[ERROR] No refresh token found!")
        print(f"Run generate_refresh_token.py first to get a refresh token.")
        sys.exit(1)
    
    # Refresh access token
    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": token_data["refresh_token"],
        "grant_type": "refresh_token",
    })
    
    if resp.status_code != 200:
        print(f"[ERROR] Token refresh failed: {resp.text}")
        print("Your refresh token may be expired. Run generate_refresh_token.py again.")
        sys.exit(1)
    
    new_token = resp.json()
    access_token = new_token["access_token"]
    
    # Update saved token (keep refresh_token from old data)
    token_data.update(new_token)
    save_token(token_data)
    
    # Update cache
    _token_cache["token"] = access_token
    _token_cache["fetched_at"] = now
    
    print(f"[OK] Got access token ({access_token[:20]}...)")
    return access_token
def run_sql(sql):
    """Run SQL via docker exec psql, return stdout."""
    cmd = [
        "docker", "exec", "-i", "livininbintaro-db",
        "psql", "-U", "livin", "-d", "livininbintaro",
        "-t", "-A", "-c", sql
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[SQL ERROR] {result.stderr.strip()}")
        return ""
    return result.stdout.strip()


def run_sql_update(sql):
    """Run an update SQL statement."""
    cmd = [
        "docker", "exec", "-i", "livininbintaro-db",
        "psql", "-U", "livin", "-d", "livininbintaro",
        "-c", sql
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[SQL ERROR] {result.stderr.strip()}")
        return False
    return True


def sanitize_dirname(cpa_code):
    """Make a filesystem-safe directory name from CPA code."""
    return re.sub(r'\s+', '_', cpa_code.strip())


def listing_already_synced(listing_id, cpa_code):
    """Double-check: does this listing already have images in DB AND on disk?"""
    # Check DB
    db_images = run_sql(
        f"SELECT images::text FROM listings WHERE id = {listing_id}"
    )
    if db_images and db_images not in ('', 'null', '[]', 'None'):
        try:
            imgs = json.loads(db_images)
            if isinstance(imgs, list) and len(imgs) > 0:
                # Also verify at least one file exists on disk
                dir_name = sanitize_dirname(cpa_code)
                dest_dir = os.path.join(IMAGES_BASE, dir_name)
                if os.path.isdir(dest_dir):
                    files = [f for f in os.listdir(dest_dir) if os.path.getsize(os.path.join(dest_dir, f)) > 0]
                    if files:
                        return True
        except (json.JSONDecodeError, TypeError):
            pass
    return False


def optimize_image(image_path):
    """Optimize image: resize to max width, compress JPEG quality."""
    try:
        img = Image.open(image_path)

        # Convert RGBA to RGB if needed (for JPEG compatibility)
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img

        # Resize if width exceeds max
        if img.width > MAX_IMAGE_WIDTH:
            ratio = MAX_IMAGE_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((MAX_IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS)

        # Save as JPEG with compression
        img.save(image_path, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        return True

    except Exception as e:
        print(f"[WARN] Could not optimize image {image_path}: {e}")
        return False


def list_drive_images(token, folder_id):
    """List image files in a Google Drive folder."""
    url = "https://www.googleapis.com/drive/v3/files"
    params = {
        "q": f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false",
        "fields": "files(id,name,mimeType)",
        "pageSize": MAX_IMAGES_PER_LISTING,
        "orderBy": "name",
    }
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json().get("files", [])


def download_image(token, file_id, file_name, dest_dir):
    """Download an image from Google Drive using alt=media and optimize it."""
    dest_path = os.path.join(dest_dir, file_name)
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return dest_path  # already downloaded

    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, stream=True, timeout=30)
    resp.raise_for_status()

    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    # Optimize image (resize + compress)
    optimize_image(dest_path)

    return dest_path


def fetch_pending_listings():
    """Query listings that still need images from DB."""
    base_where = (
        "drive_folder_id IS NOT NULL "
        "AND drive_folder_id != '' "
        "AND (images IS NULL OR images::text = 'null' OR images::text = '[]')"
    )

    if SMART_MODE:
        time_filter = f"AND (created_at > NOW() - INTERVAL '{HOURS_BACK} hours' OR updated_at > NOW() - INTERVAL '{HOURS_BACK} hours')"
        base_where = f"{base_where} {time_filter}"

    limit_clause = f"LIMIT {LIMIT}" if LIMIT > 0 else ""

    sql = (
        "SELECT id, cpa_code, drive_folder_id "
        "FROM listings "
        f"WHERE {base_where} "
        "ORDER BY created_at DESC, id DESC "
        f"{limit_clause}"
    )

    print(f"[SQL] {sql}")
    rows_raw = run_sql(sql)
    if not rows_raw:
        return []

    rows = []
    for line in rows_raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) == 3:
            rows.append({
                "id": int(parts[0]),
                "cpa_code": parts[1],
                "drive_folder_id": parts[2],
            })
    return rows


def main():
    print("=== sync_images.py - Starting ===")
    print(f"Credentials: {CREDENTIALS_FILE}")
    print(f"Token file: {TOKEN_FILE}")


    # Show mode
    if SMART_MODE:
        print(f"Mode: SMART (only new/updated in last {HOURS_BACK} hours)")
    elif LIMIT > 0:
        print(f"Mode: LIMITED (first {LIMIT} listings)")
    else:
        print(f"Mode: ALL (batched {BATCH_DURATION//60}min work / {COOLDOWN_DURATION//60}min cooldown)")

    # Grand totals across all batches
    grand_success = 0
    grand_failed = 0
    grand_skipped = 0
    grand_images = 0
    grand_already_synced = 0
    batch_num = 0

    while True:
        batch_num += 1

        # Re-query pending listings each batch (so newly synced ones are excluded)
        rows = fetch_pending_listings()
        if not rows:
            print(f"[INFO] No more listings need images. All done!")
            break

        print(f"\n{'='*60}")
        print(f"BATCH {batch_num} — {len(rows)} listings pending")
        print(f"{'='*60}")

        # Get fresh token for this batch
        token = get_access_token(force=True)
        batch_start = time.time()

        # Batch stats
        success = 0
        failed = 0
        skipped = 0
        already_synced = 0
        total_images = 0
        errors = []

        for i, row in enumerate(rows):
            # Check if batch time exceeded
            elapsed = time.time() - batch_start
            if elapsed >= BATCH_DURATION:
                print(f"\n[BATCH] 50-minute window reached after {i} listings. Pausing...")
                break

            listing_id = row["id"]
            cpa_code = row["cpa_code"]
            folder_id = row["drive_folder_id"]
            dir_name = sanitize_dirname(cpa_code)
            dest_dir = os.path.join(IMAGES_BASE, dir_name)

            # Double-check: skip if already synced (DB + disk)
            if listing_already_synced(listing_id, cpa_code):
                already_synced += 1
                continue

            try:
                # Auto-refresh token before it expires
                token = get_access_token()

                # List images in Drive folder
                files = list_drive_images(token, folder_id)
                time.sleep(API_SLEEP)

                if not files:
                    skipped += 1
                    continue

                # Create local dir
                os.makedirs(dest_dir, exist_ok=True)

                # Download images
                local_paths = []
                for f in files[:MAX_IMAGES_PER_LISTING]:
                    file_name = re.sub(r'[^\w\-.]', '_', f["name"])  # sanitize filename
                    try:
                        download_image(token, f["id"], file_name, dest_dir)
                        web_path = f"{WEB_PREFIX}/{dir_name}/{file_name}"
                        local_paths.append(web_path)
                        total_images += 1
                        time.sleep(API_SLEEP)
                    except Exception as e:
                        print(f"  [WARN] Failed to download {f['name']}: {e}")
                        continue

                if local_paths:
                    images_json = json.dumps(local_paths).replace("'", "''")
                    update_sql = (
                        f"UPDATE listings SET images = '{images_json}'::json, "
                        f"updated_at = NOW() WHERE id = {listing_id}"
                    )
                    if run_sql_update(update_sql):
                        success += 1
                        print(f"  [OK] {cpa_code}: {len(local_paths)} images")
                    else:
                        failed += 1
                        errors.append(f"DB update failed for {cpa_code}")
                else:
                    skipped += 1

            except Exception as e:
                failed += 1
                err_msg = f"{cpa_code} (folder={folder_id}): {e}"
                errors.append(err_msg)
                if "401" in str(e) or "403" in str(e):
                    print(f"[ERROR] Auth error on {cpa_code}, force-refreshing token...")
                    try:
                        token = get_access_token(force=True)
                    except Exception:
                        print("[FATAL] Cannot refresh token. Stopping.")
                        break
                continue

            # Progress log
            if (i + 1) % 50 == 0:
                elapsed_min = (time.time() - batch_start) / 60
                print(f"[PROGRESS] {i+1}/{len(rows)} | OK={success} Failed={failed} "
                      f"Skipped={skipped} AlreadySynced={already_synced} "
                      f"Images={total_images} | {elapsed_min:.1f}min elapsed")

        # Batch report
        grand_success += success
        grand_failed += failed
        grand_skipped += skipped
        grand_images += total_images
        grand_already_synced += already_synced

        print(f"\n--- Batch {batch_num} done ---")
        print(f"Success: {success} | Failed: {failed} | Skipped: {skipped} | "
              f"Already synced: {already_synced} | Images: {total_images}")

        if errors:
            print(f"Errors ({len(errors)}):")
            for e in errors[:10]:
                print(f"  - {e}")

        # Check if there's more to do — re-query
        remaining = run_sql(
            "SELECT COUNT(*) FROM listings WHERE "
            "drive_folder_id IS NOT NULL AND drive_folder_id != '' "
            "AND (images IS NULL OR images::text = 'null' OR images::text = '[]')"
        )
        remaining_count = int(remaining) if remaining.isdigit() else 0

        if remaining_count == 0:
            print(f"\n[DONE] All listings synced!")
            break

        print(f"\n[COOLDOWN] {remaining_count} listings remaining. "
              f"Cooling down {COOLDOWN_DURATION//60} minutes to avoid Google rate limits...")
        time.sleep(COOLDOWN_DURATION)

    # Grand total report
    print(f"\n{'='*60}")
    print(f"=== GRAND TOTAL ({batch_num} batches) ===")
    print(f"{'='*60}")
    print(f"Success: {grand_success}")
    print(f"Failed: {grand_failed}")
    print(f"Skipped (no images in folder): {grand_skipped}")
    print(f"Already synced (skipped): {grand_already_synced}")
    print(f"Total images downloaded: {grand_images}")


if __name__ == "__main__":
    main()
