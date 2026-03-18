<template>
  <div class="page-shell space-y-8" v-if="lead">
    <section class="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <div class="glass-panel p-6">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-[0.3em] text-forest/45">{{ lead.status }}</p>
            <h1 class="mt-3 text-4xl text-forest">{{ lead.name }}</h1>
            <p class="mt-2 text-sm text-forest/65">{{ lead.phone || 'No phone' }} · {{ lead.email || 'No email' }}</p>
          </div>
          <AIScoreBadge :score="lead.ai_score" :reason="lead.ai_reasoning" />
        </div>

        <div class="mt-6 grid gap-3 sm:grid-cols-2">
          <article class="rounded-[1.5rem] border border-forest/10 bg-white p-4">
            <p class="text-xs uppercase tracking-[0.25em] text-forest/45">Preferred area</p>
            <p class="mt-3 text-xl text-forest">{{ lead.preferred_area || 'Unknown' }}</p>
          </article>
          <article class="rounded-[1.5rem] border border-forest/10 bg-white p-4">
            <p class="text-xs uppercase tracking-[0.25em] text-forest/45">Budget</p>
            <p class="mt-3 text-xl text-forest">{{ budgetLabel }}</p>
          </article>
        </div>

        <div class="mt-6 space-y-3">
          <button class="btn-secondary w-full" @click="scoreLead">Refresh AI score</button>
          <button class="btn-secondary w-full" @click="generateSummary">Generate AI summary</button>
        </div>
      </div>

      <div class="glass-panel p-6">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="tabItem in tabs"
            :key="tabItem"
            class="rounded-full px-4 py-2 text-sm font-semibold"
            :class="tab === tabItem ? 'bg-forest text-white' : 'bg-white text-forest'"
            @click="tab = tabItem"
          >
            {{ tabItem }}
          </button>
        </div>

        <div class="mt-6">
          <WAConversation v-if="tab === 'WhatsApp'" :lead-id="lead.id" />
          <Timeline v-else-if="tab === 'Notes'" :items="notes" />
          <Timeline v-else-if="tab === 'Activities'" :items="activities" />
          <div v-else class="space-y-4">
            <article class="rounded-[1.5rem] border border-forest/10 bg-white p-4">
              <p class="text-xs uppercase tracking-[0.25em] text-forest/45">AI summary</p>
              <p class="mt-3 whitespace-pre-line text-sm leading-8 text-forest/75">
                {{ lead.ai_summary || 'No AI summary generated yet.' }}
              </p>
            </article>
            <article class="rounded-[1.5rem] border border-forest/10 bg-white p-4">
              <p class="text-xs uppercase tracking-[0.25em] text-forest/45">Suggested properties</p>
              <div class="mt-4 space-y-3">
                <div v-for="property in lead.interested_properties" :key="property.id" class="rounded-2xl border border-forest/10 px-4 py-3">
                  <p class="font-semibold text-forest">{{ property.property_name }}</p>
                  <p class="text-sm text-forest/60">{{ property.district }} · {{ property.price ? formatCurrency(property.price) : 'On request' }}</p>
                </div>
                <p v-if="!lead.interested_properties?.length" class="text-sm text-forest/50">No suggested properties yet.</p>
              </div>
            </article>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import * as leadsApi from '../../api/leads'
import AIScoreBadge from '../../components/AIScoreBadge.vue'
import Timeline from '../../components/Timeline.vue'
import WAConversation from '../../components/WAConversation.vue'
import { useLeadsStore } from '../../store'

const route = useRoute()
const leadsStore = useLeadsStore()
const tab = ref('WhatsApp')
const tabs = ['WhatsApp', 'Notes', 'Activities', 'AI']

const lead = computed(() => leadsStore.currentLead)
const notes = computed(() => (lead.value?.notes_list || []).map((item) => ({ ...item, type: 'note' })))
const activities = computed(() => (lead.value?.activities || []).map((item) => ({ ...item, type: item.activity_type })))
const budgetLabel = computed(() => {
  if (!lead.value) return '-'
  if (lead.value.budget_min || lead.value.budget_max) {
    return `${lead.value.budget_min || 0} - ${lead.value.budget_max || 0}`
  }
  return 'Not specified'
})

async function load() {
  await leadsStore.fetchLead(route.params.id)
}

async function scoreLead() {
  await leadsApi.scoreLead(route.params.id)
  await load()
}

async function generateSummary() {
  await leadsApi.generateSummary(route.params.id)
  await load()
}

function formatCurrency(value) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0
  }).format(value)
}

onMounted(load)
</script>
