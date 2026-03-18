import client from './client'

export function getLeads(params = {}) {
  return client.get('/leads/', { params })
}

export function getLead(id) {
  return client.get(`/leads/${id}`)
}

export function createLead(payload) {
  return client.post('/leads/', payload)
}

export function updateLead(id, payload) {
  return client.put(`/leads/${id}`, payload)
}

export function scoreLead(id) {
  return client.post(`/leads/${id}/score`, {})
}

export function getTimeline(id) {
  return client.get(`/leads/${id}/timeline`)
}

export function addNote(id, payload) {
  return client.post(`/leads/${id}/notes`, payload)
}

export function generateSummary(id) {
  return client.post(`/leads/${id}/ai-summary`, {})
}

export function getRecommendations(id) {
  return client.post(`/leads/${id}/ai-recommend`, {})
}
