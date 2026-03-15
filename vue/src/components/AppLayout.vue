<template>
  <div class="app-shell">

    <!-- ── Sidebar ─────────────────────────────────── -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <!-- Brand -->
      <div class="sidebar-brand">
        <img src="@/assets/logo.png" alt="Здоровый Город" class="brand-logo-img" />
        <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed" title="Свернуть">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
      </div>

      <!-- Nav links -->
      <nav class="sidebar-nav">
        <RouterLink to="/" class="nav-item" :class="{ active: route.path === '/' }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>
          </svg>
          <span>Портал</span>
        </RouterLink>

        <RouterLink
          v-if="auth.canBudget || auth.isAdmin"
          to="/budget"
          class="nav-item"
          :class="{ active: route.path.startsWith('/budget') }"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="7" width="20" height="14" rx="2"/>
            <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
            <line x1="12" y1="12" x2="12" y2="16"/><line x1="10" y1="14" x2="14" y2="14"/>
          </svg>
          <span>Бюджет</span>
        </RouterLink>

        <RouterLink
          v-if="auth.canPeople || auth.isAdmin"
          to="/people"
          class="nav-item"
          :class="{ active: route.path.startsWith('/people') }"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          <span>Люди / CRM</span>
        </RouterLink>

        <RouterLink
          v-if="auth.canPeople || auth.isAdmin"
          to="/families"
          class="nav-item"
          :class="{ active: route.path.startsWith('/families') }"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
            <polyline points="9 22 9 12 15 12 15 22"/>
          </svg>
          <span>Семьи</span>
        </RouterLink>

        <RouterLink
          v-if="auth.isAdmin"
          to="/users"
          class="nav-item"
          :class="{ active: route.path.startsWith('/users') }"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span>Пользователи</span>
        </RouterLink>

        <!-- Django Admin — plain <a> so browser navigates directly to Django -->
        <a
          v-if="auth.user?.is_superuser"
          :href="adminUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="nav-item nav-item-admin"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2"/>
          </svg>
          <span>Django Admin ↗</span>
        </a>
      </nav>

      <!-- Bottom user section -->
      <div class="sidebar-bottom">
        <RouterLink to="/profile" class="user-row">
          <div class="user-avatar">{{ userInitial }}</div>
          <div class="user-info">
            <div class="user-name">{{ auth.user?.full_name?.split(' ')[0] || 'Профиль' }}</div>
            <div class="user-email">{{ auth.user?.email }}</div>
          </div>
        </RouterLink>
        <button class="logout-btn" @click="handleLogout" title="Выйти">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
        </button>
      </div>
    </aside>

    <!-- ── Main content ─────────────────────────────── -->
    <div class="main-area">
      <!-- Flash messages -->
      <TransitionGroup name="alert-list" tag="div" class="alerts-wrap">
        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="['alert', `alert-${msg.type}`]"
        >
          <span>{{ msg.text }}</span>
          <button class="close-btn" @click="removeMessage(msg.id)">×</button>
        </div>
      </TransitionGroup>

      <slot />
    </div>

  </div>
</template>

<script setup>
import { computed, ref, provide } from 'vue'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const sidebarCollapsed = ref(false)

// Django Admin lives on the backend server — not the Vue dev server
const adminUrl = `${import.meta.env.VITE_BACKEND_URL ?? "http://127.0.0.1:8000"}/admin/`

// ── Flash messages ────────────────────────────────────
const messages = ref([])
let msgId = 0

function addMessage(text, type = 'info') {
  const id = ++msgId
  messages.value.push({ id, text, type })
  setTimeout(() => removeMessage(id), 4000)
}
function removeMessage(id) {
  messages.value = messages.value.filter(m => m.id !== id)
}
provide('addMessage', addMessage)

// ── Auth ──────────────────────────────────────────────
const userInitial = computed(() =>
  auth.user?.full_name?.[0]?.toUpperCase() || auth.user?.email?.[0]?.toUpperCase() || '?'
)

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped>
/* ── Shell ───────────────────────────────────────────── */
.app-shell {
  min-height: 100vh;
  display: flex;
  background: var(--bg);
}

