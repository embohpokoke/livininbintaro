import axios from 'axios'

import { dequeueAll, enqueueRequest } from '../utils/offline'
import { clearStoredAuth, getStoredToken } from '../utils/auth'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000
})

client.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!error.response && error.config?.method && error.config.method !== 'get') {
      enqueueRequest({
        method: error.config.method,
        url: error.config.url,
        data: error.config.data ? JSON.parse(error.config.data) : null
      })
    }

    if (error.response?.status === 401) {
      clearStoredAuth()
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
        window.location.assign('/login')
      }
    }

    return Promise.reject(error)
  }
)

export async function flushOfflineQueue() {
  const requests = dequeueAll()
  for (const request of requests) {
    try {
      await client({
        method: request.method,
        url: request.url,
        data: request.data
      })
    } catch (error) {
      enqueueRequest(request)
      break
    }
  }
}

export default client
