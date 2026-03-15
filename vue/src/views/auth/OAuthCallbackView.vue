<template>
  <div class="callback-wrap">
    <div class="callback-inner">
      <template v-if="!failed">
        <div class="spinner" style="width:28px;height:28px;border-width:2px;margin:0 auto 16px;" />
        <p>Выполняется вход…</p>
      </template>
      <template v-else>
        <p class="callback-error">{{ errorMsg }}</p>
        <RouterLink to="/login" class="btn btn-primary" style="margin-top:12px;">
          Вернуться к входу
        </RouterLink>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { saveTokens } from '@/api/index.js'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const auth   = useAuthStore()

const failed   = ref(false)
const errorMsg = ref('Ошибка OAuth. Попробуйте ещё раз.')

onMounted(async () => {
  const params  = new URLSearchParams(window.location.search)
  const access  = params.get('access')
  const refresh = params.get('refresh')
  const oauthError = params.get('error')

  // Django redirected here with ?error=oauth_failed
  if (oauthError) {
    failed.value = true
    errorMsg.value = 'Провайдер вернул ошибку. Попробуйте войти снова.'
    return
  }

  if (!access || !refresh) {
    failed.value = true
    return
  }

  try {
    saveTokens(access, refresh)
    await auth.fetchMe()

    if (!auth.user) {
      // Tokens saved but /api/auth/me/ failed — likely invalid tokens
      failed.value = true
      return
    }

    router.replace('/')
  } catch {
    failed.value = true
  }
})
</script>

<style scoped>
.callback-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.callback-inner {
  text-align: center;
  color: var(--muted);
  font-size: .9rem;
}
.callback-error {
  color: var(--danger, #e53e3e);
  font-weight: 500;
}
</style>
