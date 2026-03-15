import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, saveTokens, clearTokens } from '@/api/index.js'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!user.value)
  const canBudget = computed(() =>
  user.value?.is_superuser || ['budget','all'].includes(user.value?.app_access)
  )
  const canPeople = computed(() =>
  user.value?.is_superuser || ['people','all'].includes(user.value?.app_access)
  )
  const isAdmin  = computed(() => user.value?.is_superuser || user.value?.role === 'admin')
  const canEdit  = computed(() => user.value?.is_superuser || ['admin','editor'].includes(user.value?.role))

  async function fetchMe() {
    if (!localStorage.getItem('access')) return
      try {
        loading.value = true
        user.value = await authApi.me()
      } catch {
        user.value = null
      } finally {
        loading.value = false
      }
  }

  async function login(email, password) {
    const data = await authApi.login({ email, password })
    // Django возвращает { access, refresh }
    saveTokens(data.access, data.refresh)
    user.value = await authApi.me()
  }

  async function logout() {
    try {
      await authApi.logout({ refresh: localStorage.getItem('refresh') })
    } catch {}
    clearTokens()
    user.value = null
  }

  return { user, loading, isAuthenticated, canBudget, canPeople, isAdmin, canEdit, fetchMe, login, logout }
})
