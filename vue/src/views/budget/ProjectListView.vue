<template>
  <AppLayout>
    <div class="animate-fadeUp">

      <!-- Page header -->
      <div class="page-header mb-6">
        <div>
          <h2 class="page-title">Бюджетные проекты</h2>
          <p class="muted" style="font-size:.875rem;margin-top:4px;">Мониторинг финансов по грантам организации</p>
        </div>
        <div class="flex gap-2" v-if="auth.canEdit">
          <RouterLink to="/budget/new" class="btn btn-primary">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Новый проект
          </RouterLink>
          <a href="/api/budget/import/" class="btn btn-ghost">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/><polyline points="3 7 3 17"/></svg>
            Импорт Excel
          </a>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="empty-state">
        <div class="spinner" style="width:32px;height:32px;border-width:3px;margin:0 auto;" />
        <p class="mt-3 muted">Загрузка проектов…</p>
      </div>

      <template v-else>

        <!-- Active projects -->
        <template v-if="active.length">
          <div class="section-label mb-4">
            <span class="dot-success" />
            Активные проекты
          </div>
          <div class="projects-grid mb-6">
            <RouterLink
              v-for="p in active"
              :key="p.id"
              :to="`/budget/${p.id}`"
              class="project-card animate-fadeUp"
            >
              <div class="card-stripe" style="background:linear-gradient(90deg,#22c55e,#10b981)" />
              <div class="card-body">
                <div class="flex justify-between items-center mb-2">
                  <div>
                    <div class="card-name">{{ p.name }}</div>
                    <div class="card-code muted mono" v-if="p.project_code">{{ p.project_code }}</div>
                  </div>
                  <span class="badge badge-success">Активный</span>
                </div>
                <div class="muted" style="font-size:.8rem;margin-bottom:12px;" v-if="p.donor">
                  🏢 {{ p.donor }}
                </div>

                <!-- Stats row -->
                <div class="stats-row mb-3">
                  <div class="stat-cell">
                    <div class="stat-val">${{ fmt(p.total_budget) }}</div>
                    <div class="stat-lbl">Бюджет</div>
                  </div>
                  <div class="stat-cell">
                    <div class="stat-val" :class="pctClass(p.spent_percent)">${{ fmt(p.total_spent) }}</div>
                    <div class="stat-lbl">Потрачено</div>
                  </div>
                  <div class="stat-cell">
                    <div class="stat-val" :class="p.total_remaining < 0 ? 'danger' : 'text-success'">${{ fmt(p.total_remaining) }}</div>
                    <div class="stat-lbl">Остаток</div>
                  </div>
                </div>

                <!-- Progress -->
                <div class="flex justify-between mb-1" style="font-size:.72rem;color:var(--muted);">
                  <span>Исполнение</span>
                  <span class="badge" :class="pctBadge(p.spent_percent)">{{ p.spent_percent }}%</span>
                </div>
                <div class="progress mb-3">
                  <div class="progress-bar" :class="pctBar(p.spent_percent)" :style="`width:${Math.min(p.spent_percent,100)}%`" />
                </div>

                <div class="muted" style="font-size:.76rem;">
                  📅 {{ p.start_date }} — {{ p.end_date }}
                  <span class="badge badge-muted ms" style="margin-left:6px;">{{ p.duration_months }} мес.</span>
                </div>
              </div>
            </RouterLink>
          </div>
        </template>

        <!-- Completed projects -->
        <template v-if="completed.length">
          <div class="section-label mb-3">
            <span class="dot-muted" />
            Завершённые проекты
          </div>
          <div class="table-wrap mb-6">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Проект</th>
                  <th>Период</th>
                  <th class="num">Бюджет</th>
                  <th class="num">Потрачено</th>
                  <th>Исполнение</th>
                  <th>Завершён</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in completed" :key="p.id">
                  <td>
                    <div style="font-weight:600;">{{ p.name }}</div>
                    <div class="muted" style="font-size:.76rem;">{{ p.project_code }} — {{ p.donor }}</div>
                  </td>
                  <td class="muted" style="font-size:.78rem;">{{ p.start_date }}<br>{{ p.end_date }}</td>
                  <td class="num" style="font-weight:600;">${{ fmt(p.total_budget) }}</td>
                  <td class="num">${{ fmt(p.total_spent) }}</td>
                  <td style="min-width:110px;">
                    <div class="flex items-center gap-2">
                      <div class="progress grow"><div class="progress-bar ok" :style="`width:${p.spent_percent}%`" /></div>
                      <span class="muted" style="font-size:.75rem;min-width:34px;">{{ p.spent_percent }}%</span>
                    </div>
                  </td>
                  <td class="muted" style="font-size:.8rem;">{{ p.completed_at?.slice(0,10) || '—' }}</td>
                  <td>
                    <RouterLink :to="`/budget/${p.id}`" class="btn btn-ghost btn-sm">Открыть</RouterLink>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <!-- Empty -->
        <div v-if="!active.length && !completed.length" class="card empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            <line x1="12" y1="11" x2="12" y2="17"/><line x1="9" y1="14" x2="15" y2="14"/>
          </svg>
          <h4 style="margin-top:12px;">Проектов пока нет</h4>
          <p>Создайте первый бюджетный проект</p>
          <RouterLink v-if="auth.canEdit" to="/budget/new" class="btn btn-primary" style="margin-top:16px;">
            + Создать проект
          </RouterLink>
        </div>

      </template>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import { useAuthStore } from '@/stores/auth.js'
import { budgetApi } from '@/api/index.js'

const auth = useAuthStore()
const projects = ref([])
const loading = ref(true)

const active    = computed(() => projects.value.filter(p => p.status === 'active'))
const completed = computed(() => projects.value.filter(p => p.status !== 'active'))

onMounted(async () => {
  try {
    projects.value = await budgetApi.projects()
  } finally {
    loading.value = false
  }
})

const fmt = n => Number(n || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })

const pctClass  = p => p >= 100 ? 'danger' : p >= 80 ? 'warn' : 'text-success'
const pctBar    = p => p >= 100 ? 'over'   : p >= 80 ? 'warn' : 'ok'
const pctBadge  = p => p >= 100 ? 'badge-danger' : p >= 80 ? 'badge-warning' : 'badge-success'

const danger = 'danger'
</script>

<style scoped>
.page-header { display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.page-title  { font-size: 1.5rem; font-weight: 700; letter-spacing: -.02em; }

.section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: .7rem;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--muted);
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }
.dot-success { width: 8px; height: 8px; border-radius: 50%; background: var(--success); flex-shrink: 0; }
.dot-muted   { width: 8px; height: 8px; border-radius: 50%; background: var(--muted);   flex-shrink: 0; }

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.project-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow: hidden;
  text-decoration: none;
  color: inherit;
  display: block;
  transition: transform .2s, box-shadow .2s, border-color .2s;
}
.project-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 40px rgba(0,0,0,.4);
  border-color: var(--border-2);
}
.card-stripe { height: 3px; }
.card-body   { padding: 16px; }
.card-name   { font-weight: 700; font-size: .95rem; }
.card-code   { font-size: .75rem; margin-top: 2px; }

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.stat-cell {
  background: var(--surface-2);
  border-radius: 8px;
  padding: 8px 10px;
  text-align: center;
}
.stat-val {
  font-size: .95rem;
  font-weight: 700;
  line-height: 1.2;
}
.stat-lbl {
  font-size: .62rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .06em;
  margin-top: 2px;
}
.text-success { color: var(--success); }
.warn         { color: var(--warning); }
.danger       { color: var(--danger); }
</style>
