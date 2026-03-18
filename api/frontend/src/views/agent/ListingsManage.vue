<template>
  <div class="page-shell space-y-6">
    <section class="glass-panel p-6">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.3em] text-forest/45">Agent management</p>
          <h1 class="text-4xl text-forest">Listings workspace</h1>
        </div>
        <button class="btn-primary" @click="load">Refresh inventory</button>
      </div>
    </section>

    <section class="grid gap-4">
      <article v-for="listing in items" :key="listing.id" class="glass-panel p-5">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.25em] text-forest/45">{{ listing.listing_code }}</p>
            <h2 class="mt-2 text-2xl text-forest">{{ listing.property_name }}</h2>
            <p class="mt-2 text-sm text-forest/65">{{ listing.district || 'Unknown area' }}</p>
          </div>
          <div class="flex items-center gap-3">
            <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="listing.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'">
              {{ listing.is_active ? 'Active' : 'Inactive' }}
            </span>
            <button class="btn-secondary" @click="toggleActive(listing)">
              {{ listing.is_active ? 'Deactivate' : 'Activate' }}
            </button>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import * as listingsApi from '../../api/listings'

const items = ref([])

async function load() {
  const { data } = await listingsApi.getAgentListings({ limit: 25 })
  items.value = data.data
}

async function toggleActive(listing) {
  await listingsApi.updateListing(listing.id, { is_active: !listing.is_active })
  await load()
}

onMounted(load)
</script>
