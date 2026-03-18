<template>
  <footer class="border-t border-forest/10 py-10">
    <div class="page-shell flex flex-col gap-4 text-sm text-forest/70 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="font-display text-lg text-forest">Livininbintaro</p>
        <p>Unified property marketplace, CRM dashboard, and WhatsApp ops.</p>
      </div>
      <div class="flex gap-4">
        <RouterLink to="/search">Search</RouterLink>
        <RouterLink to="/dashboard">Dashboard</RouterLink>
        <a href="https://livininbintaro.my.id" target="_blank" rel="noreferrer">Production</a>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>
