# VERIFICATION CHECKLIST — LIVININBINTARO V2.0

**Version:** 1.0
**Date:** 2026-03-14
**Purpose:** Comprehensive testing checklist for each development phase

---

## HOW TO USE THIS CHECKLIST

**For Each Phase:**
1. Copy the phase checklist to a new file or issue tracker
2. Work through each item sequentially
3. Mark items as completed only after verification
4. Document any issues found in separate issue tracker
5. Do not proceed to next phase until all critical items pass

**Priority Levels:**
- ❗ **CRITICAL** - Must pass before phase completion
- ⚠️ **IMPORTANT** - Should pass, document if skipped
- ℹ️ **NICE-TO-HAVE** - Optional, can defer

---

## PHASE 0: PRODUCTION VERIFICATION

**Objective:** Validate production state before V2 development

### Production Services

```
❗ [ ] SSH access to VPS working (ssh vpshost)
❗ [ ] Port 8000 API responding (curl http://localhost:8000/health)
❗ [ ] Port 8003 CRM API responding (curl http://localhost:8003/api/leads)
❗ [ ] Nginx running and serving HTTPS (curl https://livininbintaro.my.id)
❗ [ ] PostgreSQL accessible (psql -U livin -d livininbintaro)
❗ [ ] SSL certificate valid (check expiry date)
⚠️ [ ] GOWA WhatsApp connected (curl http://livinin:password@localhost:3003/status)
⚠️ [ ] Ollama AI service running (curl http://localhost:11434/api/tags)
```

### Database Validation

```sql
-- Copy these queries to verify data integrity

❗ [ ] Listings count matches expected
SELECT COUNT(*) FROM listings;
-- Expected: 17,930

❗ [ ] Active listings count
SELECT COUNT(*) FROM listings WHERE is_active = true;
-- Expected: 17,912

❗ [ ] Leads count
SELECT COUNT(*) FROM crm.leads;
-- Expected: 110

⚠️ [ ] WhatsApp messages stored
SELECT COUNT(*) FROM crm.wa_messages;
-- Expected: 14 (may grow)

⚠️ [ ] Leads by status distribution
SELECT status, COUNT(*) FROM crm.leads GROUP BY status;
-- Expected:
--   inbox: 45
--   active: 30
--   follow_up: 20
--   non_lead: 10
--   closed: 5

ℹ️ [ ] Stuck listings identified
SELECT COUNT(*) FROM listings
WHERE drive_folder_id IS NOT NULL
AND (images IS NULL OR images = '[]');
-- Expected: 18 (known issue, non-blocking)
```

### Local Environment Sync

```
❗ [ ] V1 frontend downloaded (scp vpshost:/var/www/livininbintaro/index.html ...)
❗ [ ] V1 backend routers copied (for reference)
⚠️ [ ] Database schema documented (see 02-DATABASE-SCHEMA.md)
⚠️ [ ] .env files backed up
```

### Optional: Fix Stuck Listings

```
ℹ️ [ ] Investigate 18 stuck listings
ℹ️ [ ] Check Google Drive folder permissions
ℹ️ [ ] Trigger manual image sync
ℹ️ [ ] Verify images appear after sync

-- Can defer to Phase 1 if time-consuming
```

**Phase 0 Sign-off:** [ ] All critical items passed, ready for Phase 1

---

## PHASE 1: ARCHITECTURE & PROJECT SETUP

**Objective:** Create V2 project structure, unify backend

### Project Scaffolding

```
❗ [ ] Frontend created (npm create vite@latest frontend -- --template vue)
❗ [ ] Backend directory created (mkdir backend)
❗ [ ] Dependencies installed
    [ ] Frontend: vue-router, pinia, axios, tailwindcss, vite-plugin-pwa
    [ ] Backend: fastapi, uvicorn, sqlalchemy, psycopg2-binary, pyjwt
❗ [ ] Git repository initialized
❗ [ ] .gitignore configured (node_modules, venv, .env)
```

### Backend Unification

