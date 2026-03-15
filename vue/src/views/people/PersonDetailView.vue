<template>
  <AppLayout>
    <div v-if="loading" class="empty-state">
      <div class="spinner" style="width:28px;height:28px;border-width:2px;margin:0 auto;" />
    </div>

    <div v-else-if="person" class="animate-fadeUp">

      <!-- Breadcrumb + actions -->
      <div class="flex justify-between items-start mb-4 wrap gap-2">
        <div>
          <RouterLink to="/people" class="muted" style="font-size:.85rem;text-decoration:none;">
            ← Все люди
          </RouterLink>
          <h2 style="font-size:1.6rem;font-weight:700;letter-spacing:-.03em;margin-top:4px;">
            {{ person.full_name }}
          </h2>
          <div class="muted" style="font-size:.875rem;margin-top:4px;display:flex;gap:12px;flex-wrap:wrap;">
            <span v-if="person.birth_date">📅 {{ person.birth_date }}{{ person.age ? ` · ${person.age} лет` : '' }}</span>
            <span v-if="person.gender_display">{{ person.gender_display }}</span>
          </div>
        </div>
        <div class="flex gap-2">
          <RouterLink :to="`/people/${person.id}/edit`" class="btn btn-ghost btn-sm">✏ Редактировать</RouterLink>
          <button class="btn btn-danger btn-sm" @click="confirmDelete">🗑 Удалить</button>
        </div>
      </div>

      <div class="detail-grid">

        <!-- Left: questionnaire fields -->
        <div class="card">
          <h6 style="font-weight:700;margin-bottom:16px;font-size:.95rem;">📋 Анкета</h6>

          <template v-if="grouped && Object.keys(grouped).length">
            <div v-for="(fvs, cat) in grouped" :key="cat" class="field-group">
              <div class="field-group-title">{{ cat }}</div>
              <div v-for="fv in fvs.filter(f => f.value)" :key="fv.field.name" class="field-row">
                <span class="field-label">{{ fv.field.label }}</span>
                <span class="field-value">{{ fv.value }}</span>
              </div>
            </div>
          </template>
          <div v-else class="muted" style="font-size:.875rem;">Дополнительные данные не заполнены</div>
        </div>

        <!-- Right: families + relationships -->
        <div class="side-stack">

          <!-- Families -->
          <div class="card card-sm">
            <div class="flex justify-between items-center mb-3">
              <h6 style="font-weight:700;font-size:.9rem;">🏠 Семьи</h6>
            </div>
            <div v-if="families.length">
              <div v-for="m in families" :key="m.id" class="member-row">
                <div>
                  <RouterLink :to="`/families/${m.family.id}`" class="member-name">{{ m.family.name }}</RouterLink>
                  <span v-if="m.role" class="badge badge-muted ms">{{ m.role.name }}</span>
                  <span v-if="m.is_head" class="badge badge-warning ms">Глава</span>
                </div>
                <button class="btn btn-danger btn-xs" @click="removeMember(m.id)">×</button>
              </div>
            </div>
            <div v-else class="muted" style="font-size:.875rem;">Не состоит в семьях</div>
          </div>

          <!-- Relationships -->
          <div class="card card-sm">
            <div class="flex justify-between items-center mb-3">
              <h6 style="font-weight:700;font-size:.9rem;">🔗 Связи</h6>
              <RouterLink :to="`/people/${person.id}/relationship/new`" class="btn btn-ghost btn-xs">+ Добавить</RouterLink>
            </div>

            <template v-if="outgoing.length || incoming.length">
              <div v-for="r in outgoing" :key="r.id" class="rel-row">
                <span class="badge badge-budget">{{ r.relationship_type.name }}</span>
                <RouterLink :to="`/people/${r.to_person.id}`" class="rel-name">{{ r.to_person.full_name }}</RouterLink>
                <button class="btn btn-danger btn-xs ms-auto" @click="deleteRel(r.id)">×</button>
              </div>
              <div v-for="r in incoming" :key="r.id" class="rel-row">
                <RouterLink :to="`/people/${r.from_person.id}`" class="rel-name">{{ r.from_person.full_name }}</RouterLink>
                <span class="badge badge-muted">{{ r.relationship_type.reverse_name || r.relationship_type.name }}</span>
                <span class="muted" style="font-size:.72rem;">(входящая)</span>
              </div>
            </template>
            <div v-else class="muted" style="font-size:.875rem;">Связей нет</div>
          </div>

        </div>
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
const person  = ref(null)
const loading = ref(true)

const families = computed(() => person.value?.family_memberships || [])
const outgoing  = computed(() => person.value?.relationships_from || [])
const incoming  = computed(() => person.value?.relationships_to || [])
const grouped   = computed(() => person.value?.grouped_fields || {})

onMounted(async () => {
  try {
    person.value = await peopleApi.person(route.params.id)
  } finally {
    loading.value = false
  }
})

async function removeMember(memberId) {
  if (!confirm('Убрать из семьи?')) return
  await peopleApi.removeMember(memberId)
  person.value = await peopleApi.person(route.params.id)
}

async function deleteRel(relId) {
  await peopleApi.deleteRelationship(relId)
  person.value = await peopleApi.person(route.params.id)
}

async function confirmDelete() {
  if (!confirm(`Удалить ${person.value.full_name}?`)) return
  await peopleApi.deletePerson(route.params.id)
  router.push('/people')
}
</script>

<style scoped>
.detail-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 16px;
  align-items: start;
}
@media (max-width: 900px) { .detail-grid { grid-template-columns: 1fr; } }

.side-stack { display: flex; flex-direction: column; gap: 12px; }

.field-group { margin-bottom: 16px; }
.field-group-title {
  font-size: .68rem;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}
.field-row {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  font-size: .875rem;
}
.field-label {
  color: var(--muted);
  min-width: 160px;
  flex-shrink: 0;
}
.field-value { font-weight: 500; }

.member-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-size: .875rem;
}
.member-row:last-child { border-bottom: none; }
.member-name { text-decoration: none; color: var(--text); font-weight: 600; }
.member-name:hover { color: var(--budget); }
.ms { margin-left: 6px; }
.ms-auto { margin-left: auto; }

.rel-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 0;
  border-bottom: 1px solid var(--border);
  font-size: .85rem;
}
.rel-row:last-child { border-bottom: none; }
.rel-name { text-decoration: none; color: var(--text); font-weight: 500; }
.rel-name:hover { color: var(--budget); }
</style>
