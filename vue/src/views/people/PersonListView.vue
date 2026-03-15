<template>
  <AppLayout>
    <div class="animate-fadeUp">

      <div class="page-header mb-4">
        <div>
          <h2 class="page-title">Люди</h2>
          <p class="muted" style="font-size:.875rem;margin-top:4px;">
            {{ total ? `${total} человек в базе` : 'CRM — база контактов' }}
          </p>
        </div>
        <RouterLink to="/people/new" class="btn btn-primary">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          Добавить
        </RouterLink>
      </div>

      <!-- Search bar -->
      <div class="search-bar mb-4">
        <div class="search-input-wrap">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            v-model="q"
            type="text"
            placeholder="Поиск по имени…"
            @input="debouncedSearch"
          />
          <button v-if="q" class="clear-btn" @click="q = ''; search()">×</button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="empty-state">
        <div class="spinner" style="width:28px;height:28px;border-width:2px;margin:0 auto;" />
      </div>

      <!-- Table -->
      <div v-else-if="people.length" class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>ФИО</th>
              <th>Пол</th>
              <th>Дата рождения</th>
              <th>Возраст</th>
              <th>Семьи</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in people" :key="p.id" class="person-row">
              <td>
                <RouterLink :to="`/people/${p.id}`" class="person-link">
                  <div class="person-avatar">{{ p.full_name[0] }}</div>
                  <span>{{ p.full_name }}</span>
                </RouterLink>
              </td>
              <td class="muted">{{ p.gender_display || '—' }}</td>
              <td class="muted">{{ p.birth_date || '—' }}</td>
              <td class="muted">{{ p.age ? `${p.age} л.` : '—' }}</td>
              <td>
                <div class="flex gap-1 wrap">
                  <RouterLink
                    v-for="m in p.family_memberships"
                    :key="m.family_id"
                    :to="`/families/${m.family_id}`"
                    class="badge badge-muted"
                  >{{ m.family_name }}</RouterLink>
                  <span v-if="!p.family_memberships?.length" class="muted">—</span>
                </div>
              </td>
              <td>
                <RouterLink :to="`/people/${p.id}/edit`" class="btn btn-ghost btn-xs">✏</RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Empty -->
      <div v-else class="card empty-state">
        <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
        <h4 style="margin-top:12px;">{{ q ? 'Никого не найдено' : 'Список пуст' }}</h4>
        <p>{{ q ? `Нет людей по запросу «${q}»` : 'Добавьте первого человека' }}</p>
        <RouterLink v-if="!q" to="/people/new" class="btn btn-primary" style="margin-top:16px;">
          + Добавить
        </RouterLink>
      </div>

    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import { peopleApi } from '@/api/index.js'

const people = ref([])
const total  = ref(0)
const q      = ref('')
const loading = ref(true)

async function search() {
  loading.value = true
  try {
    const res = await peopleApi.persons({ q: q.value })
    people.value = Array.isArray(res) ? res : (res.results || [])
    total.value  = res.count || people.value.length
  } finally {
    loading.value = false
  }
}

let timer
function debouncedSearch() {
  clearTimeout(timer)
  timer = setTimeout(search, 300)
}

onMounted(search)
</script>

<style scoped>
.page-header { display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.page-title  { font-size: 1.5rem; font-weight: 700; letter-spacing: -.02em; }

.search-bar { max-width: 420px; }
.search-input-wrap { position: relative; }
.search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--muted); pointer-events: none; }
.search-input-wrap input { padding-left: 38px; padding-right: 32px; }
.clear-btn { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: none; border: none; color: var(--muted); cursor: pointer; font-size: 1.1rem; line-height: 1; }

.person-row:hover .person-link { color: var(--budget); }
.person-link {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--text);
  font-weight: 600;
  font-size: .9rem;
}
.person-avatar {
  width: 30px; height: 30px; border-radius: 50%;
  background: var(--budget-dim); color: var(--budget);
  font-size: .78rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
</style>
