<template>
  <div class="page-shell space-y-8">
    <section class="glass-panel p-8">
      <p class="text-sm uppercase tracking-[0.35em] text-forest/50">Agent dashboard</p>
      <div class="mt-4 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 class="text-5xl text-forest">Field-ready overview</h1>
          <p class="mt-3 max-w-2xl text-base leading-8 text-forest/70">
            Live pipeline, listing inventory, unread conversations, and the tasks that need action today.
          </p>
        </div>
        <RouterLink class="btn-primary" to="/leads">Open Leads Pipeline</RouterLink>
      </div>
    </section>

    <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <article class="metric-card">
        <p class="text-xs uppercase tracking-[0.3em] text-forest/45">Listings</p>
        <p class="mt-4 text-4xl text-forest">{{ dashboard.summary?.active_listings ?? '...' }}</p>
      </article>
      <article class="metric-card">
        <p class="text-xs uppercase tracking-[0.3em] text-forest/45">Leads</p>
        <p class="mt-4 text-4xl text-forest">{{ dashboard.summary?.total_leads ?? '...' }}</p>
      </article>
      <article class="metric-card">
        <p class="text-xs uppercase tracking-[0.3em] text-forest/45">Hot listings</p>
        <p class="mt-4 text-4xl text-forest">{{ dashboard.summary?.hot_listings ?? '...' }}</p>
      </article>
      <article class="metric-card bg-forest text-white">
        <p class="text-xs uppercase tracking-[0.3em] text-white/60">Unread WA</p>
        <p class="mt-4 text-4xl">{{ dashboard.summary?.unread_messages ?? '...' }}</p>
      </article>
    </section>

    <section class="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <div class="glass-panel p-6">
        <div class="flex items-end justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-[0.3em] text-forest/45">Pipeline</p>
            <h2 class="text-3xl text-forest">Lead buckets</h2>
          </div>
          <RouterLink class="btn-secondary" to="/leads">Manage</RouterLink>
        </div>
        <div class="mt-6 grid gap-3 sm:grid-cols-2">
          <article v-for="bucket in bucketCards" :key="bucket.id" class="rounded-[1.5rem] border border-forest/10 bg-white p-4">
            <p class="text-xs uppercase tracking-[0.25em] text-forest/45">{{ bucket.id }}</p>
            <p class="mt-3 text-3xl text-forest">{{ bucket.count }}</p>
          </article>
        </div>
      </div>

      <div class="glass-panel p-6">
        <div class="flex items-end justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-[0.3em] text-forest/45">Today</p>
            <h2 class="text-3xl text-forest">Follow-up queue</h2>
          </div>
        </div>
        <div class="mt-6 space-y-4">
          <RouterLink
            v-for="lead in dashboard.todayTasks"
            :key="lead.id"
            :to="`/leads/${lead.id}`"
            class="block rounded-[1.5rem] border border-forest/10 bg-white p-4"
          >
            <p class="text-xs uppercase tracking-[0.25em] text-forest/45">{{ lead.status }}</p>
            <h3 class="mt-2 text-xl text-forest">{{ lead.name }}</h3>
            <p class="mt-1 text-sm text-forest/65">{{ lead.follow_up_reason || lead.phone || 'Action required' }}</p>
          </RouterLink>
          <p v-if="!dashboard.todayTasks.length" class="rounded-[1.5rem] border border-dashed border-forest/15 px-4 py-8 text-center text-sm text-forest/45">
            No follow-up task due right now.
          </p>
        </div>
      </div>
    </section>

    <section class="glass-panel p-6">
      <p class="text-xs uppercase tracking-[0.3em] text-forest/45">Recent activity</p>
      <h2 class="mt-2 text-3xl text-forest">Latest CRM movement</h2>
      <Timeline class="mt-6" :items="timelineItems" />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import Timeline from '../../components/Timeline.vue'
import { useDashboardStore } from '../../store'

const dashboard = useDashboardStore()

const bucketCards = computed(() =>
  Object.entries(dashboard.pipeline || {}).map(([id, count]) => ({ id, count }))
)

const timelineItems = computed(() =>
  (dashboard.recentActivity || []).map((item) => ({
    ...item,
    type: item.activity_type
  }))
)

onMounted(() => {
  dashboard.fetchStats()
})
</script>
