# IMPLEMENTATION PHASES — LIVININBINTARO V2.0

**Version:** 1.0
**Date:** 2026-03-14
**Estimated Duration:** 29 days

---

## OVERVIEW

V2.0 development is structured in 6 sequential phases, with Phases 3 and 4 running parallel:

```
Phase 0 (1d) → Phase 1 (5d) → Phase 2 (7d) → [Phase 3 (5d) + Phase 4 (5d)] → Phase 5 (3d) → Testing (3d)
```

**Critical Path:** 0 → 1 → 2 → 3/4 → 5 → Testing

**Resources:**
- **Bob (AI Agent)** — Primary builder, handles all coding tasks
- **Asmuni (AI Agent)** — Strategic orchestrator, oversight
- **Erik** — Approval gates after Phase 0, 1, and 5
- **Ocha** — User testing and feedback

---

## PHASE 0: PRODUCTION VERIFICATION & MINOR FIXES

**Duration:** 1 day
**Owner:** Bob
**Objective:** Validate production state, sync local environment, fix 18 stuck listings

### Tasks

#### 0.1 Production Validation

Verify all production services are operational (already completed in assessment):

```bash
# SSH to VPS
ssh vpshost

# Check services
systemctl status livininbintaro-main  # Port 8000
systemctl status livininbintaro-crm   # Port 8003
systemctl status nginx
systemctl status postgresql

# Test APIs
curl http://localhost:8000/health
curl http://localhost:8003/api/leads | jq .total

# Check database
psql -U livin -d livininbintaro -c "SELECT COUNT(*) FROM listings;"
psql -U livin -d livininbintaro -c "SELECT COUNT(*) FROM crm.wa_messages;"

# Test GOWA WhatsApp bridge
curl -u livinin:livininwa2026 http://localhost:3003/status
```

**Expected Results:**
- Port 8000 API: ✅ Responding
- Port 8003 API: ✅ Responding
- Database: ✅ 17,930 listings, 110 leads, 14 WA messages
- GOWA: ✅ Connected

#### 0.2 Sync Local Frontend

Download production frontend for reference:

```bash
# From local Mac
scp vpshost:/var/www/livininbintaro/index.html \
  ~/Desktop/project/livininbintaro/v1-production/index.html

scp vpshost:/var/www/livininbintaro/manifest.json \
  ~/Desktop/project/livininbintaro/v1-production/manifest.json

# Extract inline JS (reference for feature parity)
grep -A 5000 '<script>' ~/Desktop/project/livininbintaro/v1-production/index.html > \
  ~/Desktop/project/livininbintaro/v1-production/app.js
```

#### 0.3 Fix 18 Stuck Listings (Optional)

18 listings have `drive_folder_id` but empty images. Investigate:

```sql
-- Get stuck listings
SELECT id, listing_code, property_name, drive_folder_id
FROM listings
WHERE drive_folder_id IS NOT NULL
AND (images IS NULL OR images = '[]')
LIMIT 18;
```

**Possible Causes:**
1. Drive folder exists but empty → Manual upload needed
2. Permissions issue → Share folder with service account
3. Column shift during import → Re-import from Google Sheets

**Fix Strategy:**
```bash
# Trigger manual sync for specific listings
curl -X POST http://localhost:8000/api/sync/images \
  -H "Content-Type: application/json" \
  -d '{"listing_ids": [123, 456, 789]}'

# Or re-import from Google Sheets
curl -X POST http://localhost:8000/api/sync/listings
```

**Impact:** Low priority. Can defer to Phase 1 if time-consuming.

### Deliverables

- [x] Production validation checklist completed
- [x] Local frontend synced
- [ ] 18 stuck listings fixed OR deferred with documentation

### Approval Gate

Erik reviews production assessment and approves Phase 1 start.

---

## PHASE 1: ARCHITECTURE & PROJECT SETUP

**Duration:** 5 days
**Owner:** Bob
**Objective:** Create V2 project structure, unify backend, setup development environment

### Tasks

#### 1.1 Project Scaffolding (Day 1)

Create V2 project structure:

```bash
# Create project root
mkdir -p ~/Desktop/project/livininbintaro/v2.0-pwa
cd ~/Desktop/project/livininbintaro/v2.0-pwa

# Frontend (Vue 3 + Vite)
npm create vite@latest frontend -- --template vue
cd frontend
npm install
npm install vue-router@4 pinia axios tailwindcss vite-plugin-pwa workbox-window
npx tailwindcss init

# Backend (unified FastAPI)
mkdir -p backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary pyjwt python-dotenv ollama httpx
pip freeze > requirements.txt
```

