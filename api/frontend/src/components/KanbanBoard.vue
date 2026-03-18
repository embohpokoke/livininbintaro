<template>
  <div class="flex snap-x gap-4 overflow-x-auto pb-2">
    <section
      v-for="column in columns"
      :key="column.id"
      class="min-w-[18rem] flex-1 snap-start rounded-[2rem] border border-forest/10 bg-white/60 p-4 shadow-card"
      @dragover.prevent
      @drop="dropLead(column.id)"
    >
      <div class="mb-4 flex items-center justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.25em] text-forest/50">{{ column.id }}</p>
          <h3 class="text-2xl text-forest">{{ column.title }}</h3>
        </div>
        <span class="rounded-full bg-sand px-3 py-1 text-sm font-semibold text-forest">{{ column.items.length }}</span>
      </div>

      <div class="space-y-3">
        <LeadCard
          v-for="lead in column.items"
          :key="lead.id"
          :lead="lead"
          @dragstart="draggedLead = $event"
        />
        <div
          v-if="!column.items.length"
          class="rounded-[1.5rem] border border-dashed border-forest/15 px-4 py-8 text-center text-sm text-forest/45"
        >
          Drop a lead here
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'

import LeadCard from './LeadCard.vue'

defineProps({
  columns: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['status-change'])
const draggedLead = ref(null)

function dropLead(status) {
  if (!draggedLead.value || draggedLead.value.status === status) return
  emit('status-change', { leadId: draggedLead.value.id, status })
  draggedLead.value = null
}
</script>
