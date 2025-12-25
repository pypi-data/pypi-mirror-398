<script setup>
import DefaultTheme from 'vitepress/theme'
import { ref, onMounted } from 'vue'
import { useRoute } from 'vitepress'

const { Layout } = DefaultTheme
const route = useRoute()
const isLoading = ref(true)
const isHome = ref(false)

onMounted(() => {
  // Check if we're on the home page
  isHome.value = route.path === '/' || route.path === '/index.html'
  
  if (isHome.value) {
    // Preload hero image
    const heroImage = new Image()
    heroImage.src = '/hero.png'
    
    const hideLoading = () => {
      isLoading.value = false
    }
    
    heroImage.onload = hideLoading
    heroImage.onerror = hideLoading
    
    // If already cached
    if (heroImage.complete) {
      hideLoading()
    }
    
    // Fallback: max 2 seconds
    setTimeout(hideLoading, 2000)
  } else {
    // Not home page, no loading screen needed
    isLoading.value = false
  }
})
</script>

<template>
  <!-- Loading Screen (only on home page) -->
  <Transition name="fade">
    <div v-if="isLoading && isHome" class="loading-screen">
      <img src="/logo.svg" alt="ACTO" class="loading-logo" />
      <div class="loading-spinner"></div>
      <div class="loading-text">Loading...</div>
    </div>
  </Transition>
  
  <!-- Main Layout -->
  <Layout>
    <template #layout-top>
      <!-- Can add custom components here -->
    </template>
  </Layout>
</template>

<style>
/* Loading Screen Styles */
.loading-screen {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.loading-logo {
  width: 80px;
  height: auto;
  margin-bottom: 24px;
  animation: pulse 2s ease-in-out infinite;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #4b5563;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-text {
  margin-top: 16px;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  color: #6b7280;
  letter-spacing: 0.5px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(0.98); }
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