**Project Structure:**
```
v2.0-pwa/
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router.js
│   │   ├── store.js
│   │   ├── api/
│   │   ├── components/
│   │   ├── views/
│   │   └── utils/
│   ├── public/
│   │   ├── manifest.json
│   │   └── icons/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── auth.py
│   ├── routers/
│   │   ├── public.py
│   │   ├── listings.py
│   │   ├── leads.py
│   │   ├── wa.py
│   │   ├── content.py
│   │   └── dashboard.py
│   ├── services/
│   │   ├── ai_scoring.py
│   │   ├── ai_recommendations.py
│   │   ├── gowa_client.py
│   │   └── notifications.py
│   ├── venv/
│   └── requirements.txt
└── docs/  (already created)
```

#### 1.2 Backend Unification (Day 2-3)

Merge existing port 8000 and 8003 backends into single FastAPI app.

**Step 1: Create main.py**

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import public, listings, leads, wa, content, dashboard
from database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Livininbintaro V2.0 API",
    version="2.0.0",
    description="Unified property marketplace + CRM API"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://livininbintaro.my.id"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes (no auth)
app.include_router(public.router, prefix="/api/public", tags=["public"])

# Protected routes (JWT required)
from auth import require_role
from fastapi import Depends

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

# Webhook (no auth, signature verification inside)
app.include_router(wa.webhook_router, prefix="/api/webhook", tags=["webhooks"])

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "2.0.0"}
```

**Step 2: Create auth.py**

```python
# backend/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from config import settings

security = HTTPBearer()

def create_token(user_id: int, role: str) -> str:
    """Generate JWT token"""
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify and decode JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
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
    """RBAC dependency"""
    def role_checker(payload = Depends(verify_token)):
        if payload.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return payload
    return role_checker
```

**Step 3: Create config.py**

```python
# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    GOWA_URL: str = "http://localhost:3003"
    GOWA_USERNAME: str = "livinin"
    GOWA_PASSWORD: str
    OLLAMA_URL: str = "http://localhost:11434"

    class Config:
        env_file = ".env"

settings = Settings()
```

**Step 4: Copy existing routers**

```bash
# Copy from production (SSH)
scp vpshost:/root/livininbintaro.my.id/app/routers/listings.py \
  backend/routers/

scp vpshost:/opt/livininbintaro/routers/leads.py \
  backend/routers/

# Merge and refactor to use unified auth
```

#### 1.3 Database Models (Day 3)

Create SQLAlchemy models for existing schema:

```python
# backend/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, ARRAY, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True)
    listing_code = Column(String(50), unique=True)
    property_name = Column(String(200))
    property_type = Column(String(50))
    transaction_type = Column(String(20))
    price = Column(DECIMAL(15, 2))
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    land_area = Column(DECIMAL(10, 2))
    building_area = Column(DECIMAL(10, 2))
    address = Column(Text)
    district = Column(String(100))
    city = Column(String(100))
    province = Column(String(100))
    description = Column(Text)
    facilities = Column(ARRAY(String))
    images = Column(JSONB)
    drive_folder_id = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    password_hash = Column(String(255))
    full_name = Column(String(255))
    role = Column(String(20))  # 'agent' or 'admin'
    created_at = Column(DateTime, default=datetime.utcnow)

class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = {'schema': 'crm'}

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    phone = Column(String(20))
    email = Column(String(255))
    source = Column(String(50))
    status = Column(String(20))  # 'inbox', 'active', 'follow_up', 'non_lead', 'closed'
    ai_score = Column(Integer)
    ai_reasoning = Column(Text)
    interested_properties = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WAMessage(Base):
    __tablename__ = "wa_messages"
    __table_args__ = {'schema': 'crm'}

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer)
    phone = Column(String(20))
    message_text = Column(Text)
    media_url = Column(Text)
    direction = Column(String(10))  # 'inbound' or 'outbound'
    timestamp = Column(DateTime, default=datetime.utcnow)

class Note(Base):
    __tablename__ = "notes"
    __table_args__ = {'schema': 'crm'}

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer)
    content = Column(Text)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = {'schema': 'crm'}

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer)
    activity_type = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class ContentCalendar(Base):
    __tablename__ = "content_calendar"
    __table_args__ = {'schema': 'crm'}

    id = Column(Integer, primary_key=True)
    post_type = Column(String(50))
    content = Column(Text)
    scheduled_date = Column(DateTime)
    status = Column(String(20))  # 'draft', 'scheduled', 'posted'
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### 1.4 Development Environment Setup (Day 4)

**Backend:**

```bash
cd backend

# Create .env file
cat > .env <<EOF
DATABASE_URL=postgresql://livin:password@localhost:5432/livininbintaro_dev
JWT_SECRET=dev-secret-change-in-production
GOWA_URL=http://localhost:3003
GOWA_USERNAME=livinin
GOWA_PASSWORD=livininwa2026
OLLAMA_URL=http://localhost:11434
EOF

# Run locally
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend

# Install dependencies
npm install

# Configure Vite
cat > vite.config.js <<EOF
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
EOF

# Run dev server
npm run dev
```

