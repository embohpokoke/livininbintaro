import client from './client'

export function getMessages(leadId, params = {}) {
  return client.get(`/wa/messages/${leadId}`, { params })
}

export function sendMessage(payload) {
  return client.post('/wa/send', payload)
}
