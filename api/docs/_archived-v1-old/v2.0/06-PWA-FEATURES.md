# PWA FEATURES — LIVININBINTARO V2.0

**Version:** 1.0
**Date:** 2026-03-14
**Objective:** Production-grade Progressive Web App with offline mode, push notifications, and install prompt

---

## OVERVIEW

V2.0 implements full PWA capabilities to enable mobile-first experience for Ocha's field work:

**Core Features:**
1. **Service Worker** - Cache app shell and listings for offline access
2. **Offline Mode** - View cached properties without network
3. **Offline Queue** - Queue CRM actions when offline, sync when online
4. **Push Notifications** - New leads, follow-up reminders
5. **Install Prompt** - Add to home screen for app-like experience

**Use Cases:**
- Ocha visits property site without network → cached listing data accessible
- Ocha adds note to lead while offline → syncs automatically when online
- New lead from WhatsApp → push notification alerts Ocha immediately
- Ocha installs PWA on phone → one-tap access like native app

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────┐
│          BROWSER (Chrome, Safari)               │
├─────────────────────────────────────────────────┤
│  ┌──────────────┐          ┌─────────────────┐ │
│  │  Vue App     │          │ Service Worker  │ │
│  │              │◄─────────┤ (sw.js)         │ │
│  │ • UI         │  Cache   │                 │ │
│  │ • Router     │  Request │ • Cache Mgmt    │ │
│  │ • Pinia      │          │ • Offline Queue │ │
│  └──────┬───────┘          │ • Push Handler  │ │
│         │                  └────────┬────────┘ │
│         │ API Call                  │          │
│         ▼                           ▼          │
│  ┌──────────────────────────────────────────┐  │
│  │        Network Layer                     │  │
│  │  Online: Fetch from API                  │  │
│  │  Offline: Return from Cache              │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
         │                           ▲
         │ HTTPS                     │ Push
         ▼                           │
┌─────────────────┐         ┌────────────────┐
│  Backend API    │         │ Push Service   │
│  (FastAPI)      │         │ (FCM/VAPID)    │
└─────────────────┘         └────────────────┘
```

---

## IMPLEMENTATION

### Step 1: Vite PWA Plugin Configuration

**Install Dependencies:**

```bash
cd frontend
npm install -D vite-plugin-pwa workbox-window
```

**Configure vite.config.js:**

```javascript
// frontend/vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'robots.txt', 'icons/*.png'],

      manifest: {
        name: 'Livininbintaro Property Marketplace',
        short_name: 'Livinin',
        description: 'Property marketplace with integrated CRM for agents',
        theme_color: '#1B4332',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: '/icons/icon-72.png',
            sizes: '72x72',
            type: 'image/png'
          },
          {
            src: '/icons/icon-96.png',
            sizes: '96x96',
            type: 'image/png'
          },
          {
            src: '/icons/icon-128.png',
            sizes: '128x128',
            type: 'image/png'
          },
          {
            src: '/icons/icon-144.png',
            sizes: '144x144',
            type: 'image/png'
          },
          {
            src: '/icons/icon-152.png',
            sizes: '152x152',
            type: 'image/png'
          },
          {
            src: '/icons/icon-192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any maskable'
          },
          {
            src: '/icons/icon-384.png',
            sizes: '384x384',
            type: 'image/png'
          },
          {
            src: '/icons/icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ],
        categories: ['business', 'productivity'],
        shortcuts: [
          {
            name: 'Dashboard',
            short_name: 'Dashboard',
            description: 'Open agent dashboard',
            url: '/dashboard',
            icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }]
          },
          {
            name: 'Leads',
            short_name: 'Leads',
            description: 'View leads pipeline',
            url: '/leads',
            icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }]
          }
        ]
      },

      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],

        runtimeCaching: [
          {
            // API: Public listings (network-first with cache fallback)
            urlPattern: /^https:\/\/livininbintaro\.my\.id\/api\/public\/listings/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-listings-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24  // 1 day
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },

          {
            // API: Listings detail (cache-first for performance)
            urlPattern: /^https:\/\/livininbintaro\.my\.id\/api\/public\/listings\/\d+/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'api-listing-detail-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24 * 7  // 7 days
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },

          {
            // Images: Property photos (cache-first, long expiry)
            urlPattern: /^https:\/\/livininbintaro\.my\.id\/images\//,
            handler: 'CacheFirst',
            options: {
              cacheName: 'images-cache',
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 60 * 60 * 24 * 30  // 30 days
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },

          {
            // API: CRM data (network-only, sensitive data)
            urlPattern: /^https:\/\/livininbintaro\.my\.id\/api\/(leads|wa|dashboard|content)/,
            handler: 'NetworkOnly'
          },

          {
            // Google Fonts
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365  // 1 year
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          }
        ],

        // Clean old caches on activation
        cleanupOutdatedCaches: true,

        // Skip waiting and claim clients immediately
        skipWaiting: true,
        clientsClaim: true
      },

      devOptions: {
        enabled: true,  // Enable in dev mode for testing
        type: 'module'
      }
    })
  ]
})
```

---

### Step 2: Service Worker Registration

**Update main.js:**

```javascript
// frontend/src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'