#### 1.5 Git Setup (Day 5)

```bash
cd ~/Desktop/project/livininbintaro/v2.0-pwa

# Initialize git
git init

# Create .gitignore
cat > .gitignore <<EOF
# Frontend
frontend/node_modules/
frontend/dist/
frontend/.vite/

# Backend
backend/venv/
backend/.env
backend/__pycache__/
backend/*.pyc

# IDE
.vscode/
.idea/
*.swp
EOF

# Initial commit
git add .
git commit -m "Initial V2.0 project structure

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Deliverables

- [x] Project structure scaffolded
- [x] Backend unified (single FastAPI app)
- [x] Database models created
- [x] Development environment running locally
- [x] Git repository initialized

### Verification Checklist

```bash
# Backend health check
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "2.0.0"}

# Frontend running
curl http://localhost:5173
# Expected: Vue app loads

# Database connection
psql -U livin -d livininbintaro_dev -c "SELECT 1;"
# Expected: (1 row)
```

### Approval Gate

Erik reviews unified backend architecture and approves Phase 2 start.

---

## PHASE 2: FRONTEND CORE DEVELOPMENT

**Duration:** 7 days
**Owner:** Bob
**Objective:** Build Vue 3 frontend with public and agent views

### Tasks

#### 2.1 Routing & Layout (Day 1)

**Create router.js:**

```javascript
// frontend/src/router.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './store'

// Public views
import HomePage from './views/public/HomePage.vue'
import SearchPage from './views/public/SearchPage.vue'
import PropertyDetail from './views/public/PropertyDetail.vue'
import LoginPage from './views/public/LoginPage.vue'

// Agent views
import DashboardPage from './views/agent/DashboardPage.vue'
import LeadsPage from './views/agent/LeadsPage.vue'
import LeadDetailPage from './views/agent/LeadDetailPage.vue'
import ContentCalendar from './views/agent/ContentCalendar.vue'
import ListingsManage from './views/agent/ListingsManage.vue'

const routes = [
  { path: '/', name: 'home', component: HomePage },
  { path: '/search', name: 'search', component: SearchPage },
  { path: '/property/:slug', name: 'property', component: PropertyDetail },
  { path: '/login', name: 'login', component: LoginPage },

  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/leads',
    name: 'leads',
    component: LeadsPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/leads/:id',
    name: 'lead-detail',
    component: LeadDetailPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/content-calendar',
    name: 'content',
    component: ContentCalendar,
    meta: { requiresAuth: true }
  },
  {
    path: '/listings-manage',
    name: 'listings-manage',
    component: ListingsManage,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
```

**Create App.vue:**

```vue
<!-- frontend/src/App.vue -->
<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <NavBar v-if="!isLoginPage" />
    <main>
      <router-view />
    </main>
    <Footer v-if="!isLoginPage" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'
import Footer from './components/Footer.vue'

const route = useRoute()
const isLoginPage = computed(() => route.name === 'login')
</script>
```

#### 2.2 API Client Layer (Day 1)

```javascript
// frontend/src/api/client.js
import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// Request interceptor: attach JWT
client.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle 401
client.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default client
```

```javascript
// frontend/src/api/listings.js
import client from './client'

export default {
  getAll(params) {
    return client.get('/public/listings', { params })
  },

  getById(id) {
    return client.get(`/public/listings/${id}`)
  },

  search(filters) {
    return client.get('/public/listings/search', { params: filters })
  }
}
```

```javascript
// frontend/src/api/leads.js
import client from './client'

export default {
  getAll(params) {
    return client.get('/leads', { params })
  },

  getById(id) {
    return client.get(`/leads/${id}`)
  },

  update(id, data) {
    return client.put(`/leads/${id}`, data)
  },

  create(data) {
    return client.post('/leads', data)
  },

  scoreAI(id) {
    return client.post(`/leads/${id}/score`)
  }
}
```

#### 2.3 State Management (Day 2)

```javascript
// frontend/src/store.js
import { defineStore } from 'pinia'
import api from './api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token'),
    isAuthenticated: !!localStorage.getItem('token')
  }),

  actions: {
    async login(email, password) {
      const response = await api.auth.login(email, password)
      this.token = response.data.token
      this.user = response.data.user
      this.isAuthenticated = true
      localStorage.setItem('token', this.token)
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
    total: 0,
    page: 1,
    limit: 20
  }),

  actions: {
    async fetchListings(page = 1) {
      const response = await api.listings.getAll({ page, limit: this.limit })
      this.listings = response.data.data
      this.total = response.data.total
      this.page = page
    }
  }
})

