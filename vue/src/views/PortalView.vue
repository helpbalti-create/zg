<template>
  <div class="portal-wrap">

    <!-- Grid background -->
    <div class="grid-bg" aria-hidden="true" />

    <header class="portal-header animate-fadeUp">
      <p class="portal-eyebrow mono">ЗДОРОВЫЙ ГОРОД · ПОРТАЛ</p>
      <h1 class="portal-title">Добро пожаловать</h1>
      <p class="portal-greeting">
        Привет, <strong>{{ auth.user?.full_name?.split(' ')[0] }}</strong> — выберите раздел
      </p>
    </header>

    <!-- App cards -->
    <div class="apps-grid animate-fadeUp stagger-2">

      <RouterLink
        v-if="auth.canBudget || auth.isAdmin"
        to="/budget"
        class="app-card budget"
      >
        <div class="card-glow" />
        <div class="card-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="7" width="20" height="14" rx="2"/>
            <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
            <line x1="12" y1="12" x2="12" y2="16"/>
            <line x1="10" y1="14" x2="14" y2="14"/>
          </svg>
        </div>
        <div class="card-title">Бюджет</div>
        <p class="card-desc">Учёт грантов, смета, расходы, экспорт в Excel</p>
        <span class="card-arrow">→</span>
      </RouterLink>

      <RouterLink
        v-if="auth.canPeople || auth.isAdmin"
        to="/people"
        class="app-card people"
      >
        <div class="card-glow" />
        <div class="card-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
        </div>
        <div class="card-title">CRM — Люди</div>
        <p class="card-desc">База людей, семьи, связи, динамические поля</p>
        <span class="card-arrow">→</span>
      </RouterLink>

      <RouterLink
        v-if="!auth.canBudget && !auth.canPeople && !auth.isAdmin"
        to="/profile"
        class="app-card pending"
      >
        <div class="card-icon">⏳</div>
        <div class="card-title">Ожидание одобрения</div>
        <p class="card-desc">Администратор ещё не назначил вам доступ к приложениям</p>
        <span class="card-arrow">→</span>
      </RouterLink>
    </div>

    <!-- Footer links -->
    <footer class="portal-footer animate-fadeUp stagger-4">
      <RouterLink v-if="auth.isAdmin" to="/users" class="footer-link">⚙ Пользователи</RouterLink>
      <a v-if="auth.isAdmin" :href="`${backendUrl}/admin/`" target="_blank" rel="noopener noreferrer" class="footer-link">Администрирование Django</a>
      <RouterLink to="/profile" class="footer-link">Профиль</RouterLink>
      <button class="footer-link" @click="handleLogout">Выйти</button>
    </footer>

  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth.js'
import { useRouter, RouterLink } from 'vue-router'

const auth = useAuthStore()
const backendUrl = import.meta.env.VITE_BACKEND_URL ?? "http://127.0.0.1:8000"
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.portal-wrap {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  position: relative;
  overflow: hidden;
}

.grid-bg {
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
  background-size: 44px 44px;
  pointer-events: none;
  z-index: 0;
}

/* Header */
.portal-header {
  text-align: center;
  margin-bottom: 3.5rem;
  position: relative;
  z-index: 1;
}
.portal-eyebrow {
  font-size: .7rem;
  letter-spacing: .25em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: .75rem;
}
.portal-title {
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 700;
  letter-spacing: -.04em;
  line-height: 1.05;
  margin-bottom: .5rem;
}
.portal-greeting {
  color: var(--muted);
  font-size: .95rem;
}
.portal-greeting strong { color: var(--text); }

/* Apps grid */
.apps-grid {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.app-card {
  position: relative;
  width: 290px;
  padding: 2rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  text-decoration: none;
  color: inherit;
  overflow: hidden;
  transition: transform .22s, border-color .22s, box-shadow .22s;
}
.app-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 24px 50px rgba(0,0,0,.5);
}
.app-card.budget:hover { border-color: var(--budget); }
.app-card.people:hover { border-color: var(--people); }
.app-card.pending      { cursor: default; opacity: .7; }

.card-glow {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity .25s;
  pointer-events: none;
}
.budget .card-glow { background: radial-gradient(circle at 30% 20%, var(--budget-glow), transparent 65%); }
.people .card-glow { background: radial-gradient(circle at 30% 20%, var(--people-glow), transparent 65%); }
.app-card:hover .card-glow { opacity: 1; }

.card-icon {
  margin-bottom: 1.25rem;
  color: var(--muted);
  transition: color .2s;
}
.budget:hover .card-icon { color: var(--budget); }
.people:hover .card-icon { color: var(--people); }

.card-title {
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: -.02em;
  margin-bottom: .5rem;
}

.card-desc {
  font-size: .875rem;
  color: var(--muted);
  line-height: 1.6;
  margin-bottom: 2.5rem;
}

.card-arrow {
  position: absolute;
  bottom: 1.5rem;
  right: 1.5rem;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1px solid var(--border-2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: .9rem;
  transition: all .2s;
}
.budget .card-arrow { color: var(--budget); }
.people .card-arrow { color: var(--people); }
.app-card:hover .card-arrow { background: var(--border); }

/* Footer */
.portal-footer {
  margin-top: 3.5rem;
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  justify-content: center;
  position: relative;
  z-index: 1;
}
.footer-link {
  color: var(--muted);
  font-size: .78rem;
  font-family: 'JetBrains Mono', monospace;
  text-decoration: none;
  background: none;
  border: none;
  cursor: pointer;
  transition: color .15s;
}
.footer-link:hover { color: var(--text); }
</style>