```
❗ [ ] main.py created with unified app structure
❗ [ ] auth.py created (JWT + RBAC middleware)
❗ [ ] config.py created (Settings with .env support)
❗ [ ] database.py created (SQLAlchemy setup)
❗ [ ] models.py created (all 7 tables mapped)
    [ ] Listing model
    [ ] User model
    [ ] Lead model
    [ ] WAMessage model
    [ ] Note model
    [ ] Activity model
    [ ] ContentCalendar model

❗ [ ] Routers created and configured:
    [ ] public.py (no auth)
    [ ] listings.py (auth required)
    [ ] leads.py (auth required)
    [ ] wa.py (auth required)
    [ ] content.py (auth required)
    [ ] dashboard.py (auth required)

⚠️ [ ] Services copied from V1:
    [ ] ai_scoring.py (Ollama integration)
    [ ] ai_recommendations.py
    [ ] gowa_client.py (WhatsApp bridge)

❗ [ ] CORS configured (allow localhost:5173, livininbintaro.my.id)
```

### Development Environment

```
❗ [ ] Backend .env created with correct credentials
❗ [ ] Frontend .env created (VITE_API_BASE_URL)
❗ [ ] Backend runs locally (uvicorn main:app --reload --port 8000)
❗ [ ] Frontend runs locally (npm run dev)
❗ [ ] Backend accessible from frontend (proxy configured in vite.config.js)

❗ [ ] Health check endpoint works
curl http://localhost:8000/health
-- Expected: {"status":"healthy","version":"2.0.0"}

❗ [ ] Database connection works
curl http://localhost:8000/api/public/listings?limit=1
-- Expected: Listings data returned
```

### Git Setup

```
⚠️ [ ] Initial commit created
⚠️ [ ] .gitignore working (sensitive files not tracked)
ℹ️ [ ] Remote repository created (optional)
```

**Phase 1 Sign-off:** [ ] All critical items passed, Erik approval received

---

## PHASE 2: FRONTEND CORE DEVELOPMENT

**Objective:** Build Vue 3 frontend with public and agent views

### Routing & Navigation

```
❗ [ ] router.js created with all routes
❗ [ ] Navigation guards implemented (auth check)
❗ [ ] App.vue created with layout structure
❗ [ ] NavBar component created (public vs agent nav)
❗ [ ] Footer component created

❗ [ ] Route navigation works:
    [ ] / → HomePage
    [ ] /search → SearchPage
    [ ] /property/:slug → PropertyDetail
    [ ] /login → LoginPage
    [ ] /dashboard → DashboardPage (auth required)
    [ ] /leads → LeadsPage (auth required)
    [ ] /leads/:id → LeadDetailPage (auth required)
```

### API Client Layer

```
❗ [ ] client.js created (Axios instance)
❗ [ ] JWT interceptor configured (attach token to requests)
❗ [ ] 401 interceptor configured (redirect to login)
❗ [ ] API modules created:
    [ ] listings.js (getAll, getById, search)
    [ ] leads.js (getAll, getById, create, update, scoreAI)
    [ ] wa.js (getMessages, sendMessage)
    [ ] content.js (getAll, create, update)
    [ ] dashboard.js (getStats, getTodayTasks)
```

### State Management (Pinia)

```
❗ [ ] store.js created with Pinia setup
❗ [ ] Stores implemented:
    [ ] useAuthStore (login, logout, user state)
    [ ] useListingsStore (fetchListings, pagination)
    [ ] useLeadsStore (fetchLeads, updateLeadStatus, currentLead)

❗ [ ] State persistence works (token in localStorage)
❗ [ ] Store actions work (test API calls)
```

### Public Views

```
❗ [ ] HomePage.vue created
    [ ] Hero section displays
    [ ] Featured listings load (3 cards)
    [ ] Stats section shows correct numbers
    [ ] Links to /search work

❗ [ ] SearchPage.vue created
    [ ] Search filters display
    [ ] Listings grid loads
    [ ] Pagination works
    [ ] Filters work (property type, price range)
    [ ] Results count displays

❗ [ ] PropertyDetail.vue created
    [ ] Property data loads from API
    [ ] Image gallery displays
    [ ] Property specs show (bedrooms, bathrooms, area)
    [ ] Description displays
    [ ] Price formats correctly (IDR)

❗ [ ] LoginPage.vue created
    [ ] Form validation works
    [ ] Login API call works
    [ ] JWT token stored
    [ ] Redirect to /dashboard after login
    [ ] Error handling (wrong password)
```