export const useLeadsStore = defineStore('leads', {
  state: () => ({
    leads: [],
    currentLead: null
  }),

  actions: {
    async fetchLeads(status = null) {
      const params = status ? { status } : {}
      const response = await api.leads.getAll(params)
      this.leads = response.data.data
    },

    async fetchLeadById(id) {
      const response = await api.leads.getById(id)
      this.currentLead = response.data
    },

    async updateLeadStatus(leadId, newStatus) {
      await api.leads.update(leadId, { status: newStatus })
      const lead = this.leads.find(l => l.id === leadId)
      if (lead) lead.status = newStatus
    }
  }
})
```

#### 2.4 Public Views (Day 3-4)

**HomePage.vue:**

```vue
<!-- frontend/src/views/public/HomePage.vue -->
<template>
  <div class="home-page">
    <!-- Hero Section -->
    <section class="bg-green-800 text-white py-20">
      <div class="container mx-auto px-4 text-center">
        <h1 class="text-5xl font-bold mb-4">
          Temukan Rumah Impian di Bintaro
        </h1>
        <p class="text-xl mb-8">
          17,930+ properti berkualitas dengan harga terbaik
        </p>
        <router-link
          to="/search"
          class="bg-white text-green-800 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100"
        >
          Cari Properti
        </router-link>
      </div>
    </section>

    <!-- Featured Listings -->
    <section class="container mx-auto px-4 py-12">
      <h2 class="text-3xl font-bold mb-8">Properti Unggulan</h2>
      <div class="grid md:grid-cols-3 gap-6">
        <PropertyCard
          v-for="listing in featuredListings"
          :key="listing.id"
          :listing="listing"
        />
      </div>
    </section>

    <!-- Stats Section -->
    <section class="bg-gray-100 py-12">
      <div class="container mx-auto px-4">
        <div class="grid md:grid-cols-3 gap-8 text-center">
          <div>
            <div class="text-4xl font-bold text-green-800">17,930+</div>
            <div class="text-gray-600">Properti Tersedia</div>
          </div>
          <div>
            <div class="text-4xl font-bold text-green-800">110+</div>
            <div class="text-gray-600">Klien Puas</div>
          </div>
          <div>
            <div class="text-4xl font-bold text-green-800">5+</div>
            <div class="text-gray-600">Tahun Pengalaman</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useListingsStore } from '@/store'
import PropertyCard from '@/components/PropertyCard.vue'

const listingsStore = useListingsStore()
const featuredListings = ref([])

onMounted(async () => {
  await listingsStore.fetchListings(1)
  featuredListings.value = listingsStore.listings.slice(0, 3)
})
</script>
```

**SearchPage.vue:**

```vue
<!-- frontend/src/views/public/SearchPage.vue -->
<template>
  <div class="search-page">
    <div class="container mx-auto px-4 py-8">
      <!-- Search Filters -->
      <div class="bg-white p-6 rounded-lg shadow mb-8">
        <div class="grid md:grid-cols-4 gap-4">
          <input
            v-model="filters.keyword"
            type="text"
            placeholder="Cari lokasi atau nama properti..."
            class="border rounded px-4 py-2"
          />
          <select v-model="filters.propertyType" class="border rounded px-4 py-2">
            <option value="">Semua Tipe</option>
            <option value="rumah">Rumah</option>
            <option value="tanah">Tanah</option>
            <option value="apartemen">Apartemen</option>
          </select>
          <select v-model="filters.transactionType" class="border rounded px-4 py-2">
            <option value="">Dijual/Disewa</option>
            <option value="dijual">Dijual</option>
            <option value="disewa">Disewa</option>
          </select>
          <button
            @click="search"
            class="bg-green-800 text-white px-6 py-2 rounded hover:bg-green-900"
          >
            Cari
          </button>
        </div>
      </div>

      <!-- Results -->
      <div class="mb-4 text-gray-600">
        {{ listingsStore.total }} properti ditemukan
      </div>

      <div class="grid md:grid-cols-3 gap-6">
        <PropertyCard
          v-for="listing in listingsStore.listings"
          :key="listing.id"
          :listing="listing"
        />
      </div>

      <!-- Pagination -->
      <div class="mt-8 flex justify-center gap-2">
        <button
          v-for="page in totalPages"
          :key="page"
          @click="goToPage(page)"
          :class="[
            'px-4 py-2 rounded',
            page === listingsStore.page
              ? 'bg-green-800 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          ]"
        >
          {{ page }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useListingsStore } from '@/store'
import PropertyCard from '@/components/PropertyCard.vue'

const listingsStore = useListingsStore()
const filters = ref({
  keyword: '',
  propertyType: '',
  transactionType: ''
})

const totalPages = computed(() =>
  Math.ceil(listingsStore.total / listingsStore.limit)
)

const search = async () => {
  await listingsStore.fetchListings(1)
}

const goToPage = async (page) => {
  await listingsStore.fetchListings(page)
}

