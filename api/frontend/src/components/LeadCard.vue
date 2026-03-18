<template>
  <RouterLink
    :to="`/leads/${lead.id}`"
    class="block rounded-[1.5rem] border border-forest/10 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-card"
    draggable="true"
    @dragstart="$emit('dragstart', lead)"
  >
    <div class="flex items-start justify-between gap-3">
      <div>
        <p class="text-xs uppercase tracking-[0.25em] text-forest/50">{{ lead.source || 'manual' }}</p>
        <h3 class="mt-1 text-lg font-semibold text-forest">{{ lead.name }}</h3>
        <p class="text-sm text-forest/65">{{ lead.phone || 'No phone' }}</p>
      </div>
      <AIScoreBadge :score="lead.ai_score" :reason="lead.ai_reasoning" />
    </div>
  </RouterLink>
</template>

<script setup>
import { RouterLink } from 'vue-router'

import AIScoreBadge from './AIScoreBadge.vue'

defineProps({
  lead: {
    type: Object,
    required: true
  }
})

defineEmits(['dragstart'])
</script>
