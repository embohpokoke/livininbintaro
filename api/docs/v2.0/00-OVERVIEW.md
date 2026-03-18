# LIVININBINTARO V2.0 — PROJECT OVERVIEW

**Created:** 2026-03-14
**Owner:** Erik Mahendra (tech enabler) + Ocha (operations)
**Objective:** Transform Livininbintaro into unified PWA with integrated CRM dashboard

---

## EXECUTIVE SUMMARY

Livininbintaro V2.0 is a complete architectural transformation from a dual-app system (separate public site + CRM dashboard) to a **unified Progressive Web App** that seamlessly combines:

- **Public property marketplace** (17,930 listings)
- **Agent CRM dashboard** (110 leads, Kanban pipeline, AI scoring)
- **WhatsApp conversation integration** (14 messages in DB, growing)
- **Production-grade PWA** (offline mode, push notifications, installable)

### Current Pain Points Being Solved

1. **Split User Experience**
   - Dashboard at separate subdomain (dashboard.livininbintaro.my.id)
   - Ocha switches between 2 apps to manage leads + view listings
   - No unified navigation

2. **WhatsApp Isolation**
   - 14 WA messages stored in DB but NOT visible in dashboard
   - Must check WhatsApp app separately
   - No conversation history when viewing leads

3. **Mobile Experience Gap**
   - Basic PWA manifest exists but incomplete
   - No offline caching
   - No install prompt
   - No push notifications

4. **Technical Debt**
   - Dual backends (port 8000 + 8003)
   - Vanilla JS frontend (2,045 lines in single file)
   - Difficult to maintain and extend

---

## BUSINESS CONTEXT

**Property Management Workflow:**
- Ocha manages 17,930 listings (synced from Google Sheets)
- 110 active leads across 5-stage pipeline (Inbox → Active → Follow Up → Non-Lead → Closed)
- Daily WhatsApp follow-ups with prospects
- On-site visits requiring quick mobile access to property data
- Fast-moving market = response time critical