### Agent Views

```
❗ [ ] DashboardPage.vue created
    [ ] Stats cards display (leads count, properties count)
    [ ] Today's tasks section loads
    [ ] Recent activity timeline displays

❗ [ ] LeadsPage.vue created (Kanban)
    [ ] 5 columns display (Inbox, Active, Follow Up, Non-Lead, Closed)
    [ ] Lead cards render in correct columns
    [ ] Drag-and-drop works
    [ ] Status updates on drop
    [ ] Lead count badges show

❗ [ ] LeadDetailPage.vue created
    [ ] Lead info displays (name, phone, email)
    [ ] AI score badge shows
    [ ] Tabs work (WA, Notes, Activities, AI)
    [ ] WhatsApp tab placeholder ready (Phase 3)
    [ ] Notes tab displays timeline
    [ ] Activities tab displays timeline
    [ ] AI recommendations tab placeholder ready

⚠️ [ ] ContentCalendar.vue created
    [ ] Calendar view displays
    [ ] Scheduled posts show
    [ ] Create post form works

⚠️ [ ] ListingsManage.vue created
    [ ] Listings table displays
    [ ] Edit/deactivate actions work
```

### Reusable Components

```
❗ [ ] PropertyCard.vue created
    [ ] Image displays
    [ ] Property name, district, price show
    [ ] Bedrooms, bathrooms, area display
    [ ] Link to detail page works

❗ [ ] LeadCard.vue created
    [ ] Lead name, phone display
    [ ] Source badge shows
    [ ] AI score badge displays

⚠️ [ ] KanbanColumn.vue created
    [ ] Column title displays
    [ ] Lead cards render
    [ ] Drag-drop handlers work

⚠️ [ ] AIScoreBadge.vue created
    [ ] Color based on score (hot/warm/cool/cold)
    [ ] Tooltip shows reasoning

⚠️ [ ] Timeline.vue created
    [ ] Notes display chronologically
    [ ] Activities display chronologically
    [ ] Add note form works
```

### Styling & Responsiveness

```
❗ [ ] TailwindCSS configured
❗ [ ] Mobile responsive (test on 375px width)
    [ ] HomePage mobile-friendly
    [ ] SearchPage mobile-friendly
    [ ] PropertyDetail mobile-friendly
    [ ] Dashboard mobile-friendly
    [ ] Kanban scrolls horizontally on mobile

⚠️ [ ] Dark mode support (optional, can defer)
```

### Testing

```
❗ [ ] Manual testing completed:
    [ ] All public pages accessible
    [ ] All agent pages accessible (after login)
    [ ] Navigation works (click all links)
    [ ] Forms work (login, search, add note)
    [ ] API calls work (check Network tab)
    [ ] No console errors

⚠️ [ ] Cross-browser testing:
    [ ] Chrome
    [ ] Safari
    [ ] Mobile Chrome
    [ ] Mobile Safari

ℹ️ [ ] Lighthouse score >90 (can optimize in Phase 5)
```

**Phase 2 Sign-off:** [ ] All critical items passed, frontend functional

---

## PHASE 3: WHATSAPP INTEGRATION

**Objective:** Display WhatsApp conversations in lead detail

### Backend WhatsApp API

```
❗ [ ] routers/wa.py created
❗ [ ] Endpoints implemented:
    [ ] GET /api/wa/messages/{lead_id}
    [ ] POST /api/wa/send
    [ ] POST /api/webhook/gowa

❗ [ ] Webhook endpoint works:
    [ ] Receives POST from GOWA
    [ ] Parses message payload
    [ ] Creates lead if phone not found
    [ ] Stores message in crm.wa_messages
    [ ] Returns 200 OK

❗ [ ] GOWA client service created (services/gowa_client.py)
    [ ] send_message() method works
    [ ] get_status() method works
    [ ] Authentication configured

❗ [ ] Test webhook locally:
curl -X POST http://localhost:8000/api/webhook/gowa \
  -H "Content-Type: application/json" \
  -d '{
    "from": "628123456789",
    "name": "Test User",
    "message": "Test message",
    "media_url": null
  }'
-- Expected: Lead created, message stored
```

