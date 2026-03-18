import client from './client'

export function getPublicListings(params = {}) {
  return client.get('/public/listings', { params })
}

export function searchPublicListings(params = {}) {
  return client.get('/public/listings/search', { params })
}

export function getPublicListing(id) {
  return client.get(`/public/listings/${id}`)
}

export function getDistricts() {
  return client.get('/public/districts')
}

export function getPublicStats() {
  return client.get('/public/stats')
}

export function getAgentListings(params = {}) {
  return client.get('/listings/', { params })
}

export function updateListing(id, payload) {
  return client.put(`/listings/${id}`, payload)
}