**Current Friction:**
- Desktop-only workflow (no mobile optimization)
- Must open multiple apps (site, dashboard, WhatsApp) to handle one lead
- No offline access (site visits without network = can't show properties)
- Manual follow-up tracking (no notifications)

**Strategic Goal:**
ONE unified PWA where Ocha can:
- See everything: listings + leads + WhatsApp conversations
- Work anywhere: mobile-optimized, installable app
- Work offline: cached property data for field visits
- Stay on top: push notifications for new leads and follow-ups

---

## TRANSFORMATION STRATEGY

### From (V1):
```
┌─────────────────────┐     ┌──────────────────────┐
│  Public Site        │     │  CRM Dashboard       │
│  (vanilla JS 132KB) │     │  (separate subdomain)│
│  livininbintaro.id  │     │  dashboard.livinin*  │
└─────────────────────┘     └──────────────────────┘
         ↓                            ↓
   Backend 8000              Backend 8003
   (listings API)            (CRM API)
         ↓                            ↓
   ┌────────────────────────────────────┐
   │   PostgreSQL (dual schema)         │
   │   public + crm                     │
   └────────────────────────────────────┘
```

### To (V2):
```
┌────────────────────────────────────────────────┐
│      UNIFIED PWA: livininbintaro.my.id        │
├────────────────────────────────────────────────┤
│ PUBLIC VIEW          │  AGENT VIEW             │
│ ├─ Home              │  ├─ Dashboard           │
│ ├─ Search            │  ├─ Leads Kanban        │
│ └─ Property Detail   │  ├─ Lead Detail + WA    │
│                      │  ├─ Content Calendar    │
│                      │  └─ Listings Mgmt       │
└────────────────────────────────────────────────┘
                      ↓
        Unified Backend (port 8000)
        FastAPI + JWT + RBAC
                      ↓
        ┌────────────────────────┐
        │   PostgreSQL           │
        │   (same DB, no change) │
        └────────────────────────┘
```

---

## KEY FEATURES (V2)

### 1. Unified App Architecture
- Single domain, single codebase
- Vue 3 SPA with Vue Router
- Role-based routing (public vs agent views)
- Seamless navigation

### 2. WhatsApp Integration
- Conversations visible in lead detail
- Full message history from `crm.wa_messages`
- Inline reply capability
- Media display (images from `media_url` column)

### 3. Production-Grade PWA
- **Offline Mode:** Cache app shell + listings for field visits
- **Push Notifications:** New leads, follow-up reminders
- **Install Prompt:** Add to home screen
- **Background Sync:** Queue actions when offline

### 4. Unified Backend
- Single FastAPI app (merge 8000 + 8003)
- JWT authentication + RBAC
- Shared auth middleware
- Combined routers (listings, leads, wa, content, dashboard)

### 5. Mobile-First Design
- TailwindCSS responsive layouts
- Touch-optimized interactions
- Fast loading (<2s initial load)
- Lazy loading images

---

## PRODUCTION ASSESSMENT SUMMARY

**Infrastructure (VPS Hostinger - 72.60.78.181):**

| Component | Status | Notes |
|-----------|--------|-------|
| Port 8000 - Main API | ✅ Active | 13+ hours uptime, listings sync working |
| Port 8003 - CRM API | ✅ Active | 110 leads, AI scoring operational |
| HTTPS Frontend | ✅ Active | 132KB vanilla JS, last updated 2026-03-07 |
| PostgreSQL 15 | ✅ Healthy | 17,930 listings, 110 leads, 14 WA messages |
| Google Drive OAuth | ✅ Working | Token valid, sync operational |
| GOWA WhatsApp | ✅ Connected | Webhook receiving messages |

**Data Inventory:**
- **Listings:** 17,930 total
- **Leads:** 110 (Inbox: 45, Active: 30, Follow Up: 20, Non-Lead: 10, Closed: 5)
- **Activities:** 289 logged actions
- **WA Messages:** 14 (stored, not visible in UI)
- **Content Calendar:** Active posts

**Phase Completion:**
- ✅ Phase A: Lead Buckets + AI Scoring (100%)
- ✅ Phase B: WhatsApp Integration (webhook working, UI missing)
- ✅ Phase C: Notes + AI Recommendations (100%)
- ✅ Phase D: Content Calendar (100%)

**Issues Found:**
- 18 listings stuck in image sync (0.1% of total, non-blocking)
- Dashboard on separate subdomain (by design, UX friction)
- No WhatsApp UI in dashboard (feature gap)
- Basic PWA (no offline/push)

**Critical Correction:** Previous plan claimed Google token expired and GOWA broken. Both are FALSE. Production is healthy and operational.

---

## SUCCESS METRICS

| Metric | Current (V1) | Target (V2) | Measurement |
|--------|--------------|-------------|-------------|
| Lead Response Time | Unknown | <30 min | Track first response timestamp |
| Mobile Usage | ~60% | >80% | Analytics user agent |
| Install Rate | N/A | >30% | Track install events |
| Offline Usage | 0% | >10% | Service worker cache hits |
| Ocha Satisfaction | 7/10 | 9/10 | Verbal feedback after 2 weeks |
| Page Load Time | ~3s | <2s | Lighthouse score >90 |

---

## TIMELINE

| Phase | Duration | Key Milestone |
|-------|----------|---------------|
| Phase 0: Verification | 1 day | Production validated, local synced |
| Phase 1: Setup | 5 days | Project scaffolded, backend unified |
| Phase 2: Frontend | 7 days | Public + dashboard views working |
| Phase 3: WhatsApp | 5 days | WA conversations visible |
| Phase 4: PWA | 5 days | Offline + push working |
| Phase 5: Deploy | 3 days | V2 live in production |
| Testing | 3 days | Bug fixes, Ocha training |
| **Total** | **29 days** | |

**Critical Path:** Phase 0 → 1 → 2 → (3 + 4 parallel) → 5

---

## RISK MITIGATION

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| VPS downtime during deploy | High | Low | Blue-green deployment, staging first, rollback ready |
| Vue learning curve | Medium | Medium | Use Composition API, code examples, pair programming |
| Performance regression | Medium | Low | Code-splitting, lazy loading, monitor bundle size |
| Offline queue bugs | High | Medium | Persist to localStorage, retry logic, extensive testing |

---

## TEAM

**Erik Mahendra** — Tech Enabler / CTO
- Strategy, architecture, oversight
- NOT daily operations

**Ocha** — Property Agent / Operations Lead
- Primary user of dashboard
- Manages leads, listings, WhatsApp follow-ups
- Field visits, client meetings

**Asmuni (AI Agent)** — Strategic Orchestrator
- Plan execution, coordination
- Delegate technical work to Bob

**Bob (AI Agent)** — Technical Builder
- Coding, deployment, VPS operations
- Workspace: `~/clawd/agents/bob/`

---

## NEXT STEPS

1. ✅ **Documentation Complete** (this file + 6 others)
2. **Phase 0:** Verify production, sync local frontend
3. **Phase 1:** Setup V2 project structure
4. **Erik Review:** Approve before proceeding to Phase 2

---

**Document Version:** 1.0
**Last Updated:** 2026-03-14
**Next Review:** After Phase 1 completion