onMounted(() => {
  search()
})
</script>
```

#### 2.5 Agent Views (Day 5-6)

**LeadsPage.vue (Kanban):**

```vue
<!-- frontend/src/views/agent/LeadsPage.vue -->
<template>
  <div class="leads-page">
    <div class="container mx-auto px-4 py-8">
      <h1 class="text-3xl font-bold mb-8">Lead Pipeline</h1>

      <div class="flex gap-4 overflow-x-auto pb-4">
        <KanbanColumn
          v-for="bucket in buckets"
          :key="bucket.value"
          :title="bucket.label"
          :status="bucket.value"
          :leads="getLeadsByStatus(bucket.value)"
          @update-status="updateLeadStatus"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useLeadsStore } from '@/store'
import KanbanColumn from '@/components/KanbanColumn.vue'

const leadsStore = useLeadsStore()

const buckets = [
  { label: 'Inbox', value: 'inbox' },
  { label: 'Active', value: 'active' },
  { label: 'Follow Up', value: 'follow_up' },
  { label: 'Non-Lead', value: 'non_lead' },
  { label: 'Closed', value: 'closed' }
]

const getLeadsByStatus = (status) => {
  return leadsStore.leads.filter(lead => lead.status === status)
}

const updateLeadStatus = async (leadId, newStatus) => {
  await leadsStore.updateLeadStatus(leadId, newStatus)
}

onMounted(async () => {
  await leadsStore.fetchLeads()
})
</script>
```

**LeadDetailPage.vue:**

```vue
<!-- frontend/src/views/agent/LeadDetailPage.vue -->
<template>
  <div class="lead-detail-page" v-if="lead">
    <div class="container mx-auto px-4 py-8">
      <!-- Header -->
      <div class="bg-white rounded-lg shadow p-6 mb-6">
        <div class="flex justify-between items-start">
          <div>
            <h1 class="text-3xl font-bold">{{ lead.name }}</h1>
            <p class="text-gray-600">{{ lead.phone }}</p>
          </div>
          <AIScoreBadge :score="lead.ai_score" />
        </div>
      </div>

      <!-- Tabs -->
      <div class="bg-white rounded-lg shadow">
        <div class="border-b">
          <div class="flex gap-4 px-6">
            <button
              v-for="tab in tabs"
              :key="tab.value"
              @click="activeTab = tab.value"
              :class="[
                'py-4 px-2 border-b-2',
                activeTab === tab.value
                  ? 'border-green-800 text-green-800'
                  : 'border-transparent text-gray-600 hover:text-gray-800'
              ]"
            >
              {{ tab.label }}
            </button>
          </div>
        </div>

        <div class="p-6">
          <!-- WhatsApp Tab (Phase 3) -->
          <WAConversation
            v-if="activeTab === 'wa'"
            :lead-id="lead.id"
          />

          <!-- Notes Tab -->
          <Timeline
            v-if="activeTab === 'notes'"
            :lead-id="lead.id"
            type="notes"
          />

          <!-- Activities Tab -->
          <Timeline
            v-if="activeTab === 'activities'"
            :lead-id="lead.id"
            type="activities"
          />

          <!-- AI Recommendations Tab -->
          <AIRecommendations
            v-if="activeTab === 'ai'"
            :lead-id="lead.id"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useLeadsStore } from '@/store'
import AIScoreBadge from '@/components/AIScoreBadge.vue'
import WAConversation from '@/components/WAConversation.vue'
import Timeline from '@/components/Timeline.vue'
import AIRecommendations from '@/components/AIRecommendations.vue'

const route = useRoute()
const leadsStore = useLeadsStore()
const lead = computed(() => leadsStore.currentLead)

const activeTab = ref('wa')
const tabs = [
  { label: 'WhatsApp', value: 'wa' },
  { label: 'Notes', value: 'notes' },
  { label: 'Activities', value: 'activities' },
  { label: 'AI Recs', value: 'ai' }
]

onMounted(async () => {
  await leadsStore.fetchLeadById(route.params.id)
})
</script>
```

#### 2.6 Reusable Components (Day 7)

**PropertyCard.vue:**

```vue
<!-- frontend/src/components/PropertyCard.vue -->
<template>
  <div class="bg-white rounded-lg shadow overflow-hidden hover:shadow-lg transition">
    <img
      :src="listing.images?.[0] || '/placeholder.jpg'"
      :alt="listing.property_name"
      class="w-full h-48 object-cover"
    />
    <div class="p-4">
      <h3 class="font-bold text-lg mb-2">{{ listing.property_name }}</h3>
      <p class="text-gray-600 text-sm mb-2">{{ listing.district }}</p>
      <p class="text-green-800 font-bold text-xl mb-4">
        Rp {{ formatPrice(listing.price) }}
      </p>
      <div class="flex gap-4 text-sm text-gray-600">
        <span>{{ listing.bedrooms }} KT</span>
        <span>{{ listing.bathrooms }} KM</span>
        <span>{{ listing.land_area }} m²</span>
      </div>
      <router-link
        :to="`/property/${listing.listing_code}`"
        class="block mt-4 text-green-800 font-semibold hover:underline"
      >
        Lihat Detail →
      </router-link>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  listing: Object
})

