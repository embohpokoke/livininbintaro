#!/bin/bash
# Livininbintaro listing data sync
# Runs: 08:00 WIB (01:00 UTC) daily
# Only syncs listing data from Google Sheets. Images synced separately.

cd /var/www/livininbintaro/api
source .venv/bin/activate

echo "=========================================="
echo "LISTING SYNC - $(date)"
echo "=========================================="

python3 sync_listings.py 2>&1

echo ""
echo "=========================================="
echo "LISTING SYNC COMPLETED - $(date)"
echo "=========================================="
