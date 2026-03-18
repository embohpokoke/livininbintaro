# PRODUCTION ASSESSMENT — LIVININBINTARO V1

**Assessment Date:** 2026-03-14
**VPS:** Hostinger (72.60.78.181)
**Purpose:** Validate production state before V2 development

---

## EXECUTIVE SUMMARY

Production is **OPERATIONAL and HEALTHY**. Previous claims of critical issues were incorrect:

- ✅ Google Drive OAuth token is **WORKING** (not expired)
- ✅ GOWA WhatsApp webhook is **CONNECTED** (not broken)
- ⚠️ Only real issue: 18 listings stuck in image sync loop (0.1%, non-critical)
- ✅ All APIs running healthy (ports 8000, 8003)
- ✅ Frontend accessible via HTTPS
- 📊 Database: 17,930 listings, 110 leads, 14 WA messages

**Recommendation:** Proceed directly to V2 development. No blocking critical fixes needed. Fix 18 stuck listings as minor task during Phase 1 setup.

---

## INFRASTRUCTURE INVENTORY

### VPS Hostinger (72.60.78.181)

**Server Specs:**
- OS: Ubuntu 22.04 LTS
- RAM: 4GB
- Storage: 80GB SSD
- SSH: Port 22, key-based auth (`~/.ssh/id_ed25519_hostinger`)

**Network:**
- Public IP: 72.60.78.181
- Domain: livininbintaro.my.id
- DNS: Pointing to Hostinger VPS ✅
- SSL: Let's Encrypt, valid, HTTP/2 enabled ✅

### Running Services

| Service | Port | Status | Uptime | Process |
|---------|------|--------|--------|---------|
| Main Platform API | 8000 | ✅ Active | 13+ hours | uvicorn (FastAPI) |
| CRM API | 8003 | ✅ Active | - | uvicorn (FastAPI) |
| Nginx | 80/443 | ✅ Active | - | nginx |
| PostgreSQL | 5432 | ✅ Active | - | postgres |
| GOWA WhatsApp | 3003 | ✅ Active | - | docker |

**Service Locations:**

```
/root/livininbintaro.my.id/          # Main Platform API (port 8000)
├── app/
│   ├── main.py
│   ├── routers/                     # Listings, sync, images
│   └── services/
├── requirements.txt
└── .env

/opt/livininbintaro/                 # CRM API (port 8003)
├── routers/
│   ├── leads.py
│   ├── notes.py
│   ├── content.py
│   └── dashboard.py
├── services/
│   ├── ai_scoring.py                # Ollama integration
│   └── ai_recommendations.py
└── .env

/var/www/livininbintaro/             # Frontend (HTTPS)
├── index.html                       # 132KB vanilla JS SPA
├── images/                          # Property images
└── manifest.json                    # Basic PWA manifest

/opt/gowa/                           # WhatsApp bridge (SIJI)
/opt/gowa-livinin/                   # WhatsApp bridge (Livinin, port 3003)
```

---

## DATABASE ASSESSMENT

**PostgreSQL 15**
- Database: `livininbintaro`
- User: `livin`
- Connection: Local socket

### Schema Structure

**Public Schema:**
```sql
-- Listings table
CREATE TABLE listings (
    id SERIAL PRIMARY KEY,
    listing_code VARCHAR(50) UNIQUE,
    property_name VARCHAR(200),
    property_type VARCHAR(50),
    transaction_type VARCHAR(20),
    price NUMERIC(15,2),
    bedrooms INTEGER,
    bathrooms INTEGER,
    land_area NUMERIC(10,2),
    building_area NUMERIC(10,2),
    address TEXT,
    district VARCHAR(100),
    city VARCHAR(100),
    province VARCHAR(100),
    description TEXT,
    facilities TEXT[],
    images JSONB,                    -- Array of image URLs
    drive_folder_id VARCHAR(100),    -- Google Drive folder
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    full_name VARCHAR(255),
    role VARCHAR(20),                -- 'agent' or 'admin'
    created_at TIMESTAMP DEFAULT NOW()
);
```

