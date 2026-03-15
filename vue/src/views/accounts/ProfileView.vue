<template>
  <AppLayout>
    <div class="animate-fadeUp" style="max-width:560px;">
      <h2 style="font-size:1.5rem;font-weight:700;letter-spacing:-.02em;margin-bottom:24px;">Мой профиль</h2>

      <div class="card mb-4">
        <div class="flex items-center gap-4 mb-6">
          <div class="profile-ava">{{ initial }}</div>
          <div>
            <div style="font-size:1.1rem;font-weight:700;">{{ auth.user?.full_name }}</div>
            <div class="muted" style="font-size:.875rem;">{{ auth.user?.email }}</div>
            <div class="flex gap-2 mt-2">
              <span class="badge" :class="accessBadge">{{ accessLabel }}</span>
              <span class="badge badge-muted">{{ auth.user?.role }}</span>
            </div>
          </div>
        </div>

        <hr class="divider">

        <div class="info-grid">
          <div class="info-row">
            <span class="info-lbl">Отдел</span>
            <span>{{ auth.user?.department_display || '—' }}</span>
          </div>
          <div class="info-row">
            <span class="info-lbl">Должность</span>
            <span>{{ auth.user?.position || '—' }}</span>
          </div>
          <div class="info-row">
            <span class="info-lbl">Телефон</span>
            <span>{{ auth.user?.phone || '—' }}</span>
          </div>
          <div class="info-row">
            <span class="info-lbl">2FA</span>
            <span class="badge" :class="auth.user?.two_factor_enabled ? 'badge-success' : 'badge-muted'">
              {{ auth.user?.two_factor_enabled ? 'Включена' : 'Отключена' }}
            </span>
          </div>
          <div class="info-row">
            <span class="info-lbl">Дата регистрации</span>
            <span>{{ auth.user?.date_joined?.slice(0,10) }}</span>
          </div>
        </div>
      </div>

      <!-- Quick links -->
      <div class="card card-sm">
        <h6 style="font-weight:700;margin-bottom:12px;font-size:.875rem;">Безопасность</h6>
        <div class="flex gap-2 wrap">
          <a href="/accounts/password/change/" class="btn btn-ghost btn-sm">🔑 Сменить пароль</a>
          <a href="/two_factor/account/two-factor/" class="btn btn-ghost btn-sm">🛡 Настроить 2FA</a>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { useAuthStore } from '@/stores/auth.js'

const auth = useAuthStore()

const initial = computed(() =>
  auth.user?.full_name?.[0]?.toUpperCase() || '?'
)
const accessLabel = computed(() => {
  const a = auth.user?.app_access
  if (a === 'budget') return '💰 Бюджет'
  if (a === 'people') return '👥 Люди'
  if (a === 'all')    return '🔑 Все'
  return '⏳ Ожидание'
})
const accessBadge = computed(() => {
  const a = auth.user?.app_access
  return a ? 'badge-budget' : 'badge-warning'
})
</script>

<style scoped>
.profile-ava {
  width: 64px; height: 64px; border-radius: 50%;
  background: var(--budget-dim); color: var(--budget);
  font-size: 1.5rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  border: 2px solid var(--budget-dim);
}
.mt-2 { margin-top: 8px; }

.info-grid { display: flex; flex-direction: column; gap: 2px; }
.info-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; border-bottom: 1px solid var(--border);
  font-size: .875rem;
}
.info-row:last-child { border-bottom: none; }
.info-lbl { color: var(--muted); }

.wrap { flex-wrap: wrap; }
</style>
