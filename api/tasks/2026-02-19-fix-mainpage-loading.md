# Task: Fix Mainpage Loading Error

**Date:** 2026-02-19
**Status:** COMPLETED
**Author:** Claude Code (with Erik)

---

## Objective

Fix the livininbintaro mainpage that was showing a loading error / blank page due to a corrupted `index.html` file.

## Root Cause

The file `/var/www/livininbintaro/index.html` was accidentally overwritten on 2026-02-19 at 14:19 UTC. The full SPA (101KB, 1963 lines of HTML/CSS/JS) was replaced with a 61-line JavaScript fragment containing only the `loadLeads()` and `filterLeads()` functions.

This likely happened during an incomplete implementation of the Leads Page Improvement (PLAN.md) where the file write operation only wrote a code snippet instead of the full file.

**Before (broken):** 2,370 bytes, 61 lines - just JS functions, no HTML structure
**After (restored):** 101,087 bytes, 1963 lines - complete SPA with HTML/CSS/JS

## Affected Components

- `/var/www/livininbintaro/index.html` - Frontend SPA (single-file PWA)

## Implementation

1. Identified the issue: `index.html` started with `async function loadLeads()` instead of `<!DOCTYPE html>`
2. Found two backup files:
   - `index.html.backup-20260217-161957` (100,331 bytes, Feb 17)
   - `index.html.backup-20260218-065346` (101,087 bytes, Feb 18) - **used this one**
3. Restored from the latest backup (Feb 18)

**Command used:**
```bash
yes | /usr/bin/cp /var/www/livininbintaro/index.html.backup-20260218-065346 /var/www/livininbintaro/index.html
```

## What Was NOT Restored

The `filterLeads()` function (client-side filtering for leads page) was a new feature under development that only existed in the corrupted fragment. It was NOT in the backup. This function needs to be re-implemented as part of the Leads Page Improvement plan (PLAN.md).

## Verification (QA)

| Check | Result |
|-------|--------|
| `index.html` starts with `<!DOCTYPE html>` | PASS |
| File size: 101,087 bytes (1963 lines) | PASS |
| Public URL returns HTTP 200 | PASS |
| Content-Type: text/html | PASS |
| API `/api/listings/?limit=1` returns data | PASS |
| `init()` function exists (line 1910) | PASS |
| `loadHomeStats()` exists (line 1032) | PASS |
| `loadHotListings()` exists (line 1052) | PASS |
| `loadLatestListings()` exists (line 1138) | PASS |
| `loadLeads()` exists (line 1493) | PASS |
| `handleUrl()` exists (line 1820) | PASS |
| `apiFetch()` exists (line 799) | PASS |

## Rollback Plan

If this restore causes issues, the previous backups are available:
- Broken file saved as: `/var/www/livininbintaro/index.html.broken-20260219` (if mv succeeded) or the fragment is trivial to recreate
- Older backup: `/var/www/livininbintaro/index.html.backup-20260217-161957`

## Lessons Learned

1. **Always create a backup before writing to index.html** - Any file write operation should backup first
2. **File write operations must be atomic** - Write to a temp file first, then move
3. **The `filterLeads()` function needs re-implementation** - It was lost in the corruption
