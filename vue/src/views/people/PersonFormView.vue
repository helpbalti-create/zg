<template>
  <AppLayout>
    <div class="animate-fadeUp" style="max-width:640px;">
      <RouterLink :to="isEdit ? `/people/${route.params.id}` : '/people'" class="muted" style="font-size:.85rem;text-decoration:none;">
        ← {{ isEdit ? 'Назад к карточке' : 'Все люди' }}
      </RouterLink>
      <h2 style="font-size:1.4rem;font-weight:700;margin:8px 0 24px;letter-spacing:-.02em;">
        {{ isEdit ? 'Редактировать' : 'Добавить человека' }}
      </h2>

      <div class="card">
        <div v-if="error" class="alert alert-danger mb-4">{{ error }}</div>

        <form @submit.prevent="save">
          <div class="form-group">
            <label class="form-label">Полное имя *</label>
            <input v-model="form.full_name" type="text" placeholder="Фамилия Имя Отчество" required />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Дата рождения</label>
              <input v-model="form.birth_date" type="date" />
            </div>
            <div class="form-group">
              <label class="form-label">Пол</label>
              <select v-model="form.gender">
                <option value="">— не указан —</option>
                <option value="M">Мужской</option>
                <option value="F">Женский</option>
                <option value="O">Другой</option>
              </select>
            </div>
          </div>

          <!-- Dynamic fields -->
          <template v-for="cat in fieldCategories" :key="cat.id">
            <div class="field-section-title">{{ cat.name }}</div>
            <template v-for="fd in cat.fields" :key="fd.id">
              <div class="form-group">
                <label class="form-label">{{ fd.label }}{{ fd.required ? ' *' : '' }}</label>
                <textarea v-if="fd.field_type === 'textarea'" v-model="dynFields[fd.name]" :placeholder="fd.help_text" />
                <select v-else-if="fd.field_type === 'choice'" v-model="dynFields[fd.name]">
                  <option value="">— выберите —</option>
                  <option v-for="c in fd.choices_list" :key="c" :value="c">{{ c }}</option>
                </select>
                <input v-else :type="fieldInputType(fd.field_type)" v-model="dynFields[fd.name]" :placeholder="fd.help_text" :required="fd.required" />
                <p v-if="fd.help_text" class="form-hint">{{ fd.help_text }}</p>
              </div>
            </template>
          </template>

          <div class="flex gap-2 mt-4">
            <button type="submit" class="btn btn-primary" :disabled="saving">
              <span v-if="saving" class="spinner" style="width:14px;height:14px;border-width:2px" />
              <span v-else>{{ isEdit ? 'Сохранить' : 'Создать' }}</span>
            </button>
            <RouterLink :to="isEdit ? `/people/${route.params.id}` : '/people'" class="btn btn-ghost">Отмена</RouterLink>
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
import { peopleApi } from '@/api/index.js'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id && route.path.includes('/edit'))
const form = ref({ full_name: '', birth_date: '', gender: '' })
const dynFields = ref({})
const fieldCategories = ref([])
const saving = ref(false)
const error = ref('')

onMounted(async () => {
  fieldCategories.value = await peopleApi.fieldCategories()
  if (isEdit.value) {
    const p = await peopleApi.person(route.params.id)
    form.value = { full_name: p.full_name, birth_date: p.birth_date || '', gender: p.gender || '' }
    // populate dynamic fields from field_values
    p.field_values?.forEach(fv => { dynFields.value[fv.field_name] = fv.value })
  }
})

async function save() {
  saving.value = true
  error.value = ''
  try {
    const payload = { ...form.value, field_values: dynFields.value }
    if (isEdit.value) {
      await peopleApi.updatePerson(route.params.id, payload)
      router.push(`/people/${route.params.id}`)
    } else {
      const p = await peopleApi.createPerson(payload)
      router.push(`/people/${p.id}`)
    }
  } catch(e) {
    error.value = e.data?.detail || e.message || 'Ошибка сохранения'
  } finally {
    saving.value = false
  }
}

function fieldInputType(t) {
  if (t === 'number') return 'number'
  if (t === 'date')   return 'date'
  if (t === 'email')  return 'email'
  if (t === 'phone')  return 'tel'
  return 'text'
}
</script>

<style scoped>
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 500px) { .form-row { grid-template-columns: 1fr; } }

.field-section-title {
  font-size: .68rem;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 20px 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.mt-4 { margin-top: 20px; }
</style>