// PWA Service Worker Registration
import { registerSW } from 'virtual:pwa-register'

const updateSW = registerSW({
  onNeedRefresh() {
    // Show update notification
    if (confirm('New version available! Reload to update?')) {
      updateSW(true)
    }
  },
  onOfflineReady() {
    console.log('App ready to work offline')

    // Show offline-ready notification (optional)
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Livininbintaro is ready to work offline!')
    }
  },
  onRegistered(registration) {
    console.log('Service Worker registered:', registration)
  },
  onRegisterError(error) {
    console.error('Service Worker registration failed:', error)
  }
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```

---

### Step 3: Offline Mode Implementation

**Create Offline Composable:**

```javascript
// frontend/src/composables/useOffline.js
import { ref, onMounted, onUnmounted } from 'vue'

export function useOffline() {
  const isOnline = ref(navigator.onLine)
  const showOfflineBanner = ref(false)

  const updateOnlineStatus = () => {
    isOnline.value = navigator.onLine

    if (!isOnline.value) {
      showOfflineBanner.value = true
    } else {
      // Hide banner after 3 seconds when back online
      setTimeout(() => {
        showOfflineBanner.value = false
      }, 3000)
    }
  }

  onMounted(() => {
    window.addEventListener('online', updateOnlineStatus)
    window.addEventListener('offline', updateOnlineStatus)
  })

  onUnmounted(() => {
    window.removeEventListener('online', updateOnlineStatus)
    window.removeEventListener('offline', updateOnlineStatus)
  })

  return {
    isOnline,
    showOfflineBanner
  }
}
```

**Add Offline Banner to App.vue:**

```vue
<!-- frontend/src/App.vue -->
<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <!-- Offline Banner -->
    <transition name="slide-down">
      <div
        v-if="showOfflineBanner"
        class="fixed top-0 left-0 right-0 z-50 bg-yellow-500 text-white px-4 py-2 text-center"
      >
        <span v-if="!isOnline">
          📡 You are offline. Viewing cached data.
        </span>
        <span v-else>
          ✅ Back online! Syncing...
        </span>
      </div>
    </transition>

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
import { useOffline } from '@/composables/useOffline'
import NavBar from './components/NavBar.vue'
import Footer from './components/Footer.vue'

const route = useRoute()
const isLoginPage = computed(() => route.name === 'login')
const { isOnline, showOfflineBanner } = useOffline()
</script>

<style>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: transform 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  transform: translateY(-100%);
}
</style>
```

---

### Step 4: Offline Queue for CRM Actions

**Create Offline Queue Composable:**

```javascript
// frontend/src/composables/useOfflineQueue.js
import { ref, watch } from 'vue'
import { useOffline } from './useOffline'

