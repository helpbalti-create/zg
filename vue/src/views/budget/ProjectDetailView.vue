<template>
  <AppLayout>
    <div v-if="loading" class="empty-state">
      <div class="spinner" style="width:32px;height:32px;border-width:3px;margin:0 auto;" />
    </div>

    <div v-else-if="project" class="animate-fadeUp">

      <!-- Hero card -->
      <div class="hero-card mb-4">
        <div class="hero-left">
          <div class="hero-name">{{ project.name }}</div>
          <div class="hero-meta muted">
            <span v-if="project.donor">🏢 {{ project.donor }}</span>
            <span v-if="project.project_code" class="code-chip">{{ project.project_code }}</span>
            <span>{{ project.start_date }} — {{ project.end_date }}</span>
            <span class="badge badge-muted">{{ project.duration_months }} мес.</span>
          </div>
          <span class="badge badge-success mt-2" v-if="project.status === 'active'">● Активный</span>
          <span class="badge badge-muted mt-2" v-else>✓ Завершён</span>
        </div>

        <div class="hero-right">
          <div class="hero-stats">
            <div class="hero-stat">
              <div class="hero-val" style="color:#7fffc4">${{ fmt(project.total_budget) }}</div>
              <div class="hero-lbl">Всего выделено</div>
            </div>
            <div class="hero-stat">
              <div class="hero-val" :style="`color:${project.spent_percent>=100?'#ff7675':project.spent_percent>=80?'#ffd93d':'#74b9ff'}`">
                ${{ fmt(project.total_spent) }}
              </div>
              <div class="hero-lbl">Потрачено ({{ project.spent_percent }}%)</div>
            </div>
            <div class="hero-stat">
              <div class="hero-val" :style="`color:${project.total_remaining<0?'#ff7675':'#a8edea'}`">
                ${{ fmt(project.total_remaining) }}
              </div>
              <div class="hero-lbl">Остаток</div>
            </div>
          </div>
          <div style="font-size:.7rem;color:rgba(255,255,255,.5);display:flex;justify-content:space-between;margin-bottom:4px;">
            <span>Использование</span><span>{{ project.spent_percent }}%</span>
          </div>
          <div class="hero-progress">
            <div class="hero-progress-fill"
              :style="`width:${Math.min(project.spent_percent,100)}%;background:${project.spent_percent>=100?'#ff7675':project.spent_percent>=80?'#ffd93d':'#55efc4'}`"
            />
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-2 wrap mb-4">
        <template v-if="auth.canEdit && project.status === 'active'">
          <RouterLink :to="`/budget/${project.id}/expense/new`" class="btn btn-primary btn-sm">
            + Добавить расход
          </RouterLink>
          <button class="btn btn-ghost btn-sm" @click="$router.push(`/budget/${project.id}/category/new`)">
            + Новая статья
          </button>
          <button class="btn btn-ghost btn-sm" @click="showComplete = true">
            🏁 Завершить
          </button>
        </template>
        <a :href="`/api/budget/projects/${project.id}/export/`" class="btn btn-ghost btn-sm" style="margin-left:auto;">
          📊 Экспорт Excel
        </a>
        <RouterLink to="/budget" class="btn btn-ghost btn-sm">← Назад</RouterLink>
      </div>

      <!-- Completed alert -->
      <div v-if="project.status === 'completed'" class="alert alert-success mb-4">
        ✓ Проект завершён {{ project.completed_at?.slice(0,10) }}
        <span v-if="project.completion_note"> — {{ project.completion_note }}</span>
      </div>

      <!-- Tabs -->
      <div class="tabs-bar">
        <button class="tab-btn" :class="{ active: tab === 'budget' }" @click="tab = 'budget'">📋 Смета</button>
        <button class="tab-btn" :class="{ active: tab === 'expenses' }" @click="tab = 'expenses'">🧾 Расходы</button>
        <button class="tab-btn" :class="{ active: tab === 'corrections' }" @click="tab = 'corrections'" v-if="corrections.length">
          🕐 Корректировки
        </button>
      </div>

      <!-- TAB: Budget table -->
      <div v-show="tab === 'budget'">
        <div class="table-wrap">
          <table class="data-table budget-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Код</th>
                <th style="text-align:left;min-width:200px;">Статья</th>
                <th>Ед.изм.</th>
                <th class="num">Кол-во</th>
                <th class="num">Стоим.</th>
                <th class="num">Частота</th>
                <th class="num">Бюджет</th>
                <th class="num">Потрачено</th>
                <th class="num">Остаток</th>
                <th class="ctr">%</th>
                <th v-if="auth.canEdit && project.status==='active'"></th>
              </tr>
            </thead>
            <tbody>
              <template v-for="sw in sectionsWithGroups" :key="sw.section.id">
                <!-- Section row -->
                <tr class="section-row">
                  <td :colspan="auth.canEdit && project.status==='active' ? 12 : 11">
                    <div class="flex justify-between items-center">
                      <span>📁 SECTION {{ sw.section.code }}: {{ sw.section.name.toUpperCase() }}</span>
                      <span class="muted" style="font-size:.72rem;">
                        Budget: ${{ fmt(sw.section.total_allocated) }} · Spent: ${{ fmt(sw.section.total_spent) }}
                      </span>
                    </div>
                  </td>
                </tr>

                <!-- Categories -->
                <template v-for="(grp, gi) in sw.groups" :key="gi">
                  <!-- Group header -->
                  <tr v-if="grp.categories.length > 1" class="group-header">
                    <td :colspan="auth.canEdit && project.status==='active' ? 12 : 11">
                      <div class="flex items-center gap-3">
                        <span class="code-chip">{{ grp.code || '—' }}</span>
                        <span class="muted" style="font-size:.72rem;">{{ grp.categories.length }} строки</span>
                        <span style="margin-left:auto;font-size:.72rem;color:var(--text-2);">
                          Лимит: <b>${{ fmt(grp.allocated) }}</b> · Потрачено: <b>${{ fmt(grp.spent) }}</b> · Остаток: <b :class="grp.remaining<0?'danger':''">{{ fmt(grp.remaining) }}</b>
                        </span>
                      </div>
                    </td>
                  </tr>

                  <tr v-for="(cat, ci) in grp.categories" :key="cat.id"
                    :class="{ 'row-over': cat.is_over_budget, 'row-warn': cat.is_warning }">
                    <td class="ctr muted">{{ gi+1 }}.{{ ci+1 }}</td>
                    <td class="ctr"><span class="code-chip">{{ cat.code || '—' }}</span></td>
                    <td>
                      <div style="font-weight:500;">{{ cat.name }}</div>
                      <div v-if="cat.notes" class="muted" style="font-size:.7rem;margin-top:1px;">{{ cat.notes.slice(0,80) }}</div>
                    </td>
                    <td class="ctr muted" style="font-size:.78rem;">{{ cat.unit_measure || '—' }}</td>
                    <td class="num">{{ cat.quantity }}</td>
                    <td class="num">${{ cat.unit_cost }}</td>
                    <td class="num ctr">{{ cat.frequency }}</td>
                    <td class="num">${{ fmt(cat.allocated_amount) }}</td>
                    <td class="num" style="color:var(--danger);">${{ fmt(cat.total_spent) }}</td>
                    <td class="num" :class="cat.remaining < 0 ? 'danger' : 'text-success'">${{ fmt(cat.remaining) }}</td>
                    <td>
                      <div class="flex items-center gap-1">
                        <div class="progress" style="min-width:40px;flex:1;height:4px;">
                          <div class="progress-bar" :class="pctBar(cat.spent_percent)"
                            :style="`width:${Math.min(cat.spent_percent,100)}%`"/>
                        </div>
                        <span style="font-size:.68rem;min-width:26px;text-align:right;" :class="cat.is_over_budget?'danger':''">{{ cat.spent_percent }}%</span>
                      </div>
                    </td>
                    <td v-if="auth.canEdit && project.status==='active'" class="ctr">
                      <div class="flex gap-1 justify-center">
                        <RouterLink :to="`/budget/${project.id}/expense/new?category=${cat.id}`" class="btn btn-ghost btn-xs">+</RouterLink>
                        <button class="btn btn-ghost btn-xs">✏</button>
                      </div>
                    </td>
                  </tr>

                  <!-- Group footer -->
                  <tr v-if="grp.categories.length > 1" class="group-footer">
                    <td colspan="7" style="text-align:right;padding-right:12px;font-size:.72rem;color:var(--muted);">
                      ∑ Итого по коду <span class="code-chip">{{ grp.code }}</span>
                    </td>
                    <td class="num">${{ fmt(grp.allocated) }}</td>
                    <td class="num" :class="grp.is_over?'danger':''">{{ fmt(grp.spent) }}</td>
                    <td class="num" :class="grp.remaining<0?'danger':'text-success'">${{ fmt(grp.remaining) }}</td>
                    <td class="ctr" :class="grp.is_over?'danger':''">{{ grp.pct }}%</td>
                    <td v-if="auth.canEdit && project.status==='active'"></td>
                  </tr>
                </template>
              </template>

              <!-- Grand total -->
              <tr class="total-row">
                <td colspan="7" style="text-align:right;padding-right:14px;">TOTAL GRANT BUDGET:</td>
                <td class="num" style="color:#7fffc4;">${{ fmt(project.total_budget) }}</td>
                <td class="num" :style="`color:${project.spent_percent>=100?'#ff7675':'#ffd580'}`">${{ fmt(project.total_spent) }}</td>
                <td class="num" :style="`color:${project.total_remaining<0?'#ff7675':'#a8edea'}`">${{ fmt(project.total_remaining) }}</td>
                <td class="ctr" style="color:#a8edea;font-weight:700;">{{ project.spent_percent }}%</td>
                <td v-if="auth.canEdit && project.status==='active'"></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- TAB: Expenses -->
      <div v-show="tab === 'expenses'">
        <div class="flex gap-2 wrap mb-3 items-center">
          <select v-model="periodFilter" style="width:auto;min-width:140px;">
            <option value="">Все периоды</option>
            <option v-for="i in 6" :key="i" :value="i">Период {{ i }}</option>
          </select>
          <span class="muted" style="font-size:.8rem;margin-left:auto;">
            Записей: {{ filteredExpenses.length }} · Итого: ${{ fmt(expenseTotal) }}
          </span>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Дата</th>
                <th>Код</th>
                <th>Статья / Описание</th>
                <th class="ctr">Период</th>
                <th>Документ №</th>
                <th class="num">Сумма</th>
                <th>Кто внёс</th>
                <th v-if="auth.canEdit"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in filteredExpenses" :key="e.id">
                <td style="white-space:nowrap;">{{ e.date }}</td>
                <td class="ctr"><span class="code-chip">{{ e.category?.code || '—' }}</span></td>
                <td>
                  <div style="font-weight:500;font-size:.85rem;">{{ e.category?.name }}</div>
                  <div class="muted" style="font-size:.75rem;">{{ e.description }}</div>
                </td>
                <td class="ctr"><span class="badge badge-muted">П{{ e.period }}</span></td>
                <td class="muted" style="font-size:.8rem;">{{ e.document_number || '—' }}</td>
                <td class="num" style="color:var(--danger);font-weight:600;">${{ fmt(e.amount) }}</td>
                <td class="muted" style="font-size:.78rem;">{{ e.created_by || '—' }}</td>
                <td v-if="auth.canEdit">
                  <div class="flex gap-1">
                    <RouterLink :to="`/budget/expense/${e.id}/edit`" class="btn btn-ghost btn-xs">✏</RouterLink>
                    <button class="btn btn-danger btn-xs" @click="deleteExpense(e.id)">🗑</button>
                  </div>
                </td>
              </tr>
              <tr v-if="!filteredExpenses.length">
                <td :colspan="auth.canEdit ? 8 : 7" class="empty-state" style="padding:40px;">
                  Расходов нет
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- TAB: Corrections -->
      <div v-show="tab === 'corrections'">
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Дата</th><th>Тип</th><th>Статья</th><th>Было</th><th>Стало</th><th>Причина</th><th>Кто</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in corrections" :key="c.id">
                <td>{{ c.date }}</td>
                <td><span class="badge badge-warning">{{ c.correction_type_display }}</span></td>
                <td class="muted">{{ c.category?.name || 'Весь проект' }}</td>
                <td class="muted">{{ c.old_value || '—' }}</td>
                <td style="font-weight:600;">{{ c.new_value || '—' }}</td>
                <td>{{ c.reason }}</td>
                <td class="muted" style="font-size:.8rem;">{{ c.created_by }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import { useAuthStore } from '@/stores/auth.js'
import { budgetApi } from '@/api/index.js'

const auth = useAuthStore()
const route = useRoute()

const project = ref(null)
const expenses = ref([])
const corrections = ref([])
const loading = ref(true)
const tab = ref('budget')
const periodFilter = ref('')

onMounted(async () => {
  const id = route.params.id
  try {
    const [p, e, c] = await Promise.all([
      budgetApi.project(id),
      budgetApi.expenses(id),
      budgetApi.corrections(id),
    ])
    project.value = p
    expenses.value = e
    corrections.value = c
  } finally {
    loading.value = false
  }
})

const filteredExpenses = computed(() =>
  periodFilter.value
    ? expenses.value.filter(e => e.period == periodFilter.value)
    : expenses.value
)
const expenseTotal = computed(() =>
  filteredExpenses.value.reduce((s, e) => s + Number(e.amount || 0), 0)
)

// Build sections with groups from project data
const sectionsWithGroups = computed(() => {
  if (!project.value?.sections) return []
  return project.value.sections.map(section => ({
    section,
    groups: buildGroups(section.categories || [])
  }))
})

function buildGroups(cats) {
  const map = {}
  cats.forEach(c => {
    const k = c.code || '__none__'
    if (!map[k]) map[k] = []
    map[k].push(c)
  })
  return Object.entries(map).map(([code, categories]) => {
    const allocated = categories.reduce((s, c) => s + Number(c.allocated_amount || 0), 0)
    const spent = categories.reduce((s, c) => s + Number(c.total_spent || 0), 0)
    const remaining = allocated - spent
    const pct = allocated ? Math.round(spent / allocated * 100) : 0
    return { code: code === '__none__' ? '' : code, categories, allocated, spent, remaining, pct, is_over: spent > allocated, is_warning: pct >= 80 && spent <= allocated }
  })
}

async function deleteExpense(id) {
  if (!confirm('Удалить расход?')) return
  await budgetApi.deleteExpense(id)
  expenses.value = expenses.value.filter(e => e.id !== id)
}

const fmt = n => Number(n || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })
const pctBar = p => p >= 100 ? 'over' : p >= 80 ? 'warn' : 'ok'
</script>