### Frontend WhatsApp Components

```
❗ [ ] WAConversation.vue created
    [ ] Messages load from API
    [ ] Messages display chronologically
    [ ] Inbound messages aligned left (white bubble)
    [ ] Outbound messages aligned right (green bubble)
    [ ] Media (images) display inline
    [ ] Timestamp formats correctly (id-ID locale)
    [ ] Reply input field works
    [ ] Send message API call works
    [ ] New message appends to conversation

❗ [ ] Integrated into LeadDetailPage.vue
    [ ] WhatsApp tab shows WAConversation component
    [ ] Component loads with lead_id prop
    [ ] Tab switches work
    [ ] No errors when no messages exist
```

### API Integration

```
❗ [ ] api/wa.js created
    [ ] getMessages(leadId) works
    [ ] sendMessage(leadId, message) works

❗ [ ] Test API calls from frontend:
// DevTools console
const messages = await api.wa.getMessages(1)
console.log(messages.data)
-- Expected: Array of messages
```

### GOWA Integration

```
⚠️ [ ] GOWA webhook configured
    [ ] Webhook URL set to https://livininbintaro.my.id/api/webhook/gowa
    [ ] Test message sent from WhatsApp
    [ ] Message appears in database
    [ ] Message appears in frontend conversation

⚠️ [ ] Outbound messages work
    [ ] Send message from frontend
    [ ] Message delivered to WhatsApp
    [ ] Message appears in conversation

❗ [ ] Error handling:
    [ ] GOWA down → graceful error message
    [ ] Network error → retry logic
    [ ] Invalid phone number → validation error
```

### Testing

```
❗ [ ] End-to-end test:
    [ ] Send WhatsApp message to 6281288783088
    [ ] Webhook receives message
    [ ] Lead created (if new)
    [ ] Message stored in database
    [ ] Message appears in frontend
    [ ] Reply from frontend
    [ ] Reply delivered to WhatsApp
    [ ] Reply appears in frontend

⚠️ [ ] Edge cases:
    [ ] Lead without messages (empty conversation)
    [ ] Message with image (media_url)
    [ ] Very long message (text wrapping)
    [ ] Multiple rapid messages (order maintained)
```

**Phase 3 Sign-off:** [ ] All critical items passed, WhatsApp integration functional

---

## PHASE 4: PWA ENHANCEMENTS

**Objective:** Implement service worker, offline mode, push notifications

### Service Worker Setup

```
❗ [ ] vite-plugin-pwa installed
❗ [ ] vite.config.js configured with PWA plugin
❗ [ ] Manifest.json generated
    [ ] name: "Livininbintaro Property Marketplace"
    [ ] short_name: "Livinin"
    [ ] theme_color: "#1B4332"
    [ ] icons: 8 sizes (72, 96, 128, 144, 152, 192, 384, 512)
    [ ] display: "standalone"
    [ ] start_url: "/"

❗ [ ] Service worker registers on load
// DevTools → Application → Service Workers
-- Expected: sw.js registered, activated

❗ [ ] Workbox caching configured:
    [ ] App shell cached (HTML, CSS, JS)
    [ ] API listings cached (NetworkFirst)
    [ ] Listing detail cached (CacheFirst)
    [ ] Images cached (CacheFirst)
    [ ] CRM data NOT cached (NetworkOnly)
```

### Offline Mode

```
❗ [ ] useOffline composable created
    [ ] isOnline reactive ref works
    [ ] Detects online/offline events
    [ ] showOfflineBanner updates correctly

❗ [ ] Offline banner component created
    [ ] Shows when offline
    [ ] Hides when online (with 3s delay)
    [ ] Displays correct message

❗ [ ] Test offline mode:
    [ ] Go to /search
    [ ] DevTools → Network → Offline
    [ ] Refresh page
    [ ] Expected: Page loads from cache
    [ ] Listings display (from cache)
    [ ] Images display (from cache)
    [ ] "You are offline" banner shows

    [ ] Go back online
    [ ] Expected: "Back online" banner shows
    [ ] New API calls work
    [ ] Cache updates
```

