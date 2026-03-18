import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './store'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('./views/public/HomePage.vue')
  },
  {
    path: '/search',
    name: 'search',
    component: () => import('./views/public/SearchPage.vue')
  },
  {
    path: '/property/:id',
    name: 'property-detail',
    component: () => import('./views/public/PropertyDetail.vue')
  },
  {
    path: '/login',
    name: 'login',
    meta: { hideChrome: true },
    component: () => import('./views/public/LoginPage.vue')
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    meta: { requiresAuth: true, role: ['agent', 'admin'] },
    component: () => import('./views/agent/DashboardPage.vue')
  },
  {
    path: '/leads',
    name: 'leads',
    meta: { requiresAuth: true, role: ['agent', 'admin'] },
    component: () => import('./views/agent/LeadsPage.vue')
  },
  {
    path: '/leads/:id',
    name: 'lead-detail',
    meta: { requiresAuth: true, role: ['agent', 'admin'] },
    component: () => import('./views/agent/LeadDetailPage.vue')
  },
  {
    path: '/content',
    name: 'content',
    meta: { requiresAuth: true, role: ['agent', 'admin'] },
    component: () => import('./views/agent/ContentCalendar.vue')
  },
  {
    path: '/manage/listings',
    name: 'manage-listings',
    meta: { requiresAuth: true, role: ['agent', 'admin'] },
    component: () => import('./views/agent/ListingsManage.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  authStore.hydrate()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.role && !to.meta.role.includes(authStore.user?.role)) {
    return { name: 'home' }
  }

  if (to.name === 'login' && authStore.isAuthenticated) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
