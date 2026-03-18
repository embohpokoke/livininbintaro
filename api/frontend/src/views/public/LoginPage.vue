<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(223,109,59,0.22),_transparent_32%),linear-gradient(135deg,_#264653,_#1f2933)] px-4 py-10">
    <div class="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[1fr_0.9fr]">
      <section class="rounded-[2.5rem] border border-white/10 bg-white/8 p-8 text-white backdrop-blur">
        <p class="text-sm uppercase tracking-[0.4em] text-white/60">Agent workspace</p>
        <h1 class="mt-5 max-w-xl text-5xl leading-tight">Listings, leads, WhatsApp, and follow-up work in one place.</h1>
        <p class="mt-6 max-w-xl text-base leading-8 text-white/75">
          This is the v2 transition entry point for Ocha’s daily workflow. Use your username or your
          `@livininbintaro.my.id` email alias.
        </p>
      </section>

      <form class="rounded-[2.5rem] bg-white p-8 shadow-card" @submit.prevent="submit">
        <p class="text-xs uppercase tracking-[0.3em] text-forest/45">Sign in</p>
        <h2 class="mt-3 text-4xl text-forest">Agent Login</h2>
        <div class="mt-8 space-y-4">
          <input v-model="identifier" class="field" placeholder="Email or username" />
          <input v-model="password" type="password" class="field" placeholder="Password" />
        </div>
        <p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p>
        <button class="btn-primary mt-8 w-full" :disabled="loading">
          {{ loading ? 'Signing in...' : 'Open Dashboard' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../../store'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const identifier = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await authStore.loginWithPassword({
      identifier: identifier.value,
      password: password.value
    })
    router.push(route.query.redirect || '/dashboard')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
