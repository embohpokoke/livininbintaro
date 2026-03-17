# Livininbintaro Full Stack Inspection
*Run this with Claude Code on VPS: cd /var/www/livininbintaro && claude*

---

You are doing a full end-to-end diagnostic of the Livininbintaro property listing platform.
Output a single markdown report saved to: /var/www/livininbintaro/INSPECTION_REPORT.md

## CONTEXT
- Domain: livininbintaro.my.id
- Dashboard: dashboard.livininbintaro.my.id (currently returning {"detail":"Not Found"})
- GOWA: WA chatbot connected but CRM data stale since February
- Images: sync_images.py claims 18 pending but skips all — images not loading on web
- Migration: recently migrated from old VPS — possible broken paths/configs

---

## INSPECTION CHECKLIST

### 1. PROJECT STRUCTURE
- List all files and directories in /var/www/livininbintaro/
- Identify: API server file, frontend files, GOWA config, DB file, scripts
- Note any .env files and what env vars are set (don't print secret values, just key names)

### 2. API SERVER
- What is the main API entry point? (app.py / main.py / server.js?)
- What port is it running on?
- Check PM2 or systemd: is it running? uptime? restart count?
- Run: curl -s http://localhost:<port>/health or /api/health
- Run: curl -s http://localhost:<port>/api/listings | head -c 500
- Check all registered routes — is /dashboard route registered?

### 3. DATABASE
- Find the SQLite DB file — what is the full path?
- Run: sqlite3 <db_path> ".tables"
- Run: sqlite3 <db_path> "SELECT COUNT(*) FROM listings;"
- Run: sqlite3 <db_path> "SELECT COUNT(*) FROM contacts;" (or customers/leads table)
- Run: sqlite3 <db_path> "SELECT MAX(created_at) FROM contacts;" — when was last entry?
- Check if there are image columns — what format? (URL? local path? filename?)

### 4. IMAGES ISSUE
- Find sync_images.py — show the full script
- What does "pending" mean in this script? Where does it look for images?
- Where should images be stored on disk? Does that directory exist?
- Are there any images currently in that directory?
- Check nginx config for livininbintaro — is the image path correctly mapped?
- Run: ls -la /var/www/livininbintaro/images/ (or wherever images should be)
- Check if Google Sheets image URLs are accessible: pick 1 URL from the "ALAMAT" column image field and curl it

### 5. DASHBOARD ISSUE
- Check nginx config: grep -r "dashboard.livininbintaro" /etc/nginx/
- Is dashboard.livininbintaro.my.id pointing to the same API or a different service?
- Is there a /dashboard route in the API?
- Was there a separate Kanban/dashboard service? Is it running?
- Check: pm2 list | grep -i livin

### 6. GOWA / CRM SYNC
- Find GOWA config — what webhook URL is registered?
- Find the webhook handler (wa_webhook.py or similar)
- Is the webhook handler running? Check PM2/systemd
- Run: curl -s http://localhost:<gowa_port>/api/devices (check GOWA device status)
- Check recent webhook logs — any errors since February?
- Check: what triggers a new CRM entry? Is it GOWA webhook → API → DB?
- Test the chain: is the API endpoint that receives GOWA webhook actually reachable?

### 7. NGINX CONFIG
- Show full nginx config for livininbintaro.my.id
- Show full nginx config for dashboard.livininbintaro.my.id
- Check SSL cert expiry: openssl s_client -connect livininbintaro.my.id:443 </dev/null 2>/dev/null | openssl x509 -noout -dates

### 8. LOGS
- Check API error logs (last 50 lines)
- Check nginx error log: tail -50 /var/log/nginx/error.log | grep livin
- Check GOWA logs if available

---

## OUTPUT FORMAT

Save report to /var/www/livininbintaro/INSPECTION_REPORT.md with this structure:

```
# Livininbintaro Inspection Report
Date: [today]

## Summary
[3-5 bullet points of most critical findings]

## 1. Project Structure
...

## 2. API Server
Status: RUNNING/DOWN
Port: X
Routes found: [list]
Dashboard route: EXISTS/MISSING

## 3. Database
Tables: [list]
Listings count: X
Last CRM entry: [date]
Image storage: [how images are stored]

## 4. Images Issue
Root cause: [diagnosis]
Fix needed: [what to do]

## 5. Dashboard Issue  
Root cause: [diagnosis]
Fix needed: [what to do]

## 6. GOWA/CRM Sync
GOWA status: CONNECTED/DISCONNECTED
Webhook handler: RUNNING/DOWN
Last webhook received: [date if findable]
Root cause of stale data: [diagnosis]

## 7. Nginx
Config: OK/ISSUES
SSL expiry: [date]

## 8. Recommended Fix Priority
1. [highest priority]
2. ...
3. ...
```