export function useOfflineQueue() {
  const { isOnline } = useOffline()
  const queue = ref([])
  const QUEUE_KEY = 'livinin-offline-queue'

  // Load queue from localStorage on init
  const loadQueue = () => {
    const stored = localStorage.getItem(QUEUE_KEY)
    if (stored) {
      queue.value = JSON.parse(stored)
    }
  }

  // Save queue to localStorage
  const saveQueue = () => {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(queue.value))
  }

  // Add action to queue
  const addToQueue = (action) => {
    const queueItem = {
      id: Date.now(),
      action,
      timestamp: new Date().toISOString(),
      retries: 0
    }

    queue.value.push(queueItem)
    saveQueue()

    console.log('Action added to offline queue:', queueItem)
  }

  // Process queue when back online
  const processQueue = async () => {
    if (!isOnline.value || queue.value.length === 0) return

    console.log(`Processing ${queue.value.length} queued actions...`)

    const itemsToProcess = [...queue.value]

    for (const item of itemsToProcess) {
      try {
        // Execute the action
        await item.action()

        // Remove from queue on success
        queue.value = queue.value.filter(q => q.id !== item.id)
        saveQueue()

        console.log('Queue item processed:', item.id)
      } catch (error) {
        console.error('Failed to process queue item:', error)

        // Increment retry count
        const queueItem = queue.value.find(q => q.id === item.id)
        if (queueItem) {
          queueItem.retries += 1

          // Remove if retries exceed 3
          if (queueItem.retries > 3) {
            console.error('Max retries exceeded for queue item:', item.id)
            queue.value = queue.value.filter(q => q.id !== item.id)
          }

          saveQueue()
        }
      }
    }

    if (queue.value.length === 0) {
      console.log('All queued actions processed successfully')
    }
  }

  // Watch online status and process queue when online
  watch(isOnline, (online) => {
    if (online) {
      processQueue()
    }
  })

  // Load queue on init
  loadQueue()

  return {
    queue,
    addToQueue,
    processQueue
  }
}
```

**Integrate Queue in API Client:**

```javascript
// frontend/src/api/client.js
import axios from 'axios'
import { useOfflineQueue } from '@/composables/useOfflineQueue'

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

// Response interceptor: handle offline
client.interceptors.response.use(
  response => response,
  error => {
    if (!navigator.onLine && error.message === 'Network Error') {
      // Queue the failed request
      const { addToQueue } = useOfflineQueue()

      addToQueue(async () => {
        return axios.request(error.config)
      })

      return Promise.reject({
        message: 'Action queued for when you are back online',
        offline: true
      })
    }

    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }

    return Promise.reject(error)
  }
)

export default client
```

---

### Step 5: Push Notifications

**Backend: Web Push Setup**

```python
# backend/services/notifications.py
from pywebpush import webpush, WebPushException
import json
from config import settings

class WebPushService:
    def __init__(self):
        self.vapid_private_key = settings.VAPID_PRIVATE_KEY
        self.vapid_public_key = settings.VAPID_PUBLIC_KEY
        self.vapid_claims = {
            "sub": "mailto:admin@livininbintaro.my.id"
        }

    def send_notification(self, subscription_info, message_body):
        """Send push notification to subscribed client"""
        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(message_body),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims
            )
            return True
        except WebPushException as e:
            print(f"Push notification failed: {e}")
            return False

web_push_service = WebPushService()
```

**Backend: Subscription Endpoints**

```python
# backend/routers/notifications.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import PushSubscription
from services.notifications import web_push_service
from pydantic import BaseModel

router = APIRouter()

class SubscriptionInfo(BaseModel):
    endpoint: str
    keys: dict