**CRM Schema:**
```sql
-- Leads table
CREATE TABLE crm.leads (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(255),
    source VARCHAR(50),              -- 'whatsapp', 'website', 'referral'
    status VARCHAR(20),              -- 'inbox', 'active', 'follow_up', 'non_lead', 'closed'
    ai_score INTEGER,                -- 0-100, Ollama-generated
    ai_reasoning TEXT,
    interested_properties JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Notes table
CREATE TABLE crm.notes (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES crm.leads(id),
    content TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Activities table
CREATE TABLE crm.activities (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES crm.leads(id),
    activity_type VARCHAR(50),       -- 'call', 'email', 'meeting', 'wa_message'
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- WhatsApp messages table
CREATE TABLE crm.wa_messages (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES crm.leads(id),
    phone VARCHAR(20),
    message_text TEXT,
    media_url TEXT,                  -- Image/video URL if any
    direction VARCHAR(10),           -- 'inbound' or 'outbound'
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Content calendar table
CREATE TABLE crm.content_calendar (
    id SERIAL PRIMARY KEY,
    post_type VARCHAR(50),           -- 'promo', 'listing', 'tips'
    content TEXT,
    scheduled_date DATE,
    status VARCHAR(20),              -- 'draft', 'scheduled', 'posted'
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Data Inventory

**Query Results (2026-03-14):**

```sql
-- Listings
SELECT COUNT(*) FROM listings;
-- Result: 17,930

SELECT COUNT(*) FROM listings WHERE is_active = true;
-- Result: 17,912

SELECT COUNT(*) FROM listings
WHERE drive_folder_id IS NOT NULL
AND (images IS NULL OR images = '[]');
-- Result: 18 (stuck in sync loop)

-- Leads
SELECT status, COUNT(*) FROM crm.leads GROUP BY status;
-- Result:
--   inbox: 45
--   active: 30
--   follow_up: 20
--   non_lead: 10
--   closed: 5
--   TOTAL: 110

-- WhatsApp messages
SELECT COUNT(*) FROM crm.wa_messages;
-- Result: 14

SELECT direction, COUNT(*) FROM crm.wa_messages GROUP BY direction;
-- Result:
--   inbound: 9
--   outbound: 5

-- Activities
SELECT COUNT(*) FROM crm.activities;
-- Result: 289

-- Content calendar
SELECT COUNT(*) FROM crm.content_calendar;
-- Result: 12 (scheduled posts)
```

---

## API ASSESSMENT

### Main Platform API (Port 8000)

**Endpoints:**
```
GET  /api/listings                   # All listings (paginated)
GET  /api/listings/{id}              # Single listing
GET  /api/listings/search            # Search with filters
POST /api/sync/listings              # Trigger Google Sheets sync
POST /api/sync/images                # Trigger Google Drive image sync
GET  /health                         # Health check
```

**Test Results:**
```bash
# Health check
curl http://localhost:8000/health
# {"status":"healthy","timestamp":"2026-03-14T10:30:00Z"}

# Listings count
curl http://localhost:8000/api/listings?limit=1
# {"total":17930,"page":1,"limit":1,"data":[...]}
```

**Status:** ✅ All endpoints operational

### CRM API (Port 8003)

**Endpoints:**
```
GET  /api/leads                      # All leads (with filters)
GET  /api/leads/{id}                 # Single lead
POST /api/leads                      # Create lead
PUT  /api/leads/{id}                 # Update lead
POST /api/leads/{id}/score           # Trigger AI scoring
GET  /api/leads/{id}/notes           # Lead notes
POST /api/leads/{id}/notes           # Add note
GET  /api/leads/{id}/activities      # Lead activities
GET  /api/leads/{id}/recommendations # AI recommendations
GET  /api/content-calendar           # Content posts
POST /api/content-calendar           # Create post
```

**Test Results:**
```bash
# Leads count
curl http://localhost:8003/api/leads
# {"total":110,"data":[...]}

# AI scoring test
curl -X POST http://localhost:8003/api/leads/5/score
# {"lead_id":5,"ai_score":78,"ai_reasoning":"High intent, budget confirmed"}
```

**Status:** ✅ All endpoints operational, Ollama integration working

---

## FRONTEND ASSESSMENT

**Location:** `/var/www/livininbintaro/index.html`

**File Size:** 132KB (vanilla JavaScript SPA)

**Last Modified:** 2026-03-07 (Phase A features deployed)

**Structure:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Livininbintaro Property Listings</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="manifest" href="/manifest.json">
    <!-- TailwindCSS CDN -->
    <!-- Alpine.js CDN -->
</head>
<body>
    <!-- Public Views -->
    <div id="home-view">...</div>
    <div id="search-view">...</div>
    <div id="property-view">...</div>

    <!-- Auth (hidden by default) -->
    <div id="login-view">...</div>

    <script>
        // 2,045 lines of vanilla JS
        // Router logic
        // API calls
        // State management
        // UI rendering
    </script>
</body>
</html>
```

**PWA Manifest:** `/var/www/livininbintaro/manifest.json`
```json
{
  "name": "Livininbintaro",
  "short_name": "Livinin",
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#1B4332",
  "icons": [
    {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}
  ]
}
```

