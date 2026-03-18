import { onMounted, onUnmounted, ref } from 'vue'

import { flushOfflineQueue } from '../api/client'

const isOnline = ref(typeof navigator === 'undefined' ? true : navigator.onLine)
const showOfflineBanner = ref(false)

function updateStatus() {
  isOnline.value = navigator.onLine
  showOfflineBanner.value = true
  if (isOnline.value) {
    flushOfflineQueue()
    window.setTimeout(() => {
      showOfflineBanner.value = false
    }, 3000)
  }
}

export function useOffline() {
  onMounted(() => {
    window.addEventListener('online', updateStatus)
    window.addEventListener('offline', updateStatus)
  })

  onUnmounted(() => {
    window.removeEventListener('online', updateStatus)
    window.removeEventListener('offline', updateStatus)
  })

  return {
    isOnline,
    showOfflineBanner
  }
}
