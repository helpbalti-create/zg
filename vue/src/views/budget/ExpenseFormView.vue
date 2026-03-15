<template>
  <AppLayout>
    <div class="animate-fadeUp" style="max-width:580px;">
      <RouterLink :to="`/budget/${projId}`" class="muted" style="font-size:.85rem;text-decoration:none;">← Назад к проекту</RouterLink>
      <h2 style="font-size:1.4rem;font-weight:700;margin:8px 0 24px;letter-spacing:-.02em;">
        {{ isEdit ? 'Редактировать расход' : 'Добавить расход' }}
      </h2>

      <div class="card">
        <div v-if="error" class="alert alert-danger mb-4">{{ error }}</div>

        <form @submit.prevent="save">
          <div class="form-group">
            <label class="form-label">Статья бюджета *</label>
            <select v-model="form.category" required>
              <option value="">— Выберите статью —</option>
              <optgroup v-for="s in sections" :key="s.id" :label="`${s.code}: ${s.name}`">
                <option v-for="c in s.categories" :key="c.id" :value="c.id">
                  {{ c.code ? `[${c.code}] ` : '' }}{{ c.name }}
                </option>
              </optgroup>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Сумма (USD) *</label>
              <input v-model="form.amount" type="number" step="0.01" placeholder="0.00" required />
            </div>
            <div class="form-group">
              <label class="form-label">Количество</label>
              <input v-model="form.quantity" type="number" step="0.01" placeholder="1" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Дата расхода *</label>
              <input v-model="form.date" type="date" required />
            </div>
            <div class="form-group">
              <label class="form-label">Отчётный период</label>
              <select v-model="form.period">
                <option v-for="i in 6" :key="i" :value="i">Период {{ i }}</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Описание / Назначение *</label>
            <input v-model="form.description" type="text" placeholder="Краткое описание расхода" required />
          </div>

          <div class="form-group">
            <label class="form-label">Номер документа / чека</label>
            <input v-model="form.document_number" type="text" placeholder="ФФ-12345" class="mono" />
          </div>

          <div class="flex gap-2 mt-4">
            <button type="submit" class="btn btn-primary" :disabled="saving">
              <span v-if="saving" class="spinner" style="width:14px;height:14px;border-width:2px" />
              <span v-else>{{ isEdit ? 'Сохранить' : 'Добавить расход' }}</span>
            </button>
            <RouterLink :to="`/budget/${projId}`" class="btn btn-ghost">Отмена</RouterLink>
          </div>
        </form>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import { budgetApi } from '@/api/index.js'

const route  = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id && route.path.includes('/edit'))
const projId = computed(() => route.params.projId || route.query.project)

const today = new Date().toISOString().slice(0, 10)
const form   = ref({ category: route.query.category || '', amount: '', quantity: 1, date: today, period: 1, description: '', document_number: '' })
const sections = ref([])
const saving = ref(false)
const error  = ref('')

onMounted(async () => {
  if (projId.value) {
    const p = await budgetApi.project(projId.value)
    sections.value = p.sections || []
  }
  if (isEdit.value) {
    const e = await budgetApi.expenses(projId.value)
    const exp = e.find(x => x.id == route.params.id)
    if (exp) Object.assign(form.value, { ...exp, category: exp.category?.id })
  }
})

async function save() {
  saving.value = true
  error.value  = ''
  try {
    const payload = { ...form.value, project: projId.value }
    if (isEdit.value) {
      await budgetApi.updateExpense(route.params.id, payload)
    } else {
      await budgetApi.createExpense(payload)
    }
    router.push(`/budget/${projId.value}`)
  } catch (e) {
    error.value = e.data?.detail || JSON.stringify(e.data) || e.message
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 500px) { .form-row { grid-template-columns: 1fr; } }
.mt-4 { margin-top: 20px; }
</style>
