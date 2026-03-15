<template>
  <div class="login-wrap">
    <div class="grid-bg" aria-hidden="true" />
    <div class="login-card animate-fadeUp">
      <div class="login-logo"><span class="logo-heart">♥</span></div>
      <h1 class="login-title">Регистрация</h1>
      <p class="login-sub">Здоровый Город — Система учёта НКО</p>

      <div v-if="success" class="alert alert-success mb-4">
        ✓ Заявка отправлена! Администратор проверит ваш аккаунт.
      </div>
      <div v-else-if="error" class="alert alert-danger mb-4">{{ error }}</div>

      <form v-if="!success" @submit.prevent="handleRegister">
        <div class="form-group">
          <label class="form-label">Полное имя *</label>
          <input v-model="form.full_name" type="text" placeholder="Иван Иванов" required />
        </div>
        <div class="form-group">
          <label class="form-label">Email *</label>
          <input v-model="form.email" type="email" placeholder="you@example.com" required />
        </div>
        <div class="form-group">
          <label class="form-label">Пароль *</label>
          <input v-model="form.password1" type="password" placeholder="Минимум 8 символов" required />
        </div>
        <div class="form-group">
          <label class="form-label">Повторите пароль *</label>
          <input v-model="form.password2" type="password" placeholder="Повторите пароль" required />
        </div>

        <button type="submit" class="btn btn-primary btn-full" :disabled="loading">
          <span v-if="loading" class="spinner" style="width:15px;height:15px;border-width:2px" />
          <span v-else>Зарегистрироваться</span>
        </button>
      </form>

      <p class="login-register">
        Уже есть аккаунт? <RouterLink to="/login">Войти</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/api/index.js'

const form = ref({ full_name: '', email: '', password1: '', password2: '' })
const loading = ref(false)
const error   = ref('')
const success = ref(false)

async function handleRegister() {
  if (form.value.password1 !== form.value.password2) {
    error.value = 'Пароли не совпадают'
    return
  }
  loading.value = true
  error.value   = ''
  try {
    await api.post('/auth/register/', form.value)
    success.value = true
  } catch (e) {
    error.value = e.data?.detail || Object.values(e.data || {})[0]?.[0] || e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 2rem; position: relative; }
.grid-bg { position: fixed; inset: 0; background-image: linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px); background-size: 44px 44px; pointer-events: none; }
.login-card { width: 100%; max-width: 420px; background: var(--surface); border: 1px solid var(--border); border-radius: 24px; padding: 2.5rem; position: relative; z-index: 1; }
.login-logo { width: 64px; height: 64px; background: rgba(239,68,68,.1); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; }
.logo-heart { font-size: 1.8rem; }
.login-title { text-align: center; font-size: 1.5rem; margin-bottom: 4px; }
.login-sub   { text-align: center; color: var(--muted); font-size: .85rem; margin-bottom: 2rem; }
.btn-full    { width: 100%; justify-content: center; padding: 11px; }
.login-register { text-align: center; font-size: .85rem; color: var(--muted); margin-top: 16px; }
.login-register a { color: var(--budget); text-decoration: none; font-weight: 600; }
</style>
