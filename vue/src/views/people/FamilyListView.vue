<template>
  <AppLayout>
    <div class="animate-fadeUp">
      <div class="page-header mb-4">
        <div>
          <h2 class="page-title">Семьи</h2>
          <p class="muted" style="font-size:.875rem;margin-top:4px;">{{ total || '' }} {{ total ? 'семей в базе' : '' }}</p>
        </div>
        <RouterLink to="/families/new" class="btn btn-primary">+ Добавить семью</RouterLink>
      </div>

      <!-- Search -->
      <div class="search-bar mb-4" style="max-width:400px;">
        <div style="position:relative;">
          <svg style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--muted);pointer-events:none;" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input v-model="q" type="text" placeholder="Поиск по названию…" style="padding-left:38px;" @input="debouncedSearch" />
        </div>
      </div>

      <div v-if="loading" class="empty-state">
        <div class="spinner" style="width:28px;height:28px;border-width:2px;margin:0 auto;" />
      </div>

      <div v-else-if="families.length" class="families-grid">
        <RouterLink
          v-for="f in families"
          :key="f.id"
          :to="`/families/${f.id}`"
          class="family-card animate-fadeUp"
        >
          <div class="family-icon">🏠</div>
          <div class="family-name">{{ f.name }}</div>
          <div class="family-meta muted">{{ f.member_count || 0 }} чел.</div>
          <div class="family-address muted" v-if="f.address">📍 {{ f.address }}</div>
        </RouterLink>
      </div>

      <div v-else class="card empty-state">
        <div style="font-size:2.5rem;opacity:.3;margin-bottom:12px;">🏠</div>
        <h4>{{ q ? 'Ничего не найдено' : 'Семей пока нет' }}</h4>
        <RouterLink to="/families/new" class="btn btn-primary" style="margin-top:16px;">+ Добавить</RouterLink>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import { peopleApi } from '@/api/index.js'

const families = ref([])
const total = ref(0)
const q = ref('')
const loading = ref(true)

async function search() {
  loading.value = true
  try {
    const res = await peopleApi.families({ q: q.value })
    families.value = Array.isArray(res) ? res : (res.results || [])
    total.value = res.count || families.value.length
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

.families-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.family-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 20px;
  text-decoration: none;
  color: inherit;
  transition: border-color .15s, transform .15s, box-shadow .15s;
  display: block;
}
.family-card:hover {
  border-color: var(--people);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,.3);
}
.family-icon { font-size: 1.8rem; margin-bottom: 10px; }
.family-name { font-weight: 700; font-size: 1rem; margin-bottom: 4px; }
.family-meta { font-size: .8rem; margin-bottom: 4px; }
.family-address { font-size: .78rem; margin-top: 8px; }
</style>