<style scoped>
/* Hero */
.hero-card {
  background: linear-gradient(135deg, #1a3a5c 0%, #2d6196 100%);
  border-radius: 16px;
  padding: 22px 26px;
  color: #fff;
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  align-items: flex-start;
}
.hero-left  { flex: 1; min-width: 220px; }
.hero-right { flex: 1; min-width: 260px; }
.hero-name  { font-size: 1.15rem; font-weight: 700; margin-bottom: 6px; }
.hero-meta  { font-size: .78rem; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.hero-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 12px; }
.hero-stat  { text-align: center; }
.hero-val   { font-size: 1.3rem; font-weight: 700; line-height: 1; }
.hero-lbl   { font-size: .65rem; text-transform: uppercase; letter-spacing: .07em; opacity: .6; margin-top: 4px; }
.hero-progress { height: 8px; background: rgba(255,255,255,.2); border-radius: 5px; overflow: hidden; }
.hero-progress-fill { height: 100%; border-radius: 5px; transition: width .7s ease; }
.mt-2 { margin-top: 8px; display: inline-flex; }

/* Budget table */
.budget-table .section-row td {
  background: rgba(59,130,246,.12);
  color: var(--budget);
  font-weight: 700;
  font-size: .78rem;
  text-transform: uppercase;
  letter-spacing: .03em;
  border-top: 2px solid rgba(59,130,246,.2);
}
.budget-table .group-header td {
  background: var(--surface-2);
  border-left: 3px solid var(--border-2);
  font-size: .72rem;
}
.budget-table .group-footer td {
  background: var(--surface-2);
  border-left: 3px solid var(--border-2);
  font-size: .72rem;
  font-weight: 700;
  border-top: 1px solid var(--border);
}
.budget-table .total-row td {
  background: rgba(59,130,246,.08);
  font-weight: 700;
  border-top: 2px solid var(--budget-dim);
}
.row-over td { background: rgba(239,68,68,.07) !important; }
.row-warn td { background: rgba(245,158,11,.07) !important; }

.text-success { color: var(--success); }
.danger       { color: var(--danger); }
</style>
