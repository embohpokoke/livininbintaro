<template>
  <div class="page-shell space-y-8">
    <section class="glass-panel p-6">
      <div class="grid gap-4 lg:grid-cols-[2fr_repeat(4,1fr)]">
        <input v-model="filters.q" class="field" placeholder="Search by name, area, address..." />
        <select v-model="filters.property_type" class="field">
          <option value="">Property Type</option>
          <option value="rumah">Rumah</option>
          <option value="apartemen">Apartemen</option>
          <option value="tanah">Tanah</option>
          <option value="ruko">Ruko</option>
        </select>
        <select v-model="filters.transaction_type" class="field">
          <option value="">Transaction</option>
          <option value="dijual">Dijual</option>
          <option value="disewa">Disewa</option>
        </select>
        <select v-model="filters.district" class="field">
          <option value="">District</option>
          <option v-for="district in districts" :key="district.district" :value="district.district">
            {{ district.district }}
          </option>
        </select>
        <button class="btn-primary w-full" @click="fetchListings(1)">Apply</button>
      </div>
    </section>

    <section class="flex items-end justify-between gap-4">
      <div>
        <p class="text-xs uppercase tracking-[0.3em] text-forest/50">Search results</p>
        <h1 class="text-4xl text-forest">{{ store.total }} listings</h1>
      </div>
      <div class="flex gap-3">
        <button class="btn-secondary" :disabled="store.page <= 1" @click="fetchListings(store.page - 1)">Previous</button>
        <button class="btn-secondary" :disabled="store.page >= store.totalPages" @click="fetchListings(store.page + 1)">Next</button>
      </div>
    </section>

    <section class="grid gap-5 lg:grid-cols-3">
      <PropertyCard v-for="listing in store.items" :key="listing.id" :listing="listing" />
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import PropertyCard from '../../components/PropertyCard.vue'
import * as listingsApi from '../../api/listings'
import { useListingsStore } from '../../store'

const store = useListingsStore()
const districts = ref([])
const filters = reactive({
  q: '',
  property_type: '',
  transaction_type: '',
  district: ''
})

async function fetchListings(page = 1) {
  if (filters.q) {
    const { data } = await listingsApi.searchPublicListings({
      q: filters.q,
      page,
      limit: 9
    })
    store.items = data.data
    store.page = data.page
    store.totalPages = data.total_pages
    store.total = data.total
    return
  }

  await store.fetchPublic({
    page,
    limit: 9,
    property_type: filters.property_type || undefined,
    transaction_type: filters.transaction_type || undefined,
    district: filters.district || undefined
  })
}

onMounted(async () => {
  const { data } = await listingsApi.getDistricts()
  districts.value = data.data
  await fetchListings()
})
</script>
