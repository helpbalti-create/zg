<template>
  <AppLayout>
    <div class="animate-fadeUp" style="max-width:640px;">
      <RouterLink to="/budget" class="muted" style="font-size:.85rem;text-decoration:none;">← Бюджетные проекты</RouterLink>
      <h2 style="font-size:1.4rem;font-weight:700;margin:8px 0 24px;letter-spacing:-.02em;">
        {{ isEdit ? 'Редактировать проект' : 'Новый проект' }}
      </h2>

      <div class="card">
        <div v-if="error" class="alert alert-danger mb-4">{{ error }}</div>

        <form @submit.prevent="save">
          <div class="form-group">
            <label class="form-label">Название проекта *</label>
            <input v-model="form.name" type="text" placeholder="Название гранта или проекта" required />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Код проекта</label>
              <input v-model="form.project_code" type="text" placeholder="ABC-2024" class="mono" />
            </div>
            <div class="form-group">
              <label class="form-label">Донор / Источник</label>
              <input v-model="form.donor" type="text" placeholder="Название фонда" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Дата начала *</label>
              <input v-model="form.start_date" type="date" required />
            </div>
            <div class="form-group">
              <label class="form-label">Дата окончания *</label>
              <input v-model="form.end_date" type="date" required />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Общий бюджет (USD) *</label>
              <input v-model="form.total_budget" type="number" step="0.01" placeholder="0.00" required />
            </div>
            <div class="form-group">
              <label class="form-label">Валюта</label>
              <select v-model="form.currency">
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="MDL">MDL</option>
                <option value="RON">RON</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Описание</label>
            <textarea v-model="form.description" placeholder="Краткое описание проекта…" style="min-height:100px;" />
          </div>

          <div class="flex gap-2 mt-4">
            <button type="submit" class="btn btn-primary" :disabled="saving">
              <span v-if="saving" class="spinner" style="width:14px;height:14px;border-width:2px" />
              <span v-else>{{ isEdit ? 'Сохранить' : 'Создать проект' }}</span>
            </button>
            <RouterLink to="/budget" class="btn btn-ghost">Отмена</RouterLink>
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

const isEdit = computed(() => !!route.params.id)
const form   = ref({ name: '', project_code: '', donor: '', start_date: '', end_date: '', total_budget: '', currency: 'USD', description: '' })
const saving = ref(false)
const error  = ref('')

onMounted(async () => {
  if (isEdit.value) {
    const p = await budgetApi.project(route.params.id)
    Object.assign(form.value, p)
  }
})

async function save() {
  saving.value = true
  error.value = ''
  try {
    if (isEdit.value) {
      await budgetApi.updateProject(route.params.id, form.value)
      router.push(`/budget/${route.params.id}`)
    } else {
      const p = await budgetApi.createProject(form.value)
      router.push(`/budget/${p.id}`)
    }
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
