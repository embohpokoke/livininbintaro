<template>
  <div class="space-y-4">
    <article
      v-for="item in items"
      :key="`${item.type || 'item'}-${item.id}`"
      class="rounded-[1.5rem] border border-forest/10 bg-white p-4"
    >
      <div class="flex items-center justify-between gap-3">
        <p class="text-xs uppercase tracking-[0.25em] text-forest/55">{{ item.type || item.activity_type || item.note_type }}</p>
        <time class="text-xs text-forest/50">{{ formatDate(item.created_at || item.timestamp) }}</time>
      </div>
      <p class="mt-3 whitespace-pre-line text-sm leading-7 text-forest/80">
        {{ item.content || item.description || item.message_text }}
      </p>
    </article>
  </div>
</template>

<script setup>
function formatDate(value) {
  if (!value) return 'Unknown time'
  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(new Date(value))
}

defineProps({
  items: {
    type: Array,
    default: () => []
  }
})
</script>
