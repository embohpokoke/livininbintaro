<template>
  <div class="page-shell" v-if="listing">
    <div class="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
      <section class="space-y-4">
        <div class="glass-panel overflow-hidden">
          <img
            v-if="heroImage"
            :src="heroImage"
            :alt="listing.property_name"
            class="h-[26rem] w-full object-cover"
          />
          <div v-else class="flex h-[26rem] items-center justify-center bg-sand text-forest/60">
            Image pending
          </div>
        </div>
        <div class="grid gap-4 sm:grid-cols-3">
          <article class="metric-card"><p class="text-xs uppercase tracking-[0.3em] text-forest/45">Bedrooms</p><p class="mt-3 text-3xl text-forest">{{ listing.bedrooms || 0 }}</p></article>
          <article class="metric-card"><p class="text-xs uppercase tracking-[0.3em] text-forest/45">Bathrooms</p><p class="mt-3 text-3xl text-forest">{{ listing.bathrooms || 0 }}</p></article>
          <article class="metric-card"><p class="text-xs uppercase tracking-[0.3em] text-forest/45">Building</p><p class="mt-3 text-3xl text-forest">{{ listing.building_area || 0 }} m²</p></article>
        </div>
      </section>

      <section class="space-y-6">
        <div class="glass-panel p-8">
          <p class="text-xs uppercase tracking-[0.3em] text-forest/50">{{ listing.district }}</p>
          <h1 class="mt-3 text-5xl text-forest">{{ listing.property_name }}</h1>
          <p class="mt-4 text-2xl font-semibold text-ember">{{ formattedPrice }}</p>
          <p class="mt-6 whitespace-pre-line leading-8 text-forest/75">
            {{ listing.description || 'Detailed property description is still being synced.' }}
          </p>
        </div>
        <div class="glass-panel p-6">
          <p class="text-xs uppercase tracking-[0.3em] text-forest/50">Agent workflow</p>
          <p class="mt-4 leading-8 text-forest/70">
            This detail page is designed for public discovery now, and for quick lead handoff into the
            CRM after login in v2.
          </p>
          <RouterLink class="btn-primary mt-6" to="/login">Open Agent Workspace</RouterLink>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import * as listingsApi from '../../api/listings'

const route = useRoute()
const listing = ref(null)

const heroImage = computed(() => listing.value?.images?.[0] || '')
const formattedPrice = computed(() => {
  if (!listing.value?.price) return 'Price on request'
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0
  }).format(listing.value.price)
})

onMounted(async () => {
  const { data } = await listingsApi.getPublicListing(route.params.id)
  listing.value = data
})
</script>