### Offline Queue

```
❗ [ ] useOfflineQueue composable created
    [ ] addToQueue() stores action in localStorage
    [ ] processQueue() executes queued actions when online
    [ ] Retry logic works (max 3 retries)
    [ ] Failed items removed after max retries

❗ [ ] Integrated into API client
    [ ] Network errors queue failed requests
    [ ] Queue processes automatically when back online

❗ [ ] Test offline queue:
    [ ] Login to dashboard
    [ ] Go to lead detail
    [ ] Go offline
    [ ] Add note to lead
    [ ] Expected: "Action queued" message
    [ ] Check localStorage → livinin-offline-queue
    [ ] Expected: Queue item present

    [ ] Go back online
    [ ] Expected: Queue processes automatically
    [ ] Note appears in timeline
    [ ] Queue empty in localStorage
```

### Push Notifications

```
⚠️ [ ] Backend push notification service created (services/notifications.py)
    [ ] VAPID keys generated
    [ ] webpush library installed
    [ ] send_notification() method works

⚠️ [ ] Backend notification endpoints created:
    [ ] POST /api/notifications/subscribe
    [ ] POST /api/notifications/notify/{user_id}

⚠️ [ ] Frontend push composable created (usePushNotifications.js)
    [ ] requestPermission() works
    [ ] subscribeToPush() works
    [ ] Subscription sent to backend

⚠️ [ ] PushNotificationPrompt component created
    [ ] Shows after 30 seconds (if not dismissed)
    [ ] "Enable" button requests permission
    [ ] "Not Now" dismisses (stores in localStorage)

⚠️ [ ] Test push notifications:
    [ ] Enable notifications when prompted
    [ ] Trigger test notification from backend
    [ ] Expected: Notification appears
    [ ] Click notification → opens app
    [ ] Notification shows correct title/body/icon

ℹ️ [ ] Auto-send notifications:
    [ ] New lead created → push to agent
    [ ] Follow-up reminder → push notification
```

### Install Prompt

```
❗ [ ] useInstallPrompt composable created
    [ ] beforeinstallprompt event captured
    [ ] deferredPrompt stored
    [ ] showInstallPrompt shows after 10s

❗ [ ] InstallPrompt component created
    [ ] Shows custom prompt (not browser default)
    [ ] "Install Now" triggers native prompt
    [ ] Dismiss stores in localStorage

❗ [ ] Test install prompt:
    [ ] Open site in Chrome (desktop/mobile)
    [ ] Wait 10 seconds
    [ ] Expected: Install prompt appears
    [ ] Click "Install Now"
    [ ] Expected: Native install dialog appears
    [ ] Confirm install
    [ ] Expected: App icon added to home screen/app drawer
    [ ] Open installed app
    [ ] Expected: Standalone mode (no browser UI)
```

### PWA Validation

```
❗ [ ] Lighthouse PWA audit:
npm install -g lighthouse
lighthouse https://livininbintaro.my.id --view

-- Expected scores:
Performance: >90
Accessibility: >90
Best Practices: >90
SEO: >90
PWA: Installable ✓

❗ [ ] PWA checklist passed:
    [ ] Served over HTTPS
    [ ] Registers service worker
    [ ] Responds with 200 when offline
    [ ] Contains valid manifest
    [ ] Contains icons (192x192, 512x512)
    [ ] Provides custom offline page (optional)
    [ ] Page load fast on 3G (<5s)

⚠️ [ ] iOS PWA support:
    [ ] Meta tags added for iOS
    [ ] Apple touch icons configured
    [ ] Add to home screen works on Safari iOS
    [ ] Standalone mode works on iOS
```

**Phase 4 Sign-off:** [ ] All critical items passed, PWA features working

---

## PHASE 5: VPS DEPLOYMENT & CUTOVER

**Objective:** Deploy V2 to production with zero downtime

### Pre-Deployment

