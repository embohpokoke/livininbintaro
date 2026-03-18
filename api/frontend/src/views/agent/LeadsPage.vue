<template>
  <div class="page-shell space-y-8">
    <section class="glass-panel p-6">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.3em] text-forest/45">Pipeline</p>
          <h1 class="text-5xl text-forest">Lead Kanban</h1>
        </div>
        <div class="flex gap-3">
          <input v-model="search" class="field min-w-64" placeholder="Search leads..." @keyup.enter="load" />
          <button class="btn-primary" @click="load">Refresh</button>
        </div>
      </div>
    </section>

    <KanbanBoard :columns="columns" @status-change="moveLead" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import KanbanBoard from '../../components/KanbanBoard.vue'
import { useLeadsStore } from '../../store'

const leadsStore = useLeadsStore()
const search = ref('')

const columns = computed(() => {
  const groups = {
    inbox: [],
    active: [],
    follow_up: [],
    non_lead: [],
    closed: []
  }
  for (const lead of leadsStore.items) {
    if (groups[lead.status]) {
      groups[lead.status].push(lead)
    }
  }
  return [
    { id: 'inbox', title: 'Inbox', items: groups.inbox },
    { id: 'active', title: 'Active', items: groups.active },
    { id: 'follow_up', title: 'Follow Up', items: groups.follow_up },
    { id: 'non_lead', title: 'Non-Lead', items: groups.non_lead },
    { id: 'closed', title: 'Closed', items: groups.closed }
  ]
})

async function load() {
  await leadsStore.fetchLeads({ search: search.value || undefined, limit: 100 })
}

async function moveLead({ leadId, status }) {
  await leadsStore.updateLeadStatus(leadId, status)
}

onMounted(load)
</script>
