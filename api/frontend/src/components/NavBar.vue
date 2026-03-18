<template>
  <header class="sticky top-0 z-40 border-b border-forest/10 bg-canvas/80 backdrop-blur">
    <div class="page-shell flex items-center justify-between gap-4 py-4">
      <RouterLink class="flex items-center gap-3 text-forest" to="/">
        <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-forest text-lg font-bold text-white">L</div>
        <div>
          <p class="font-display text-xl">Livininbintaro</p>
          <p class="text-xs uppercase tracking-[0.3em] text-forest/60">Property + CRM</p>
        </div>
      </RouterLink>

      <nav class="hidden items-center gap-2 md:flex">
        <RouterLink class="btn-secondary" to="/search">Search</RouterLink>
        <RouterLink v-if="authStore.isAuthenticated" class="btn-secondary" to="/dashboard">Dashboard</RouterLink>
        <RouterLink v-if="authStore.isAuthenticated" class="btn-secondary" to="/leads">Leads</RouterLink>
        <RouterLink v-if="authStore.isAuthenticated" class="btn-secondary" to="/content">Content</RouterLink>
        <RouterLink v-if="!authStore.isAuthenticated" class="btn-primary" to="/login">Agent Login</RouterLink>
        <button v-else class="btn-primary" @click="logout">Logout</button>
      </nav>

      <button class="btn-secondary md:hidden" @click="open = !open">Menu</button>
    </div>

    <div v-if="open" class="border-t border-forest/10 bg-white/90 md:hidden">
      <div class="page-shell flex flex-col gap-3 py-4">
        <RouterLink class="btn-secondary" to="/search" @click="open = false">Search</RouterLink>
        <RouterLink v-if="authStore.isAuthenticated" class="btn-secondary" to="/dashboard" @click="open = false">Dashboard</RouterLink>
        <RouterLink v-if="authStore.isAuthenticated" class="btn-secondary" to="/leads" @click="open = false">Leads</RouterLink>
        <RouterLink v-if="authStore.isAuthenticated" class="btn-secondary" to="/content" @click="open = false">Content</RouterLink>
        <RouterLink v-if="authStore.isAuthenticated" class="btn-secondary" to="/manage/listings" @click="open = false">Listings</RouterLink>
        <RouterLink v-if="!authStore.isAuthenticated" class="btn-primary" to="/login" @click="open = false">Agent Login</RouterLink>
        <button v-else class="btn-primary" @click="logout">Logout</button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { useAuthStore } from '../store'

const authStore = useAuthStore()
const router = useRouter()
const open = ref(false)

function logout() {
  open.value = false
  authStore.logout()
  router.push('/')
}
</script>