@router.post("/subscribe")
def subscribe_push(
    subscription: SubscriptionInfo,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Save push notification subscription"""
    push_sub = PushSubscription(
        user_id=user_id,
        endpoint=subscription.endpoint,
        p256dh=subscription.keys['p256dh'],
        auth=subscription.keys['auth']
    )
    db.add(push_sub)
    db.commit()

    return {"status": "subscribed"}

@router.post("/notify/{user_id}")
def send_push_notification(
    user_id: int,
    message: str,
    db: Session = Depends(get_db)
):
    """Send push notification to user"""
    subscriptions = db.query(PushSubscription).filter(
        PushSubscription.user_id == user_id
    ).all()

    for sub in subscriptions:
        subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {
                "p256dh": sub.p256dh,
                "auth": sub.auth
            }
        }

        web_push_service.send_notification(
            subscription_info,
            {
                "title": "Livininbintaro",
                "body": message,
                "icon": "/icons/icon-192.png",
                "badge": "/icons/icon-72.png"
            }
        )

    return {"status": "sent", "count": len(subscriptions)}
```

**Frontend: Push Notification Setup**

```javascript
// frontend/src/composables/usePushNotifications.js
import { ref } from 'vue'
import api from '@/api'

export function usePushNotifications() {
  const isSupported = ref('Notification' in window && 'serviceWorker' in navigator)
  const permission = ref(Notification.permission)
  const subscription = ref(null)

  const VAPID_PUBLIC_KEY = 'YOUR_VAPID_PUBLIC_KEY'  // From backend

  const urlBase64ToUint8Array = (base64String) => {
    const padding = '='.repeat((4 - base64String.length % 4) % 4)
    const base64 = (base64String + padding)
      .replace(/\-/g, '+')
      .replace(/_/g, '/')

    const rawData = window.atob(base64)
    const outputArray = new Uint8Array(rawData.length)

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i)
    }
    return outputArray
  }

  const requestPermission = async () => {
    if (!isSupported.value) {
      console.warn('Push notifications not supported')
      return false
    }

    const result = await Notification.requestPermission()
    permission.value = result

    if (result === 'granted') {
      await subscribeToPush()
      return true
    }

    return false
  }

  const subscribeToPush = async () => {
    try {
      const registration = await navigator.serviceWorker.ready

      const sub = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
      })

      subscription.value = sub

      // Send subscription to backend
      const userId = JSON.parse(localStorage.getItem('user'))?.id
      if (userId) {
        await api.notifications.subscribe(userId, sub.toJSON())
      }

      console.log('Push notification subscription successful')
    } catch (error) {
      console.error('Failed to subscribe to push notifications:', error)
    }
  }

  const unsubscribe = async () => {
    if (subscription.value) {
      await subscription.value.unsubscribe()
      subscription.value = null
    }
  }

  return {
    isSupported,
    permission,
    subscription,
    requestPermission,
    subscribeToPush,
    unsubscribe
  }
}
```

**Add Push Notification Prompt:**

```vue
<!-- frontend/src/components/PushNotificationPrompt.vue -->
<template>
  <div
    v-if="showPrompt"
    class="fixed bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 max-w-sm z-50"
  >
    <button
      @click="dismiss"
      class="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
    >
      ✕
    </button>

    <div class="flex items-start gap-3">
      <div class="text-3xl">🔔</div>
      <div class="flex-1">
        <h3 class="font-bold mb-1">Enable Notifications</h3>
        <p class="text-sm text-gray-600 mb-3">
          Get instant alerts for new leads and follow-up reminders
        </p>
        <div class="flex gap-2">
          <button
            @click="enableNotifications"
            class="bg-green-800 text-white px-4 py-2 rounded text-sm hover:bg-green-900"
          >
            Enable
          </button>
          <button
            @click="dismiss"
            class="text-gray-600 px-4 py-2 rounded text-sm hover:bg-gray-100"
          >
            Not Now
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { usePushNotifications } from '@/composables/usePushNotifications'

const { permission, requestPermission } = usePushNotifications()
const showPrompt = ref(false)

const enableNotifications = async () => {
  const granted = await requestPermission()
  if (granted) {
    showPrompt.value = false
    localStorage.setItem('push-prompt-dismissed', 'granted')
  }
}

const dismiss = () => {
  showPrompt.value = false
  localStorage.setItem('push-prompt-dismissed', 'dismissed')
}

onMounted(() => {
  // Show prompt after 30 seconds if not already dismissed
  setTimeout(() => {
    const dismissed = localStorage.getItem('push-prompt-dismissed')
    if (!dismissed && permission.value === 'default') {
      showPrompt.value = true
    }
  }, 30000)
})
</script>
```

---

### Step 6: Install Prompt

**Create Install Prompt Composable:**

```javascript
// frontend/src/composables/useInstallPrompt.js
import { ref, onMounted } from 'vue'

export function useInstallPrompt() {
  const deferredPrompt = ref(null)
  const showInstallPrompt = ref(false)

  const handleBeforeInstallPrompt = (e) => {
    // Prevent default install prompt
    e.preventDefault()

    // Store event for later use
    deferredPrompt.value = e

    // Show custom install prompt after 10 seconds
    setTimeout(() => {
      const dismissed = localStorage.getItem('install-prompt-dismissed')
      if (!dismissed) {
        showInstallPrompt.value = true
      }
    }, 10000)
  }

  const installApp = async () => {
    if (!deferredPrompt.value) return

    // Show native install prompt
    deferredPrompt.value.prompt()

    // Wait for user choice
    const { outcome } = await deferredPrompt.value.userChoice

    if (outcome === 'accepted') {
      console.log('User accepted install prompt')
      localStorage.setItem('install-prompt-dismissed', 'installed')
    } else {
      console.log('User dismissed install prompt')
    }

    deferredPrompt.value = null
    showInstallPrompt.value = false
  }

  const dismissInstallPrompt = () => {
    showInstallPrompt.value = false
    localStorage.setItem('install-prompt-dismissed', 'dismissed')
  }

  onMounted(() => {
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)

    // Detect if already installed
    window.addEventListener('appinstalled', () => {
      console.log('PWA installed successfully')
      localStorage.setItem('install-prompt-dismissed', 'installed')
    })
  })

  return {
    showInstallPrompt,
    installApp,
    dismissInstallPrompt
  }
}
```

**Install Prompt Component:**

```vue
<!-- frontend/src/components/InstallPrompt.vue -->
<template>
  <div
    v-if="showInstallPrompt"
    class="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:max-w-sm bg-green-800 text-white rounded-lg shadow-lg p-4 z-50"
  >
    <button
      @click="dismissInstallPrompt"
      class="absolute top-2 right-2 text-white opacity-75 hover:opacity-100"
    >
      ✕
    </button>

    <div class="flex items-start gap-3">
      <div class="text-3xl">📱</div>
      <div class="flex-1">
        <h3 class="font-bold mb-1">Install Livininbintaro</h3>
        <p class="text-sm opacity-90 mb-3">
          Add to your home screen for quick access like a native app
        </p>
        <button
          @click="installApp"
          class="bg-white text-green-800 px-4 py-2 rounded text-sm font-semibold hover:bg-gray-100"
        >
          Install Now
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useInstallPrompt } from '@/composables/useInstallPrompt'

const { showInstallPrompt, installApp, dismissInstallPrompt } = useInstallPrompt()
</script>
```

**Add to App.vue:**

```vue
<!-- frontend/src/App.vue -->
<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <OfflineBanner />
    <NavBar v-if="!isLoginPage" />
    <main>
      <router-view />
    </main>
    <Footer v-if="!isLoginPage" />

    <!-- PWA Prompts -->
    <InstallPrompt />
    <PushNotificationPrompt v-if="isAuthenticated" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/store'
import NavBar from './components/NavBar.vue'
import Footer from './components/Footer.vue'
import InstallPrompt from './components/InstallPrompt.vue'
import PushNotificationPrompt from './components/PushNotificationPrompt.vue'
import OfflineBanner from './components/OfflineBanner.vue'

const route = useRoute()
const authStore = useAuthStore()
const isLoginPage = computed(() => route.name === 'login')
const isAuthenticated = computed(() => authStore.isAuthenticated)
</script>
```

---

## TESTING PWA FEATURES

### Test Offline Mode

```bash
# 1. Open DevTools → Network tab
# 2. Check "Offline" checkbox
# 3. Navigate to /search
# Expected: Cached listings display

# 4. Refresh page
# Expected: Page loads from cache

# 5. Check DevTools → Application → Cache Storage
# Expected: api-listings-cache, images-cache populated
```

### Test Offline Queue

```javascript
// 1. Login to dashboard
// 2. Go offline (DevTools → Network → Offline)
// 3. Try to add a note to a lead
// Expected: "Action queued for when you are back online" message

// 4. Go back online
// Expected: Note syncs automatically, appears in timeline

// 5. Check localStorage → livinin-offline-queue
// Expected: Empty (queue processed)
```

### Test Push Notifications

```bash
# 1. Enable notifications when prompted
# 2. From another browser/device, trigger new lead creation
# Expected: Push notification appears on first device

# Test via backend:
curl -X POST https://livininbintaro.my.id/api/notifications/notify/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "New lead: Budi Santoso"}'
```

### Test Install Prompt

```bash
# Chrome Desktop:
# 1. Open https://livininbintaro.my.id
# 2. Wait 10 seconds
# Expected: Install prompt appears bottom-left
# 3. Click "Install Now"
# Expected: Native install dialog appears

# Chrome Mobile:
# 1. Open site in Chrome mobile
# 2. Wait 10 seconds
# Expected: Install banner appears
# 3. Tap "Install"
# Expected: App icon added to home screen
```

### Verify Manifest

```bash
# DevTools → Application → Manifest
# Expected fields:
# - Name: Livininbintaro Property Marketplace
# - Short name: Livinin
# - Start URL: /
# - Display: standalone
# - Theme color: #1B4332
# - Icons: 8 sizes (72, 96, 128, 144, 152, 192, 384, 512)
```

---

## PRODUCTION CHECKLIST

Before deploying PWA features:

```
[ ] Service worker registered successfully
[ ] Manifest.json valid (test with lighthouse)
[ ] Icons generated (72, 96, 128, 144, 152, 192, 384, 512)
[ ] HTTPS enabled (required for PWA)
[ ] Offline mode works (test with airplane mode)
[ ] Offline queue syncs when back online
[ ] Push notifications permission requested
[ ] Push notifications received successfully
[ ] Install prompt appears after 10 seconds
[ ] Install works on Chrome desktop
[ ] Install works on Chrome mobile
[ ] Install works on Safari iOS
[ ] Lighthouse PWA score >90
[ ] No console errors in service worker
```

---

## TROUBLESHOOTING

### Service Worker Not Updating

```javascript
// Force update service worker (browser console)
navigator.serviceWorker.getRegistrations().then(function(registrations) {
  for(let registration of registrations) {
    registration.update()
  }
})
```

### Push Notifications Not Working

```bash
# Check VAPID keys configured
# backend/.env
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...

# Check subscription saved
curl https://livininbintaro.my.id/api/notifications/subscriptions \
  -H "Authorization: Bearer <token>"

# Test notification manually
curl -X POST https://livininbintaro.my.id/api/notifications/test \
  -H "Authorization: Bearer <token>"
```

### Offline Queue Not Syncing

```javascript
// Check queue in localStorage (browser console)
JSON.parse(localStorage.getItem('livinin-offline-queue'))

// Manually trigger queue processing
import { useOfflineQueue } from '@/composables/useOfflineQueue'
const { processQueue } = useOfflineQueue()
processQueue()
```

---

**Document Version:** 1.0
**Last Updated:** 2026-03-14
**Next Review:** After Phase 4 implementation