```
❗ [ ] Frontend production build successful
    [ ] npm run build completes
    [ ] dist/ folder created
    [ ] Bundle size <500KB gzipped
    [ ] No build warnings/errors

❗ [ ] Backend production-ready
    [ ] requirements.txt updated
    [ ] .env.production template created
    [ ] No hardcoded secrets
    [ ] Database migrations ready (if any)

❗ [ ] Deployment package created
    [ ] Tarball created (livininbintaro-v2.0-YYYYMMDD.tar.gz)
    [ ] Package size reasonable (<10MB)
```

### Staging Deployment

```
❗ [ ] Uploaded to VPS (/opt/livininbintaro-v2-staging)
❗ [ ] Backend setup:
    [ ] venv created
    [ ] Dependencies installed
    [ ] .env configured with production credentials
    [ ] Service runs (systemctl start livininbintaro-v2-staging)
    [ ] API responds (curl http://localhost:8100/health)

❗ [ ] Frontend deployed:
    [ ] Files copied to /var/www/livininbintaro-v2-staging
    [ ] Permissions set (www-data:www-data)

❗ [ ] Nginx staging subdomain configured:
    [ ] staging.livininbintaro.my.id config created
    [ ] nginx -t passes
    [ ] nginx reload successful
    [ ] HTTPS works (SSL cert valid)
    [ ] Site loads (curl https://staging.livininbintaro.my.id)
```

### Staging Testing

```
❗ [ ] Automated API tests:
    [ ] Health check: /api/health
    [ ] Public listings: /api/public/listings
    [ ] Login: /api/auth/login
    [ ] Protected endpoint: /api/leads (with JWT)

❗ [ ] Frontend testing:
    [ ] All pages load (<2s)
    [ ] Login works
    [ ] Dashboard displays
    [ ] Kanban drag-drop works
    [ ] WhatsApp conversation displays
    [ ] Offline mode works
    [ ] Service worker registers

❗ [ ] Performance testing:
    [ ] Lighthouse score >90
    [ ] First Contentful Paint <1.5s
    [ ] Time to Interactive <3s

⚠️ [ ] Load testing (optional):
    [ ] ab -n 1000 -c 10 (API endpoint)
    [ ] Requests per second >100
    [ ] No failed requests
```

### Production Cutover

```
❗ [ ] Backups created:
    [ ] V1 files backed up (/var/www/livininbintaro-v1-backup-YYYYMMDD)
    [ ] V1 nginx config backed up
    [ ] Database backed up (pg_dump)

❗ [ ] V2 deployed to production:
    [ ] Files copied to /opt/livininbintaro-v2
    [ ] Frontend copied to /var/www/livininbintaro-v2
    [ ] Service started (systemctl start livininbintaro-v2)
    [ ] Service enabled (systemctl enable livininbintaro-v2)

❗ [ ] Nginx updated:
    [ ] Production config updated to point to V2
    [ ] nginx -t passes
    [ ] nginx reload successful (CUTOVER!)

❗ [ ] Verify cutover:
    [ ] curl https://livininbintaro.my.id
    [ ] Expected: V2 frontend loads
    [ ] curl https://livininbintaro.my.id/api/health
    [ ] Expected: {"status":"healthy","version":"2.0.0"}
    [ ] Open in browser
    [ ] Expected: V2 UI displays

⚠️ [ ] Rollback plan tested:
    [ ] Know how to restore V1 nginx config
    [ ] Know how to restart V1 services
    [ ] Documented in 05-DEPLOYMENT-GUIDE.md
```

### Post-Deployment Monitoring

```
❗ [ ] Logs monitored (first 30 minutes):
    [ ] journalctl -u livininbintaro-v2 -f
    [ ] tail -f /var/log/nginx/livininbintaro.access.log
    [ ] tail -f /var/log/nginx/livininbintaro.error.log
    [ ] No critical errors

❗ [ ] Metrics healthy:
    [ ] Service status: active (running)
    [ ] Memory usage: <500MB per worker
    [ ] Response time: <100ms
    [ ] Database connections: <20

⚠️ [ ] Real-user monitoring:
    [ ] Ocha tests dashboard
    [ ] Ocha tests lead detail + WhatsApp
    [ ] No critical bugs reported

⚠️ [ ] Security checks:
    [ ] .env file permissions: 600
    [ ] SSL certificate valid
    [ ] HTTPS redirect works
    [ ] Security headers present
```

