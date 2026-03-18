const KEY = 'livinin-offline-queue'

export function loadQueue() {
  const raw = localStorage.getItem(KEY)
  return raw ? JSON.parse(raw) : []
}

export function enqueueRequest(item) {
  const queue = loadQueue()
  queue.push({ ...item, queuedAt: new Date().toISOString() })
  localStorage.setItem(KEY, JSON.stringify(queue))
}

export function dequeueAll() {
  const queue = loadQueue()
  localStorage.removeItem(KEY)
  return queue
}
