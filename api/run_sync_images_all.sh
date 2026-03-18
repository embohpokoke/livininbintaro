#!/bin/bash
# run_sync_images_all.sh — Sync images sampai selesai
# Smart stop: kalau pending tidak berubah 2x berturut-turut = semua folder kosong, disable cron.
# Flock = anti concurrent | Auto-disable cron kalau done

LOCKFILE="/tmp/sync_images_all.lock"
LOGFILE="/var/www/livininbintaro/api/sync_images_all.log"
STATEFILE="/tmp/sync_images_last_count.txt"
SCRIPT_PATH="/var/www/livininbintaro/api/sync_images.py"
VENV="/var/www/livininbintaro/api/.venv/bin/python3"
CRON_TAG="TEMP_SYNC_IMAGES_ALL"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGFILE"
}

disable_cron() {
    TMPFILE=$(mktemp)
    crontab -l 2>/dev/null | grep -v "$CRON_TAG" > "$TMPFILE"
    crontab "$TMPFILE"
    rm -f "$TMPFILE" "$STATEFILE"
    log "🗑️  Cron sementara dihapus."
}

get_pending() {
    docker exec livininbintaro-db psql -U livin -d livininbintaro -t -A -c \
        "SELECT COUNT(*) FROM listings WHERE drive_folder_id IS NOT NULL AND drive_folder_id != '' AND (images IS NULL OR images::text = 'null' OR images::text = '[]')" 2>/dev/null | tr -d '[:space:]'
}

# === Flock: cegah concurrent ===
exec 9>"$LOCKFILE"
if ! flock -n 9; then
    log "⏭️  Skip — instance lain masih jalan."
    exit 0
fi

# === Cek pending sekarang ===
PENDING=$(get_pending)

if [[ -z "$PENDING" || "$PENDING" == "0" ]]; then
    log "✅ Selesai — 0 listing pending. Hapus cron."
    disable_cron
    flock -u 9
    exit 0
fi

log "📸 Pending: $PENDING listing."

# === Smart-stop: cek apakah stuck (no progress) ===
LAST_COUNT=""
if [[ -f "$STATEFILE" ]]; then
    LAST_COUNT=$(cat "$STATEFILE")
fi

if [[ "$LAST_COUNT" == "$PENDING" ]]; then
    log "⚠️  Pending sama seperti run sebelumnya ($PENDING). Kemungkinan semua folder kosong/tidak bisa diakses."
    log "✅ Menganggap selesai — disable cron sementara."
    disable_cron
    flock -u 9
    exit 0
fi

# Simpan pending count untuk perbandingan run berikutnya
echo "$PENDING" > "$STATEFILE"

# === Jalankan sync (ONE BATCH: mode terbatas 50 menit via internal logic) ===
log "Menjalankan sync (--all mode)..."
cd /var/www/livininbintaro/api

# Jalankan dengan timeout 60 menit (satu batch), lalu stop
timeout 3600 "$VENV" "$SCRIPT_PATH" --all >> "$LOGFILE" 2>&1
EXIT_CODE=$?

# === Cek sisa setelah run ===
REMAINING=$(get_pending)
log "Run selesai (exit=$EXIT_CODE). Sisa pending: ${REMAINING:-?}"

if [[ "${REMAINING:-1}" == "0" ]]; then
    log "🎉 Semua gambar sudah sync. Hapus cron."
    disable_cron
fi

flock -u 9