**Phase 5 Sign-off:** [ ] All critical items passed, V2 live in production

---

## FINAL TESTING & HANDOFF

**Objective:** Bug fixes, user testing, documentation

### Bug Fixes

```
⚠️ [ ] All critical bugs fixed (from staging/production testing)
⚠️ [ ] All important bugs fixed or documented
ℹ️ [ ] Nice-to-have bugs deferred to backlog
```

### User Testing (Ocha)

```
❗ [ ] Ocha walkthrough completed:
    [ ] Login works
    [ ] Dashboard makes sense
    [ ] Kanban intuitive (drag-drop discovered)
    [ ] Lead detail clear (tabs make sense)
    [ ] WhatsApp conversation useful
    [ ] Can add notes
    [ ] Can view AI recommendations
    [ ] Content calendar usable

❗ [ ] Feedback documented:
    [ ] Critical UX issues fixed
    [ ] Enhancement requests logged

⚠️ [ ] Mobile testing (Ocha's phone):
    [ ] App installed from Chrome
    [ ] All features work on mobile
    [ ] Touch interactions smooth
    [ ] No layout issues
```

### Performance Optimization

```
⚠️ [ ] Bundle size optimized:
    [ ] Code splitting implemented
    [ ] Lazy loading for routes
    [ ] Images lazy loaded

⚠️ [ ] Lighthouse scores:
    [ ] Performance: >90
    [ ] Accessibility: >90
    [ ] Best Practices: >90
    [ ] SEO: >90
    [ ] PWA: Installable

ℹ️ [ ] SEO optimized:
    [ ] Meta tags configured
    [ ] Sitemap generated
    [ ] robots.txt configured
```

### Documentation

```
❗ [ ] All 7 docs completed:
    [ ] 00-OVERVIEW.md
    [ ] 01-PRODUCTION-ASSESSMENT.md
    [ ] 02-ARCHITECTURE.md
    [ ] 03-IMPLEMENTATION-PHASES.md
    [ ] 04-API-ENDPOINTS.md
    [ ] 05-DEPLOYMENT-GUIDE.md
    [ ] 06-PWA-FEATURES.md
    [ ] 07-VERIFICATION-CHECKLIST.md (this file)

⚠️ [ ] User guide created (for Ocha)
    [ ] How to use Kanban
    [ ] How to view WhatsApp conversations
    [ ] How to add notes
    [ ] How to use content calendar

⚠️ [ ] Maintenance guide created (for Erik/Bob)
    [ ] How to update frontend
    [ ] How to update backend
    [ ] How to restart services
    [ ] How to rollback
    [ ] Common troubleshooting
```

### Handoff

```
❗ [ ] Erik review session completed
❗ [ ] Ocha training session completed
⚠️ [ ] Credentials documented securely
⚠️ [ ] Monitoring setup (optional)
ℹ️ [ ] Backup schedule configured (optional)
```

---

## ACCEPTANCE CRITERIA (FINAL)

**V2.0 is considered complete when:**

```
✅ All Phase 0-5 critical items passed
✅ Production deployment successful
✅ Ocha can use all features without assistance
✅ No critical bugs in production
✅ Lighthouse PWA score >90
✅ All 8 documentation files complete
✅ Erik approves final product
```

---

## ISSUE TRACKING TEMPLATE

**For each failed checklist item, create issue:**

```markdown
## Issue: [Brief description]

**Phase:** [0-5]
**Priority:** [Critical / Important / Nice-to-have]
**Checklist Item:** [Exact text from checklist]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Environment
- Browser: [Chrome 120 / Safari 17 / Mobile Chrome]
- Device: [Desktop / iPhone 13 / Android]
- URL: [Staging / Production]

### Screenshots
[If applicable]

### Logs
```
[Relevant logs]
```

### Fix Required By
[Before proceeding to next phase / Before production / Can defer]
```

---

**Document Version:** 1.0
**Last Updated:** 2026-03-14
**Next Review:** After each phase completion
