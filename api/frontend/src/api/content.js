import client from './client'

export function getContent(params = {}) {
  return client.get('/content/', { params })
}

export function createContent(payload) {
  return client.post('/content/', payload)
}

export function updateContent(id, payload) {
  return client.put(`/content/${id}`, payload)
}