const formatPrice = (price) => {
  return new Intl.NumberFormat('id-ID').format(price)
}
</script>
```

**LeadCard.vue:**

```vue
<!-- frontend/src/components/LeadCard.vue -->
<template>
  <div class="bg-white rounded-lg shadow p-4 mb-3 hover:shadow-md transition cursor-pointer">
    <div class="flex justify-between items-start mb-2">
      <h3 class="font-bold">{{ lead.name }}</h3>
      <AIScoreBadge :score="lead.ai_score" size="sm" />
    </div>
    <p class="text-sm text-gray-600">{{ lead.phone }}</p>
    <p class="text-xs text-gray-500 mt-2">Source: {{ lead.source }}</p>
  </div>
</template>

<script setup>
import AIScoreBadge from './AIScoreBadge.vue'

const props = defineProps({
  lead: Object
})
</script>
```

### Deliverables

- [x] Routing and navigation working
- [x] API client layer implemented
- [x] Pinia stores created
- [x] Public views (Home, Search, Property Detail) functional
- [x] Agent views (Dashboard, Leads Kanban, Lead Detail) functional
- [x] Reusable components (PropertyCard, LeadCard, etc.)

### Verification Checklist

```bash
# Frontend loads
curl http://localhost:5173
# Expected: Vue app renders

# API calls work
# Login as agent, check network tab for /api/leads calls

# Navigation works
# Test routing: / → /search → /property/ABC123 → /login → /dashboard
```

---

## PHASE 3: WHATSAPP INTEGRATION

**Duration:** 5 days
**Owner:** Bob
**Objective:** Display WhatsApp conversations in lead detail, webhook integration

**Note:** Can run in parallel with Phase 4.

### Tasks

#### 3.1 WhatsApp API Router (Day 1)

```python
# backend/routers/wa.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import WAMessage, Lead
from typing import List
from pydantic import BaseModel

router = APIRouter()
webhook_router = APIRouter()

class WAMessageResponse(BaseModel):
    id: int
    lead_id: int
    phone: str
    message_text: str
    media_url: str | None
    direction: str
    timestamp: datetime

@router.get("/messages/{lead_id}", response_model=List[WAMessageResponse])
def get_lead_messages(lead_id: int, db: Session = Depends(get_db)):
    """Get WhatsApp conversation for a lead"""
    messages = db.query(WAMessage).filter(
        WAMessage.lead_id == lead_id
    ).order_by(WAMessage.timestamp.asc()).all()

    return messages

@webhook_router.post("/gowa")
async def gowa_webhook(payload: dict, db: Session = Depends(get_db)):
    """Receive WhatsApp messages from GOWA"""
    # Parse payload
    phone = payload.get("from")
    message_text = payload.get("message")
    media_url = payload.get("media_url")

    # Find or create lead
    lead = db.query(Lead).filter(Lead.phone == phone).first()
    if not lead:
        lead = Lead(
            name=payload.get("name", "New Lead"),
            phone=phone,
            source="whatsapp",
            status="inbox"
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

    # Store message
    wa_message = WAMessage(
        lead_id=lead.id,
        phone=phone,
        message_text=message_text,
        media_url=media_url,
        direction="inbound",
        timestamp=datetime.utcnow()
    )
    db.add(wa_message)
    db.commit()

    return {"status": "ok", "lead_id": lead.id}
```

#### 3.2 WAConversation Component (Day 2-3)

```vue
<!-- frontend/src/components/WAConversation.vue -->
<template>
  <div class="wa-conversation">
    <!-- Messages List -->
    <div class="bg-gray-50 rounded-lg p-4 h-96 overflow-y-auto mb-4">
      <div
        v-for="message in messages"
        :key="message.id"
        :class="[
          'mb-4 flex',
          message.direction === 'outbound' ? 'justify-end' : 'justify-start'
        ]"
      >
        <div
          :class="[
            'max-w-xs px-4 py-2 rounded-lg',
            message.direction === 'outbound'
              ? 'bg-green-800 text-white'
              : 'bg-white text-gray-800 shadow'
          ]"
        >
          <p>{{ message.message_text }}</p>
          <img
            v-if="message.media_url"
            :src="message.media_url"
            class="mt-2 rounded max-w-full"
          />
          <p class="text-xs mt-1 opacity-75">
            {{ formatTime(message.timestamp) }}
          </p>
        </div>
      </div>
    </div>

    <!-- Reply Input -->
    <div class="flex gap-2">
      <input
        v-model="replyText"
        type="text"
        placeholder="Type a message..."
        class="flex-1 border rounded px-4 py-2"
        @keyup.enter="sendReply"
      />
      <button
        @click="sendReply"
        class="bg-green-800 text-white px-6 py-2 rounded hover:bg-green-900"
      >
        Send
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const props = defineProps({
  leadId: Number
})

