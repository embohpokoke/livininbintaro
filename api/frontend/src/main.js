import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { registerSW } from 'virtual:pwa-register'

import App from './App.vue'
import router from './router'
import './assets/main.css'

registerSW({
  onNeedRefresh() {
    if (window.confirm('A new Livininbintaro version is available. Reload now?')) {
      window.location.reload()
    }
  },
  onOfflineReady() {
    console.info('Livininbintaro is ready to work offline.')
  }
})

createApp(App).use(createPinia()).use(router).mount('#app')
