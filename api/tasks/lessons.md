# Lessons Learned

## 2026-02-19: index.html Corruption

**What happened:** The full SPA `index.html` (101KB, 1963 lines) was overwritten with a 61-line JS fragment during leads page development. The entire frontend became non-functional.

**Root cause:** A file write operation wrote only a code snippet instead of the full file content.

**Lesson:**
- Always backup `index.html` before any write: `cp /var/www/livininbintaro/index.html /var/www/livininbintaro/index.html.backup-$(date +%Y%m%d-%H%M%S)`
- Use Edit tool for targeted changes instead of Write tool for the full file
- Verify file integrity after writes: check file starts with `<!DOCTYPE html>` and size > 50KB
