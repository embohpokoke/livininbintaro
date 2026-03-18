<template>
  <div
    class="inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold"
    :class="toneClass"
    :title="reason || 'AI score pending'"
  >
    <span class="h-2 w-2 rounded-full bg-current opacity-70" />
    <span>{{ scoreLabel }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  score: {
    type: Number,
    default: null
  },
  reason: {
    type: String,
    default: ''
  }
})

const toneClass = computed(() => {
  if (props.score >= 80) return 'bg-emerald-100 text-emerald-700'
  if (props.score >= 60) return 'bg-amber-100 text-amber-700'
  if (props.score >= 40) return 'bg-sky-100 text-sky-700'
  return 'bg-slate-100 text-slate-600'
})

const scoreLabel = computed(() => {
  if (props.score == null) return 'AI pending'
  return `AI ${props.score}`
})
</script>
