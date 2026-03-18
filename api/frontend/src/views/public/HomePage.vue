<template>
  <div class="page-shell space-y-10 py-10">
    <section class="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
      <div class="glass-panel overflow-hidden p-8 sm:p-10">
        <p class="text-sm uppercase tracking-[0.35em] text-forest/55">Livininbintaro V2</p>
        <h1 class="mt-4 max-w-3xl text-5xl leading-tight text-forest sm:text-6xl">
          One property app for market discovery, field work, and lead conversion.
        </h1>
        <p class="mt-6 max-w-2xl text-base leading-8 text-forest/75">
          Browse the marketplace publicly, then switch straight into the agent dashboard for leads,
          WhatsApp conversations, follow-ups, and content planning.
        </p>
        <div class="mt-8 flex flex-wrap gap-3">
          <RouterLink class="btn-primary" to="/search">Explore Listings</RouterLink>
          <RouterLink class="btn-secondary" to="/login">Agent Workspace</RouterLink>
        </div>
      </div>

      <div class="grid gap-4">
        <article class="metric-card">
          <p class="text-xs uppercase tracking-[0.3em] text-forest/50">Inventory</p>
          <p class="mt-4 text-4xl font-semibold text-forest">{{ stats.total_listings ?? '...' }}</p>
          <p class="mt-3 text-sm text-forest/65">Active property stock ready for search and offline caching.</p>
        </article>
        <article class="metric-card bg-forest text-white">
          <p class="text-xs uppercase tracking-[0.3em] text-white/65">Agent Mode</p>
          <p class="mt-4 text-3xl font-semibold">Leads, WA threads, and field-ready PWA.</p>
        </article>
      </div>
    </section>

    <section class="space-y-4">
      <div class="flex items-end justify-between gap-4">
        <div>
          <p class="text-xs uppercase tracking-[0.3em] text-forest/50">Featured</p>
          <h2 class="text-4xl text-forest">Fresh listings with room to move fast</h2>
        </div>
        <RouterLink class="btn-secondary" to="/search">See all listings</RouterLink>
      </div>
      <div class="grid gap-5 lg:grid-cols-3">
        <PropertyCard v-for="listing in featured" :key="listing.id" :listing="listing" />
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'

import PropertyCard from '../../components/PropertyCard.vue'
import * as listingsApi from '../../api/listings'

const featured = ref([])
const stats = reactive({
  total_listings: null,
  total_rumah: null
})

onMounted(async () => {
  const [featuredResponse, statsResponse] = await Promise.all([
    listingsApi.getPublicListings({ limit: 3 }),
    listingsApi.getPublicStats()
  ])
  featured.value = featuredResponse.data.data
  Object.assign(stats, statsResponse.data)
})
</script>
