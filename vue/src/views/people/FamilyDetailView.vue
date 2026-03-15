<template>
  <AppLayout>
    <div v-if="loading" class="empty-state">
      <div class="spinner" style="width:28px;height:28px;border-width:2px;margin:0 auto;" />
    </div>

    <div v-else-if="family" class="animate-fadeUp">
      <div class="flex justify-between items-start mb-4 wrap gap-2">
        <div>
          <RouterLink to="/families" class="muted" style="font-size:.85rem;text-decoration:none;">← Все семьи</RouterLink>
          <h2 style="font-size:1.6rem;font-weight:700;letter-spacing:-.03em;margin-top:4px;">🏠 {{ family.name }}</h2>
          <p class="muted" v-if="family.address" style="margin-top:4px;font-size:.875rem;">📍 {{ family.address }}</p>
        </div>
        <div class="flex gap-2">
          <RouterLink :to="`/families/${family.id}/edit`" class="btn btn-ghost btn-sm">✏ Редактировать</RouterLink>
          <button class="btn btn-danger btn-sm" @click="confirmDelete">🗑</button>
        </div>
      </div>

      <!-- Members card -->
      <div class="card mb-4">
        <div class="flex justify-between items-center mb-4">
          <h6 style="font-weight:700;font-size:1rem;">👥 Члены семьи</h6>
          <button class="btn btn-primary btn-sm" @click="showAddMember = true">+ Добавить</button>
        </div>

        <div v-if="family.members?.length" class="members-list">
          <div v-for="m in family.members" :key="m.id" class="member-item">
            <div class="member-avatar">{{ m.person.full_name[0] }}</div>
            <div class="member-info">
              <RouterLink :to="`/people/${m.person.id}`" class="member-name">{{ m.person.full_name }}</RouterLink>
              <div class="flex gap-1 mt-1">
                <span v-if="m.is_head" class="badge badge-warning">👑 Глава</span>
                <span v-if="m.role" class="badge badge-muted">{{ m.role.name }}</span>
                <span v-if="m.person.age" class="badge badge-muted">{{ m.person.age }} л.</span>
              </div>
            </div>
            <button class="btn btn-danger btn-xs" style="margin-left:auto;" @click="removeMember(m.id)">×</button>
          </div>
        </div>
        <div v-else class="muted" style="font-size:.875rem;padding:8px 0;">Членов нет</div>
      </div>

      <!-- Notes -->
      <div class="card" v-if="family.notes">
        <h6 style="font-weight:700;margin-bottom:10px;font-size:.9rem;">📝 Примечания</h6>
        <p style="font-size:.875rem;color:var(--text-2);line-height:1.6;">{{ family.notes }}</p>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import { peopleApi } from '@/api/index.js'

const route = useRoute()
const router = useRouter()
const family = ref(null)
const loading = ref(true)
const showAddMember = ref(false)

onMounted(async () => {
  try { family.value = await peopleApi.family(route.params.id) }
  finally { loading.value = false }
})

async function removeMember(memberId) {
  if (!confirm('Убрать из семьи?')) return
  await peopleApi.removeMember(memberId)
  family.value = await peopleApi.family(route.params.id)
}

async function confirmDelete() {
  if (!confirm(`Удалить семью «${family.value.name}»?`)) return
  await peopleApi.deleteFamily(route.params.id)
  router.push('/families')
}
</script>

<style scoped>
.members-list { display: flex; flex-direction: column; gap: 2px; }
.member-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}
.member-item:last-child { border-bottom: none; }
.member-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--people-dim); color: var(--people);
  font-weight: 700; font-size: .85rem;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.member-info { flex: 1; }
.member-name { text-decoration: none; color: var(--text); font-weight: 600; font-size: .9rem; }
.member-name:hover { color: var(--people); }
.mt-1 { margin-top: 4px; }
</style>
