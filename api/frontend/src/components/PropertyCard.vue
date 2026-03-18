<template>
  <article class="glass-panel overflow-hidden">
    <div class="relative h-52 overflow-hidden bg-sand">
      <img
        v-if="listing.images?.length"
        :src="listing.images[0]"
        :alt="listing.property_name"
        class="h-full w-full object-cover transition duration-500 hover:scale-105"
      />
      <div v-else class="flex h-full items-center justify-center bg-gradient-to-br from-sand to-white text-sm text-forest/60">
        Image pending
      </div>
      <span class="absolute left-4 top-4 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em] text-forest">
        {{ listing.transaction_type || 'listing' }}
      </span>
    </div>

    <div class="space-y-4 p-5">
      <div>
        <p class="text-xs uppercase tracking-[0.25em] text-forest/60">{{ listing.district || 'Bintaro Area' }}</p>
        <h3 class="mt-2 text-2xl text-forest">{{ listing.property_name }}</h3>
      </div>

      <div class="flex items-center justify-between gap-4">
        <p class="text-lg font-semibold text-ember">{{ formattedPrice }}</p>
        <div class="flex gap-3 text-sm text-forest/70">
          <span>{{ listing.bedrooms || 0 }} bd</span>
          <span>{{ listing.bathrooms || 0 }} ba</span>
          <span>{{ listing.building_area || 0 }} m²</span>
        </div>
      </div>

      <RouterLink class="btn-secondary w-full" :to="`/property/${listing.id}`">
        View Property
      </RouterLink>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const props = defineProps({
  listing: {
    type: Object,
    required: true
  }
})

const formattedPrice = computed(() => {
  if (!props.listing.price) return 'Price on request'
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0
  }).format(props.listing.price)
})
</script>
