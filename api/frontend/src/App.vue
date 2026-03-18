<template>
  <div class="min-h-screen bg-canvas text-dusk">
    <Transition name="slide-down">
      <div
        v-if="showOfflineBanner"
        class="fixed inset-x-4 top-4 z-50 rounded-full bg-ember px-4 py-3 text-center text-sm font-semibold text-white shadow-card"
      >
        <span v-if="!isOnline">Offline mode active. Cached property data is available.</span>
        <span v-else>Back online. Syncing queued actions.</span>
      </div>
    </Transition>

    <div class="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(223,109,59,0.14),_transparent_38%),linear-gradient(180deg,_#f6f1e7_0%,_#efe4d0_100%)]" />

    <NavBar v-if="!route.meta.hideChrome" />
    <main>
      <RouterView />
    </main>
    <Footer v-if="!route.meta.hideChrome" />
  </div>
</template>

<script setup>
import { RouterView, useRoute } from 'vue-router'

import Footer from './components/Footer.vue'
import NavBar from './components/NavBar.vue'
import { useOffline } from './composables/useOffline'

const route = useRoute()
const { isOnline, showOfflineBanner } = useOffline()
</script>

<style>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.25s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}
</style>
