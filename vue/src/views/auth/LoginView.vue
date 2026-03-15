<template>
  <div class="login-wrap">
    <div class="login-left">
      <div class="login-left-content">
        <div class="login-logo">
          <img src="@/assets/logo.png" alt="Здоровый Город" style="height:56px;width:auto;object-fit:contain;" />
        </div>
        <p class="login-sub">Войдите в систему учёта НКО</p>

        <!-- Error -->
        <div v-if="error" class="alert alert-danger">{{ error }}</div>

        <!-- Form -->
        <form @submit.prevent="handleLogin" novalidate class="login-form">
          <div class="form-group">
            <label class="form-label" for="email">Email</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              placeholder="you@example.com"
              autocomplete="email"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label" for="password">Пароль</label>
            <div class="pw-wrap">
              <input
                id="password"
                v-model="form.password"
                :type="showPw ? 'text' : 'password'"
                placeholder="••••••••"
                autocomplete="current-password"
                required
              />
              <button type="button" class="pw-toggle" @click="showPw = !showPw">
                <svg v-if="!showPw" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
                <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                  <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              </button>
            </div>
          </div>

          <button type="submit" class="btn btn-primary btn-submit" :disabled="loading">
            <span v-if="loading" class="spinner" style="width:14px;height:14px;border-width:2px;border-color:rgba(255,255,255,.3);border-top-color:#fff" />
            <span v-else>Войти</span>
          </button>
        </form>

        <!-- Divider -->
        <div class="login-divider"><span>или войти через</span></div>

        <!-- Social OAuth buttons — these are plain <a> tags (not RouterLink)
             so the browser does a full navigation directly to Django.
             Vue Router must NOT intercept these clicks. -->
        <div class="social-row">
          <a :href="googleLoginUrl" class="btn btn-ghost btn-social">
            <svg width="16" height="16" viewBox="0 0 48 48">
              <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9 3.2l6.7-6.7C35.8 2.5 30.3 0 24 0 14.6 0 6.6 5.4 2.6 13.3l7.8 6C12.3 13.2 17.7 9.5 24 9.5z"/>
              <path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v8.5h12.7c-.6 3-2.3 5.5-4.8 7.2l7.5 5.8c4.4-4.1 7.1-10.1 7.1-17z"/>
              <path fill="#FBBC05" d="M10.4 28.7A14.5 14.5 0 0 1 9.5 24c0-1.6.3-3.2.9-4.7l-7.8-6A23.9 23.9 0 0 0 0 24c0 3.9.9 7.5 2.6 10.7l7.8-6z"/>
              <path fill="#34A853" d="M24 48c6.3 0 11.6-2.1 15.4-5.7l-7.5-5.8c-2.1 1.4-4.8 2.2-7.9 2.2-6.3 0-11.7-3.7-13.6-9.1l-7.8 6C6.6 42.6 14.6 48 24 48z"/>
            </svg>
            Google
          </a>
          <a :href="githubLoginUrl" class="btn btn-ghost btn-social">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.2 11.38.6.11.82-.26.82-.58v-2.23c-3.34.72-4.04-1.41-4.04-1.41-.55-1.39-1.34-1.76-1.34-1.76-1.09-.75.08-.73.08-.73 1.21.08 1.85 1.24 1.85 1.24 1.07 1.84 2.81 1.31 3.49 1 .11-.78.42-1.31.76-1.61-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.12-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 3-.4c1.02 0 2.04.14 3 .4 2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.24 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.63-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.21.7.82.58C20.56 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            GitHub
          </a>
        </div>

        <p class="register-link">
          Нет аккаунта?
          <RouterLink to="/register">Зарегистрироваться</RouterLink>
        </p>

        <div class="security-note mono">
          🔒 Argon2 · 2FA · Brute-force lock
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const auth = useAuthStore()
const router = useRouter()

// VITE_BACKEND_URL is set in .env.development / .env.production.
// It points directly at the Django server so the browser performs a real
// full-page navigation — bypassing Vue Router entirely.
// Dev:  http://127.0.0.1:8000
// Prod: https://api.zdravy-gorod.md
const BACKEND = import.meta.env.VITE_BACKEND_URL ?? 'http://127.0.0.1:8000'
const googleLoginUrl = `${BACKEND}/oauth/google/login/?process=login`
const githubLoginUrl = `${BACKEND}/oauth/github/login/?process=login`

const form = ref({ email: '', password: '' })
const loading = ref(false)
const error = ref('')
const showPw = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(form.value.email, form.value.password)
    const next = new URLSearchParams(location.search).get('next') || '/'
    router.push(next)
  } catch (e) {
    error.value = e.data?.non_field_errors?.[0] || e.message || 'Ошибка входа'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  min-height: 100vh;
  display: flex;
}

/* ── Left panel ─────────────────────────────────────── */
.login-left {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  background: var(--surface);
}
.login-left-content {
  width: 100%;
  max-width: 380px;
  animation: fadeUp .3s ease both;
}

.login-logo {
  margin-bottom: 20px;
}

.login-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 4px;
}
.login-sub {
  color: var(--muted);
  font-size: .875rem;
  margin-bottom: 28px;
}

.login-form { margin-bottom: 20px; }

.btn-submit {
  width: 100%;
  justify-content: center;
  padding: 9px;
  margin-top: 4px;
  font-size: .9rem;
}

.pw-wrap { position: relative; }
.pw-wrap input { padding-right: 38px; }
.pw-toggle {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--muted);
  display: flex;
  align-items: center;
  padding: 0;
  transition: color .15s;
}
.pw-toggle:hover { color: var(--text); }

/* Divider */
.login-divider {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--muted);
  font-size: .78rem;
  margin: 18px 0;
}
.login-divider::before,
.login-divider::after { content: ''; flex: 1; border-top: 1px solid var(--border); }

/* Social */
.social-row { display: flex; gap: 8px; margin-bottom: 18px; }
.btn-social { flex: 1; justify-content: center; gap: 7px; font-size: .84rem; }

.register-link {
  text-align: center;
  font-size: .84rem;
  color: var(--muted);
  margin-bottom: 20px;
}
.register-link a {
  color: var(--primary);
  text-decoration: none;
  font-weight: 500;
}
.register-link a:hover { text-decoration: underline; }

.security-note {
  text-align: center;
  font-size: .68rem;
  color: var(--muted);
  padding: 8px;
  background: var(--surface-2);
  border-radius: 7px;
}

/* ── Responsive ─────────────────────────────────────── */
@media (max-width: 768px) {
  .login-right { display: none; }
}
</style>