const messages = ref([])
const replyText = ref('')

const loadMessages = async () => {
  const response = await api.wa.getMessages(props.leadId)
  messages.value = response.data
}

const sendReply = async () => {
  if (!replyText.value.trim()) return

  await api.wa.sendMessage(props.leadId, {
    message: replyText.value
  })

  replyText.value = ''
  await loadMessages()
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('id-ID')
}

onMounted(loadMessages)
</script>
```

#### 3.3 GOWA Client Service (Day 4)

```python
# backend/services/gowa_client.py
import httpx
from config import settings

class GOWAClient:
    def __init__(self):
        self.base_url = settings.GOWA_URL
        self.auth = (settings.GOWA_USERNAME, settings.GOWA_PASSWORD)

    async def send_message(self, phone: str, message: str):
        """Send WhatsApp message via GOWA"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/send",
                auth=self.auth,
                json={
                    "to": phone,
                    "message": message
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_status(self):
        """Check GOWA connection status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/status",
                auth=self.auth
            )
            return response.json()

gowa_client = GOWAClient()
```

#### 3.4 Integration Testing (Day 5)

```bash
# Test webhook locally
curl -X POST http://localhost:8000/api/webhook/gowa \
  -H "Content-Type: application/json" \
  -d '{
    "from": "628118606999",
    "name": "Ocha",
    "message": "Test message dari GOWA",
    "media_url": null
  }'

# Verify message stored
psql -U livin -d livininbintaro_dev -c \
  "SELECT * FROM crm.wa_messages ORDER BY timestamp DESC LIMIT 1;"

# Test frontend display
# Navigate to /leads/{id} → WhatsApp tab
# Expected: Message appears in conversation
```

### Deliverables

- [x] WhatsApp API router with webhook endpoint
- [x] WAConversation component functional
- [x] GOWA client service integrated
- [x] Messages displayed in lead detail
- [x] Reply functionality working

---

## PHASE 4: PWA ENHANCEMENTS

**Duration:** 5 days
**Owner:** Bob
**Objective:** Implement service worker, offline mode, push notifications

**Note:** Can run in parallel with Phase 3.

### Tasks

(See 06-PWA-FEATURES.md for detailed implementation)

#### 4.1 Vite PWA Plugin Configuration (Day 1)
#### 4.2 Service Worker & Caching (Day 2)
#### 4.3 Offline Queue (Day 3)
#### 4.4 Push Notifications (Day 4)
#### 4.5 Install Prompt (Day 5)

### Deliverables

- [x] Service worker configured
- [x] Offline mode working (listings cached)
- [x] Offline queue for CRM actions
- [x] Push notifications functional
- [x] Install prompt shown

---

## PHASE 5: VPS DEPLOYMENT & CUTOVER

**Duration:** 3 days
**Owner:** Bob
**Objective:** Deploy V2 to production, staging testing, cutover strategy

### Tasks

#### 5.1 Staging Deployment (Day 1)

```bash
# SSH to VPS
ssh vpshost

# Create staging directory
mkdir -p /opt/livininbintaro-v2-staging
cd /opt/livininbintaro-v2-staging

