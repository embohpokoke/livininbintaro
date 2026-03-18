<template>
  <section class="space-y-5">
    <div class="glass-panel max-h-[32rem] space-y-4 overflow-y-auto p-4">
      <div
        v-for="message in messages"
        :key="message.id"
        class="flex"
        :class="message.direction === 'outbound' ? 'justify-end' : 'justify-start'"
      >
        <article
          class="max-w-[85%] rounded-[1.5rem] px-4 py-3 text-sm leading-7 shadow-sm"
          :class="message.direction === 'outbound' ? 'bg-leaf text-white' : 'bg-white text-forest'"
        >
          <img
            v-if="message.media_url"
            :src="message.media_url"
            alt="Media attachment"
            class="mb-3 max-h-56 w-full rounded-2xl object-cover"
          />
          <p class="whitespace-pre-line">{{ message.message_text }}</p>
          <time class="mt-3 block text-[11px] opacity-70">{{ formatDate(message.timestamp) }}</time>
        </article>
      </div>

      <div v-if="!messages.length" class="rounded-[1.5rem] border border-dashed border-forest/15 px-4 py-8 text-center text-sm text-forest/45">
        No WhatsApp messages yet.
      </div>
    </div>

    <form class="glass-panel space-y-4 p-4" @submit.prevent="submitMessage">
      <textarea
        v-model="draft"
        rows="4"
        class="field"
        placeholder="Write a WhatsApp reply..."
      />
      <div class="flex justify-end">
        <button class="btn-primary" :disabled="sending || !draft.trim()">
          {{ sending ? 'Sending...' : 'Send reply' }}
        </button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'

import * as waApi from '../api/wa'

const props = defineProps({
  leadId: {
    type: Number,
    required: true
  }
})

const messages = ref([])
const draft = ref('')
const sending = ref(false)

async function loadMessages() {
  const { data } = await waApi.getMessages(props.leadId)
  messages.value = data.data
}

async function submitMessage() {
  sending.value = true
  try {
    const { data } = await waApi.sendMessage({
      lead_id: props.leadId,
      message: draft.value
    })
    messages.value = [...messages.value, data.message]
    draft.value = ''
  } finally {
    sending.value = false
  }
}

function formatDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(new Date(value))
}

watch(() => props.leadId, loadMessages)
onMounted(loadMessages)
</script>
