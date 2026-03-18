<template>
  <div class="page-shell grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
    <section class="glass-panel p-6">
      <p class="text-xs uppercase tracking-[0.3em] text-forest/45">Planner</p>
      <h1 class="mt-2 text-4xl text-forest">Content calendar</h1>
      <form class="mt-6 space-y-4" @submit.prevent="submit">
        <select v-model="draft.post_type" class="field">
          <option value="listing">Listing</option>
          <option value="promo">Promo</option>
          <option value="tips">Tips</option>
        </select>
        <input v-model="draft.scheduled_date" type="date" class="field" />
        <textarea v-model="draft.content" rows="6" class="field" placeholder="Draft caption or content brief..." />
        <button class="btn-primary w-full">Add item</button>
      </form>
    </section>

    <section class="glass-panel p-6">
      <p class="text-xs uppercase tracking-[0.3em] text-forest/45">Scheduled items</p>
      <div class="mt-6 space-y-4">
        <article v-for="item in items" :key="item.id" class="rounded-[1.5rem] border border-forest/10 bg-white p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs uppercase tracking-[0.25em] text-forest/45">{{ item.post_type }}</p>
              <p class="mt-3 whitespace-pre-line text-sm leading-7 text-forest/75">{{ item.content }}</p>
            </div>
            <div class="text-right text-sm text-forest/55">
              <p>{{ item.scheduled_date || 'Unscheduled' }}</p>
              <p class="mt-1">{{ item.status }}</p>
            </div>
          </div>
        </article>
        <p v-if="!items.length" class="rounded-[1.5rem] border border-dashed border-forest/15 px-4 py-8 text-center text-sm text-forest/45">
          No content planned yet.
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import * as contentApi from '../../api/content'

const items = ref([])
const draft = reactive({
  post_type: 'listing',
  content: '',
  scheduled_date: ''
})

async function load() {
  const { data } = await contentApi.getContent()
  items.value = data.data
}

async function submit() {
  await contentApi.createContent({ ...draft })
  draft.content = ''
  draft.scheduled_date = ''
  await load()
}

onMounted(load)
</script>