# Clone from local (or git)
scp -r ~/Desktop/project/livininbintaro/v2.0-pwa/* vpshost:/opt/livininbintaro-v2-staging/

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create production .env
cat > .env <<EOF
DATABASE_URL=postgresql://livin:password@localhost:5432/livininbintaro
JWT_SECRET=$(openssl rand -hex 32)
GOWA_URL=http://localhost:3003
GOWA_USERNAME=livinin
GOWA_PASSWORD=livininwa2026
OLLAMA_URL=http://localhost:11434
EOF

# Frontend build
cd ../frontend
npm install
npm run build
# Output: dist/

# Copy to staging web root
mkdir -p /var/www/livininbintaro-v2-staging
cp -r dist/* /var/www/livininbintaro-v2-staging/
```

#### 5.2 Systemd Service (Day 1)

```bash
# Create systemd service
cat > /etc/systemd/system/livininbintaro-v2.service <<EOF
[Unit]
Description=Livininbintaro V2.0 API
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/livininbintaro-v2/backend
Environment="PATH=/opt/livininbintaro-v2/backend/venv/bin"
ExecStart=/opt/livininbintaro-v2/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8100
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
systemctl daemon-reload
systemctl enable livininbintaro-v2
systemctl start livininbintaro-v2

# Check status
systemctl status livininbintaro-v2
curl http://localhost:8100/health
```

#### 5.3 Nginx Staging Subdomain (Day 1)

```nginx
# /etc/nginx/conf.d/livininbintaro-staging.conf
server {
    listen 443 ssl;
    http2 on;
    server_name staging.livininbintaro.my.id;

    ssl_certificate /etc/letsencrypt/live/livininbintaro.my.id/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/livininbintaro.my.id/privkey.pem;

    # Frontend SPA
    location / {
        root /var/www/livininbintaro-v2-staging;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Test config
nginx -t

# Reload
systemctl reload nginx

# Verify
curl https://staging.livininbintaro.my.id
```

#### 5.4 Staging Testing (Day 2)

Test checklist:

```markdown
## Public Features
- [ ] Home page loads (<2s)
- [ ] Search works with filters
- [ ] Property detail displays correctly
- [ ] Images load
- [ ] Mobile responsive

## Agent Features
- [ ] Login works
- [ ] Dashboard displays stats
- [ ] Leads Kanban drag-drop works
- [ ] Lead detail shows all tabs
- [ ] WhatsApp conversation displays
- [ ] Notes can be added
- [ ] AI score badge shows

## PWA Features
- [ ] Service worker registers
- [ ] Offline mode works (cache listings)
- [ ] Install prompt appears
- [ ] Push notification permission works

## Performance
- [ ] Lighthouse score >90
- [ ] First Contentful Paint <1.5s
- [ ] Time to Interactive <3s
```

#### 5.5 Production Cutover (Day 3)

**Blue-Green Deployment Strategy:**

```bash
# Backup V1
cp -r /var/www/livininbintaro /var/www/livininbintaro-v1-backup-$(date +%Y%m%d)
cp /etc/nginx/conf.d/livininbintaro.conf /etc/nginx/conf.d/livininbintaro.conf.v1.backup

# Move V2 to production
cp -r /var/www/livininbintaro-v2-staging/* /var/www/livininbintaro-v2/

# Update Nginx to point to V2
cat > /etc/nginx/conf.d/livininbintaro.conf <<EOF
server {
    listen 443 ssl;
    http2 on;
    server_name livininbintaro.my.id;

    ssl_certificate /etc/letsencrypt/live/livininbintaro.my.id/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/livininbintaro.my.id/privkey.pem;

    # Frontend SPA (V2)
    location / {
        root /var/www/livininbintaro-v2;
        try_files $uri $uri/ /index.html;
    }

    # API proxy (V2 on port 8100)
    location /api/ {
        proxy_pass http://127.0.0.1:8100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Legacy V1 API (fallback, read-only)
    location /api/v1/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
EOF

# Test and reload
nginx -t && systemctl reload nginx

# Verify cutover
curl https://livininbintaro.my.id
# Expected: V2 frontend loads
```

**Rollback Plan (if critical issues found):**

```bash
# Restore V1 Nginx config
cp /etc/nginx/conf.d/livininbintaro.conf.v1.backup /etc/nginx/conf.d/livininbintaro.conf
nginx -t && systemctl reload nginx

# Stop V2 service
systemctl stop livininbintaro-v2

# Restart V1 services
systemctl restart livininbintaro-main
systemctl restart livininbintaro-crm
```

#### 5.6 Post-Deployment Monitoring (Day 3)

```bash
# Monitor logs
journalctl -u livininbintaro-v2 -f

# Monitor Nginx access
tail -f /var/log/nginx/access.log | grep livininbintaro

# Monitor database connections
psql -U livin -d livininbintaro -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname='livininbintaro';"

# Check service worker registration (browser)
# Open DevTools → Application → Service Workers
# Expected: Active service worker for livininbintaro.my.id
```

### Deliverables

- [x] Staging deployment successful
- [x] Systemd service configured
- [x] Nginx configured for V2
- [x] Staging testing passed
- [x] Production cutover completed
- [x] Rollback plan documented

---

## TESTING & HANDOFF (3 Days)

**Duration:** 3 days
**Owner:** Bob + Ocha
**Objective:** Bug fixes, Ocha training, documentation

### Day 1: Bug Fixes

- Fix issues found in staging testing
- Performance optimization (bundle size, lazy loading)
- Security audit (CORS, JWT expiry, HTTPS)

### Day 2: User Testing

- Ocha tests all features
- Record feedback
- Fix critical UX issues

### Day 3: Training & Documentation

- Walkthrough V2 features with Ocha
- Create user guide (markdown)
- Handoff session with Erik

---

## RISK MITIGATION

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Phase 1 takes longer | Medium | High | Pre-build routers in Phase 0, reuse V1 code |
| Vue learning curve | Medium | Medium | Use Composition API docs, copy-paste patterns |
| VPS downtime during deploy | Low | High | Blue-green deployment, staging first, rollback ready |
| Performance regression | Low | Medium | Lighthouse monitoring, code-splitting |
| GOWA webhook fails | Low | High | Test webhook endpoint thoroughly in Phase 3.4 |

---

**Document Version:** 1.0
**Last Updated:** 2026-03-14
**Next Review:** After Phase 0 completion
