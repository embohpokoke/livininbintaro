import { defineStore } from 'pinia'

import client from './api/client'
import * as dashboardApi from './api/dashboard'
import * as leadsApi from './api/leads'
import * as listingsApi from './api/listings'
import {
  clearStoredAuth,
  getStoredAuth,
  setStoredAuth
} from './utils/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    hydrated: false
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token)
  },
  actions: {
    hydrate() {
      if (this.hydrated) return
      const stored = getStoredAuth()
      this.user = stored.user
      this.token = stored.token
      this.hydrated = true
    },
    async loginWithPassword(credentials) {
      const payload = {
        password: credentials.password
      }
      if (credentials.identifier.includes('@')) {
        payload.email = credentials.identifier
      } else {
        payload.username = credentials.identifier
      }

      const { data } = await client.post('/auth/login', payload)
      this.user = data.user
      this.token = data.token
      this.hydrated = true
      setStoredAuth(data)
      return data
    },
    logout() {
      this.user = null
      this.token = null
      this.hydrated = true
      clearStoredAuth()
    }
  }
})

export const useListingsStore = defineStore('listings', {
  state: () => ({
    items: [],
    page: 1,
    totalPages: 1,
    total: 0,
    loading: false
  }),
  actions: {
    async fetchPublic(params = {}) {
      this.loading = true
      try {
        const { data } = await listingsApi.getPublicListings(params)
        this.items = data.data
        this.page = data.page
        this.totalPages = data.total_pages
        this.total = data.total
      } finally {
        this.loading = false
      }
    }
  }
})

export const useLeadsStore = defineStore('leads', {
  state: () => ({
    items: [],
    currentLead: null,
    total: 0,
    loading: false
  }),
  actions: {
    async fetchLeads(params = {}) {
      this.loading = true
      try {
        const { data } = await leadsApi.getLeads(params)
        this.items = data.data
        this.total = data.total
      } finally {
        this.loading = false
      }
    },
    async fetchLead(id) {
      const { data } = await leadsApi.getLead(id)
      this.currentLead = data
      return data
    },
    async updateLeadStatus(id, status) {
      await leadsApi.updateLead(id, { status })
      const lead = this.items.find((item) => item.id === id)
      if (lead) {
        lead.status = status
      }
      if (this.currentLead?.id === id) {
        this.currentLead.status = status
      }
    }
  }
})

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    summary: null,
    pipeline: {},
    todayTasks: [],
    recentActivity: []
  }),
  actions: {
    async fetchStats() {
      const { data } = await dashboardApi.getStats()
      this.summary = data.summary
      this.pipeline = data.pipeline
      this.todayTasks = data.today_tasks
      this.recentActivity = data.recent_activity
    }
  }
})
