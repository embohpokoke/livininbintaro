# V2.0 ARCHITECTURE — UNIFIED PWA DESIGN

**Version:** 2.0
**Date:** 2026-03-14
**Architect:** Asmuni + Bob (AI Agents)

---

## ARCHITECTURAL PRINCIPLES

1. **Unified Experience** — One app, not two. Seamless navigation public ↔ agent views.
2. **Mobile-First** — Touch-optimized, fast loading, installable PWA.
3. **Offline-Capable** — Service worker caching for field visits without network.
4. **Role-Based Access** — JWT + RBAC at both frontend router and backend API.
5. **Progressive Enhancement** — Works without JavaScript (SEO), enhanced with JS.
6. **Zero Database Migration** — Reuse existing PostgreSQL schema, no breaking changes.

---

## SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                 LIVININBINTARO V2.0 PWA                     │
│                https://livininbintaro.my.id                 │
└─────────────────────────────────────────────────────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         │                                     │
┌────────▼────────┐                  ┌────────▼────────┐
│  PUBLIC VIEWS   │                  │  AGENT VIEWS    │
│  (unauthenticated)                 │  (authenticated) │
├─────────────────┤                  ├─────────────────┤
│ • Home          │                  │ • Dashboard     │
│ • Search        │                  │ • Leads Kanban  │
│ • Property      │                  │ • Lead Detail   │
│   Detail        │                  │   + WA Thread   │
│ • Login         │                  │ • Content Cal   │
└─────────────────┘                  │ • Listings Mgmt │
                                     └─────────────────┘
         │                                     │
         └──────────────────┬──────────────────┘
                            │
                   ┌────────▼────────┐
                   │  VUE 3 FRONTEND │
                   │  Vite + Router  │
                   │  + Pinia Store  │
                   │  + TailwindCSS  │
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │  SERVICE WORKER │
                   │  Workbox Cache  │
                   │  + Push Notif   │
                   │  + Offline Queue│
                   └────────┬────────┘
                            │
                            │ HTTPS (443)
                            ▼
                   ┌────────────────┐
                   │  NGINX REVERSE │
                   │  PROXY + SSL   │
                   └────────┬───────┘
                            │
         ┌──────────────────┴──────────────────┐
         │                                     │
         │ /api/public/*                      │ /api/leads/*
         │ /api/listings/*                    │ /api/wa/*
         │ (no auth)                          │ (JWT required)
         │                                     │
         └──────────────────┬──────────────────┘
                            │
                   ┌────────▼────────┐
                   │ UNIFIED FASTAPI │
                   │  Port 8000      │
                   │                 │
                   │ • JWT Auth      │
                   │ • RBAC          │
                   │ • Routers:      │
                   │   - public      │
                   │   - listings    │
                   │   - leads       │
                   │   - wa          │
                   │   - content     │
                   │   - dashboard   │
                   └────────┬────────┘
                            │
         ┌──────────────────┴──────────────────┐
         │                                     │
┌────────▼────────┐               ┌───────────▼──────────┐
│  POSTGRESQL 15  │               │  EXTERNAL SERVICES   │
│                 │               ├──────────────────────┤
│ • public schema │               │ • Google Drive API   │
│   (listings)    │               │ • GOWA WhatsApp      │
│ • crm schema    │               │ • Ollama AI          │
│   (leads, wa)   │               │ • Web Push Service   │
└─────────────────┘               └──────────────────────┘
```

---

## FRONTEND ARCHITECTURE

### Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Framework | Vue 3 (Composition API) | Reactive, component-based, <50KB gzipped |
| Build Tool | Vite | Fast HMR, code-splitting, tree-shaking |
| Router | Vue Router 4 | SPA routing, navigation guards |
| State | Pinia | Type-safe, dev tools, SSR-ready |
| Styling | TailwindCSS | Utility-first, responsive, small bundle |
| PWA | Vite PWA Plugin | Production-ready service worker |
| HTTP | Axios | Interceptors for JWT, retry logic |

### Directory Structure

```
frontend/
├── src/
│   ├── main.js                      # App entry point
│   ├── App.vue                      # Root component
│   ├── router.js                    # Vue Router config
│   ├── store.js                     # Pinia store
│   │
│   ├── api/                         # API client layer
│   │   ├── client.js                # Axios instance + interceptors
│   │   ├── listings.js              # Listings endpoints
│   │   ├── leads.js                 # Leads endpoints
│   │   └── wa.js                    # WhatsApp endpoints
│   │
│   ├── components/                  # Reusable components
│   │   ├── PropertyCard.vue
│   │   ├── LeadCard.vue
│   │   ├── KanbanBoard.vue          # Drag-drop Kanban
│   │   ├── WAConversation.vue       # WA thread view
│   │   ├── AIScoreBadge.vue
│   │   └── Timeline.vue
│   │
│   ├── views/                       # Page components
│   │   ├── public/
│   │   │   ├── HomePage.vue
│   │   │   ├── SearchPage.vue
│   │   │   └── PropertyDetail.vue
│   │   └── agent/
│   │       ├── DashboardPage.vue
│   │       ├── LeadsPage.vue        # Kanban view
│   │       ├── LeadDetailPage.vue   # With WA tab
│   │       ├── ContentCalendar.vue
│   │       └── ListingsManage.vue
│   │
│   └── utils/
│       ├── auth.js                  # JWT helpers
│       ├── offline.js               # Offline queue
│       └── push.js                  # Push notifications
│
├── public/
│   ├── manifest.json                # PWA manifest
│   └── icons/                       # App icons (192, 512)
│
├── index.html
├── vite.config.js                   # Vite + PWA config
└── package.json
```

### Component Hierarchy

```
App.vue
├── NavBar (public vs agent nav)
├── Router View
│   ├── Public Routes (/)
│   │   ├── HomePage
│   │   │   ├── HeroSection
│   │   │   ├── FeaturedListings (PropertyCard x3)
│   │   │   └── StatsSection
│   │   ├── SearchPage
│   │   │   ├── SearchFilters
│   │   │   └── PropertyGrid (PropertyCard x20, infinite scroll)
│   │   └── PropertyDetail
│   │       ├── ImageGallery
│   │       ├── PropertySpecs
│   │       ├── DescriptionSection
│   │       └── InquireButton
│   │
│   └── Agent Routes (/dashboard)
│       ├── DashboardPage
│       │   ├── StatsCards
│       │   ├── TodayTasks
│       │   └── RecentActivity
│       ├── LeadsPage
│       │   └── KanbanBoard
│       │       ├── KanbanColumn (Inbox) [LeadCard x5]
│       │       ├── KanbanColumn (Active) [LeadCard x3]
│       │       ├── KanbanColumn (Follow Up) [LeadCard x2]
│       │       ├── KanbanColumn (Non-Lead) [LeadCard x1]
│       │       └── KanbanColumn (Closed) [LeadCard x1]
│       └── LeadDetailPage
│           ├── LeadInfo (+ AIScoreBadge)
│           ├── Tabs
│           │   ├── WA Tab → WAConversation
│           │   ├── Notes Tab → Timeline
│           │   ├── Activities Tab → Timeline
│           │   └── AI Recs Tab
│           └── QuickActions
└── Footer
```

### State Management (Pinia)

```javascript
// store.js
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    isAuthenticated: false
  }),
  actions: {
    login(token, user) {
      this.token = token
      this.user = user
      this.isAuthenticated = true
      localStorage.setItem('token', token)
    },
    logout() {
      this.token = null
      this.user = null
      this.isAuthenticated = false
      localStorage.removeItem('token')
    }
  }
})

export const useListingsStore = defineStore('listings', {
  state: () => ({
    listings: [],
    totalPages: 0,
    currentPage: 1
  }),
  actions: {
    async fetchListings(page = 1) {
      const response = await api.listings.getAll({ page, limit: 20 })
      this.listings = response.data
      this.totalPages = response.totalPages
      this.currentPage = page
    }
  }
})

export const useLeadsStore = defineStore('leads', {
  state: () => ({
    leads: [],
    currentLead: null
  }),
  actions: {
    async fetchLeads() {
      const response = await api.leads.getAll()
      this.leads = response.data
    },
    async updateLeadStatus(leadId, newStatus) {
      await api.leads.update(leadId, { status: newStatus })
      // Update local state
      const lead = this.leads.find(l => l.id === leadId)
      if (lead) lead.status = newStatus
    }
  }
})
```

### Routing & Auth Guards

```javascript
// router.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './store'

const routes = [
  // Public routes
  { path: '/', component: HomePage },
  { path: '/search', component: SearchPage },
  { path: '/property/:slug', component: PropertyDetail },
  { path: '/login', component: LoginPage },

  // Agent routes (protected)
  {
    path: '/dashboard',
    component: DashboardPage,
    meta: { requiresAuth: true, role: 'agent' }
  },
  {
    path: '/leads',
    component: LeadsPage,
    meta: { requiresAuth: true, role: 'agent' }
  },
  {
    path: '/leads/:id',
    component: LeadDetailPage,
    meta: { requiresAuth: true, role: 'agent' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.role && authStore.user.role !== to.meta.role) {
    next('/')  // Redirect to home if wrong role
  } else {
    next()
  }
})

export default router
```

---

## BACKEND ARCHITECTURE

### Unified FastAPI Structure

```
backend/
├── main.py                          # App entry, CORS, routers
├── config.py                        # Settings (DB, JWT, secrets)
├── database.py                      # SQLAlchemy setup
├── models.py                        # ORM models
├── auth.py                          # JWT + RBAC middleware
│
├── routers/
│   ├── public.py                    # Public endpoints (no auth)
│   ├── listings.py                  # Listings CRUD (auth required)
│   ├── leads.py                     # Leads CRUD + scoring
│   ├── wa.py                        # WhatsApp messages + webhook
│   ├── content.py                   # Content calendar
│   └── dashboard.py                 # Dashboard stats
│
├── services/
│   ├── ai_scoring.py                # Ollama lead scoring
│   ├── ai_recommendations.py        # Ollama recommendations
│   ├── gowa_client.py               # GOWA API client
│   └── notifications.py             # Web Push
│
├── migrations/                      # Alembic (if needed)
└── tests/
```

### Main App (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import public, listings, leads, wa, content, dashboard
from auth import require_role

app = FastAPI(title="Livininbintaro V2 API", version="2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://livininbintaro.my.id"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes (no auth)
app.include_router(public.router, prefix="/api/public", tags=["public"])

# Protected routes (JWT + RBAC)
app.include_router(
    listings.router,
    prefix="/api/listings",
    tags=["listings"],
    dependencies=[Depends(require_role(["agent", "admin"]))]
)

app.include_router(
    leads.router,
    prefix="/api/leads",
    tags=["leads"],
    dependencies=[Depends(require_role(["agent", "admin"]))]
)

app.include_router(
    wa.router,
    prefix="/api/wa",
    tags=["whatsapp"],
    dependencies=[Depends(require_role(["agent", "admin"]))]
)

app.include_router(
    content.router,
    prefix="/api/content",
    tags=["content"],
    dependencies=[Depends(require_role(["agent", "admin"]))]
)

app.include_router(
    dashboard.router,
    prefix="/api/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(require_role(["agent", "admin"]))]
)

# Webhook (no auth - verified by signature)
app.include_router(wa.webhook_router, prefix="/api/webhook", tags=["webhooks"])
```

### Auth Middleware (auth.py)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"  # From .env
ALGORITHM = "HS256"

security = HTTPBearer()

def create_token(user_id: int, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def require_role(allowed_roles: list):
    def role_checker(payload = Depends(verify_token)):
        if payload.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return payload
    return role_checker
```

---

## PWA ARCHITECTURE

### Service Worker Strategy

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Livininbintaro',
        short_name: 'Livinin',
        description: 'Property marketplace with integrated CRM',
        theme_color: '#1B4332',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: '/icons/icon-192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any maskable'
          },
          {
            src: '/icons/icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        runtimeCaching: [
          {
            // API listings (network-first)
            urlPattern: /^https:\/\/livininbintaro\.my\.id\/api\/listings/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'listings-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24  // 1 day
              }
            }
          },
          {
            // Images (cache-first)
            urlPattern: /^https:\/\/livininbintaro\.my\.id\/images\//,
            handler: 'CacheFirst',
            options: {
              cacheName: 'images-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 7  // 7 days
              }
            }
          },
          {
            // CRM data (network-only, sensitive)
            urlPattern: /^https:\/\/livininbintaro\.my\.id\/api\/(leads|wa|dashboard)/,
            handler: 'NetworkOnly'
          }
        ]
      }
    })
  ]
})
```

### Offline Queue

```javascript
// utils/offline.js
export function useOfflineQueue() {
  const queue = ref([])

  const addToQueue = (action) => {
    const item = { id: Date.now(), action, timestamp: new Date() }
    queue.value.push(item)
    localStorage.setItem('offline-queue', JSON.stringify(queue.value))
  }

  const processQueue = async () => {
    const items = [...queue.value]
    for (const item of items) {
      try {
        await item.action()
        // Remove from queue on success
        queue.value = queue.value.filter(q => q.id !== item.id)
      } catch (error) {
        console.error('Failed to process queue item:', error)
      }
    }
    localStorage.setItem('offline-queue', JSON.stringify(queue.value))
  }

  // Auto-process when back online
  window.addEventListener('online', processQueue)

  return { addToQueue, processQueue, queue }
}
```

---

## DEPLOYMENT ARCHITECTURE

### VPS Structure

```
/opt/livininbintaro-v2/
├── backend/                         # FastAPI app
│   ├── venv/                        # Python virtual env
│   ├── main.py
│   ├── ...
│   └── .env                         # Secrets (DB, JWT)
│
├── frontend/                        # Vue source (dev only)
│   └── dist/                        # Built SPA
│       ├── index.html
│       ├── assets/                  # JS + CSS chunks
│       └── manifest.json
│
└── scripts/
    ├── sync_listings.py
    └── sync_images.py

/var/www/livininbintaro-v2/          # Nginx document root
├── index.html                       # Copied from frontend/dist/
├── assets/
├── manifest.json
└── icons/

/etc/systemd/system/
└── livininbintaro-v2.service        # Backend service

/etc/nginx/conf.d/
└── livininbintaro.conf              # Nginx config
```

### Nginx Configuration

```nginx
server {
    listen 443 ssl;
    http2 on;
    server_name livininbintaro.my.id;

    ssl_certificate /etc/letsencrypt/live/livininbintaro.my.id/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/livininbintaro.my.id/privkey.pem;

    # Frontend SPA
    location / {
        root /var/www/livininbintaro-v2;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Images (cache 7 days)
    location /images/ {
        root /var/www/livininbintaro;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## DATABASE SCHEMA (No Changes)

Reuse existing PostgreSQL 15 schema:
- **public.listings** — Property listings
- **public.users** — User accounts
- **crm.leads** — Lead pipeline
- **crm.notes** — Lead notes
- **crm.activities** — Activity log
- **crm.wa_messages** — WhatsApp conversations
- **crm.content_calendar** — Content schedule

**Zero migration needed.** V2 backend uses same schema as V1.

---

## SECURITY ARCHITECTURE

1. **JWT Authentication** — Token-based, stateless, 7-day expiry
2. **RBAC** — Role-based access control (agent vs admin)
3. **HTTPS Only** — All traffic encrypted, HTTP redirects to HTTPS
4. **CORS Policy** — Whitelist `livininbintaro.my.id` only
5. **Webhook Signature** — Verify GOWA webhook requests
6. **Secrets Management** — `.env` files with 600 permissions
7. **SQL Injection** — SQLAlchemy ORM + parameterized queries
8. **XSS Protection** — Vue escapes output by default

---

**Document Version:** 1.0
**Last Updated:** 2026-03-14
**Next Review:** After Phase 1 implementation