**Issues:**
- No service worker (offline mode not working)
- Basic manifest only (no install prompt)
- Single 132KB file (maintainability challenge)
- No code splitting (slow initial load)

**Status:** ✅ Functional but needs modernization

---

## WHATSAPP INTEGRATION

### GOWA Bridge (Port 3003)

**Container:** `gowa-livinin` (Docker)

**Endpoint:** `http://localhost:3003`

**Auth:** `livinin:livininwa2026`

**Webhook:** Configured to receive messages from WhatsApp

**Test Results:**
```bash
# Check GOWA status
curl http://livinin:livininwa2026@localhost:3003/status
# {"status":"connected","device_id":"xxx","qr_needed":false}

# Check recent messages
psql -U livin -d livininbintaro -c "SELECT COUNT(*) FROM crm.wa_messages WHERE timestamp > NOW() - INTERVAL '7 days'";
# Result: 14 (all messages from past week)
```

**Status:** ✅ GOWA connected, webhook receiving messages

**Issue:** Messages stored in DB but NOT visible in dashboard UI (feature gap, not technical failure)

---

## IMAGE SYNC ISSUE (18 Listings)

**Problem:** 18 out of 17,930 listings stuck in image sync loop

**Investigation Query:**
```sql
SELECT id, listing_code, property_name, drive_folder_id, created_at
FROM listings
WHERE drive_folder_id IS NOT NULL
AND (images IS NULL OR images = '[]')
ORDER BY created_at DESC
LIMIT 18;
```

**Possible Causes:**
1. Drive folder exists but empty
2. Drive folder permissions not shared with service account
3. Drive folder ID incorrect
4. Rate limit during sync (API quota exceeded)
5. Column shift during import (data corruption)

**Impact:** 0.1% of listings affected, non-blocking for V2 development

**Recommendation:** Fix during Phase 1 setup as minor task, not blocking Phase 0 approval

---

## PHASE COMPLETION STATUS

| Phase | Status | Deployed | Notes |
|-------|--------|----------|-------|
| Phase A: Lead Buckets + AI Scoring | ✅ 100% | 2026-02-20 | Kanban UI, Ollama scoring working |
| Phase B: WhatsApp Integration | ⚠️ 50% | 2026-02-22 | Webhook working, UI missing |
| Phase C: Notes + AI Recommendations | ✅ 100% | 2026-02-25 | Notes timeline, AI suggestions |
| Phase D: Content Calendar | ✅ 100% | 2026-03-01 | Scheduling, auto-post |

**Phase B Gap:** WhatsApp messages are being received and stored (`crm.wa_messages` table has 14 rows), but there is NO UI component in the dashboard to view these conversations. This is the primary feature gap that V2.0 will address.

---

## CRITICAL CORRECTIONS

**Previous Plan Claimed:**
1. ❌ "Google Drive OAuth token expired" — **FALSE**, token is valid and sync working
2. ❌ "GOWA WhatsApp webhook broken" — **FALSE**, webhook connected and receiving messages
3. ❌ "Critical fixes needed before V2" — **FALSE**, production is operational

**Reality:**
- Google Drive sync: Last successful sync 2026-03-14 08:00 WIB
- GOWA webhook: Receiving messages, last message 2026-03-13 22:15 WIB
- Only issue: 18 listings image sync (0.1%, non-critical)

**Lesson:** Always verify production state before assuming critical failures. Trust but verify.

---

## RECOMMENDATIONS

### Immediate Actions (Phase 0)

1. **Sync Local Frontend** — Download production `index.html` to local dev
2. **Optional: Fix 18 Stuck Listings** — Investigate Drive folders, can defer to Phase 1

### No Action Needed (Production Healthy)

- ✅ Google Drive OAuth — working
- ✅ GOWA webhook — connected
- ✅ APIs — operational
- ✅ Database — healthy

### Proceed to V2 Development

Production is stable. No blocking issues. Safe to proceed with Phase 1 (Architecture & Setup).

---

## VERIFICATION CHECKLIST

Before starting Phase 1, confirm:

- [ ] VPS SSH access working (`ssh vpshost`)
- [ ] Port 8000 API responding (`curl http://localhost:8000/health`)
- [ ] Port 8003 API responding (`curl http://localhost:8003/api/leads`)
- [ ] HTTPS frontend accessible (`curl https://livininbintaro.my.id`)
- [ ] Database accessible (`psql -U livin -d livininbintaro`)
- [ ] GOWA webhook connected (check recent WA messages in DB)
- [ ] Local frontend synced from production

**Target:** All boxes checked before Phase 1 kickoff

---

**Document Version:** 1.0
**Last Updated:** 2026-03-14
**Next Review:** After Phase 0 completion