/* ── Sidebar ─────────────────────────────────────────── */
.sidebar {
  width: var(--sidebar-w);
  min-height: 100vh;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  transition: width .2s ease;
  z-index: 10;
}
.sidebar.collapsed { width: 60px; }
.sidebar.collapsed .brand-logo-img { width: 32px; height: auto; }
.sidebar.collapsed .nav-item span,
.sidebar.collapsed .user-info,
.sidebar.collapsed .nav-item span,
.sidebar.collapsed .collapse-btn { display: none; }
.sidebar.collapsed .brand-logo { margin: 0 auto; }
.sidebar.collapsed .nav-item { justify-content: center; padding: 10px; }
.sidebar.collapsed .user-row { justify-content: center; padding: 12px; }
.sidebar.collapsed .logout-btn { display: none; }

/* Brand */
.sidebar-brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.brand-logo-img {
  height: 36px;
  width: auto;
  object-fit: contain;
  flex: 1;
  min-width: 0;
}
.collapse-btn {
  background: none;
  border: none;
  color: var(--muted);
  cursor: pointer;
  padding: 3px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  transition: all .15s;
  flex-shrink: 0;
}
.collapse-btn:hover { background: var(--surface-2); color: var(--text); }

/* Nav */
.sidebar-nav {
  flex: 1;
  padding: 10px 8px;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 8px 10px;
  border-radius: 7px;
  color: var(--text-2);
  text-decoration: none;
  font-size: .84rem;
  font-weight: 500;
  transition: all .12s;
  white-space: nowrap;
  overflow: hidden;
}
.nav-item svg { flex-shrink: 0; }
.nav-item:hover { background: var(--surface-2); color: var(--text); }
.nav-item-admin { color: var(--muted); border-top: 1px solid var(--border); margin-top: 4px; padding-top: 10px; }
.nav-item-admin:hover { color: var(--primary); }

.nav-item.active {
  background: var(--primary-dim);
  color: var(--primary);
  font-weight: 600;
}

/* Bottom */
.sidebar-bottom {
  border-top: 1px solid var(--border);
  padding: 10px 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.user-row {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 8px;
  border-radius: 7px;
  text-decoration: none;
  transition: background .12s;
  overflow: hidden;
  min-width: 0;
}
.user-row:hover { background: var(--surface-2); }
.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--primary-dim);
  color: var(--primary);
  font-size: .75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.user-info { min-width: 0; overflow: hidden; }
.user-name {
  font-size: .82rem;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-email {
  font-size: .72rem;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.logout-btn {
  flex-shrink: 0;
  background: none;
  border: 1px solid var(--border);
  color: var(--muted);
  border-radius: 6px;
  padding: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all .15s;
}
.logout-btn:hover { color: var(--danger); border-color: var(--danger); background: var(--red-dim); }

/* ── Main area ─────────────────────────────────────── */
.main-area {
  flex: 1;
  padding: 28px 32px;
  min-width: 0;
  max-width: 1200px;
}

/* ── Alerts ─────────────────────────────────────────── */
.alerts-wrap { margin-bottom: 16px; }
.close-btn {
  background: none;
  border: none;
  color: inherit;
  opacity: .6;
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  padding: 0 4px;
  margin-left: auto;
}
.close-btn:hover { opacity: 1; }

.alert-list-enter-active,
.alert-list-leave-active { transition: all .25s ease; }
.alert-list-enter-from { opacity: 0; transform: translateY(-6px); }
.alert-list-leave-to   { opacity: 0; transform: translateY(-6px); }

/* ── Mobile ─────────────────────────────────────────── */
@media (max-width: 768px) {
  .app-shell { flex-direction: column; }
  .sidebar {
    width: 100% !important;
    height: auto;
    min-height: unset;
    position: relative;
    flex-direction: row;
    flex-wrap: wrap;
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
  .sidebar-nav { flex-direction: row; padding: 6px 8px; }
  .sidebar-brand { border-bottom: none; padding: 10px 14px; }
  .sidebar-bottom { display: none; }
  .nav-item span { display: none; }
  .nav-item { justify-content: center; padding: 8px; }
  .main-area { padding: 16px; }
}
</style>
