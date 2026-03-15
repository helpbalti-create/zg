<template>
  <AppLayout>
    <div class="animate-fadeUp">
      <div class="page-header mb-6">
        <div>
          <h2 class="page-title">Пользователи</h2>
          <p class="muted" style="font-size:.875rem;margin-top:4px;">Управление доступом к системе</p>
        </div>
      </div>

      <div v-if="loading" class="empty-state">
        <div class="spinner" style="width:28px;height:28px;border-width:2px;margin:0 auto;" />
      </div>

      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Пользователь</th>
              <th>Роль</th>
              <th>Доступ</th>
              <th>Статус</th>
              <th>Дата регистрации</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>
                <div class="flex items-center gap-2">
                  <div class="user-ava">{{ u.full_name?.[0] || u.email?.[0] || '?' }}</div>
                  <div>
                    <div style="font-weight:600;font-size:.9rem;">{{ u.full_name }}</div>
                    <div class="muted" style="font-size:.77rem;">{{ u.email }}</div>
                  </div>
                </div>
              </td>
              <td>
                <span class="badge" :class="roleClass(u.role)">{{ u.role_display || u.role }}</span>
              </td>
              <td>
                <select
                  :value="u.app_access"
                  @change="e => updateAccess(u.id, e.target.value)"
                  style="width:auto;min-width:160px;font-size:.8rem;padding:4px 8px;"
                >
                  <option value="">— Не назначен —</option>
                  <option value="budget">💰 Бюджет</option>
                  <option value="people">👥 Люди</option>
                  <option value="all">🔑 Все</option>
                </select>
              </td>
              <td>
                <span class="badge" :class="u.is_approved ? 'badge-success' : 'badge-warning'">
                  {{ u.is_approved ? 'Активен' : 'Ожидает' }}
                </span>
              </td>
              <td class="muted" style="font-size:.8rem;">{{ u.date_joined?.slice(0, 10) }}</td>
              <td>
                <div class="flex gap-1">
                  <button
                    v-if="!u.is_approved"
                    class="btn btn-success btn-xs"
                    @click="approve(u.id)"
                  >✓ Одобрить</button>
                  <button class="btn btn-ghost btn-xs" @click="editUser = u">✏</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Edit modal -->
      <div v-if="editUser" class="modal-backdrop" @click.self="editUser = null">
        <div class="modal-card animate-fadeUp">
          <h4 style="font-weight:700;margin-bottom:20px;">Редактировать пользователя</h4>
          <div class="form-group">
            <label class="form-label">Роль</label>
            <select v-model="editUser.role">
              <option value="viewer">Только просмотр</option>
              <option value="editor">Просмотр и редактирование</option>
              <option value="admin">Администратор</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Доступ к приложению</label>
            <select v-model="editUser.app_access">
              <option value="">— Не назначен —</option>
              <option value="budget">💰 Бюджет</option>
              <option value="people">👥 Люди</option>
              <option value="all">🔑 Все</option>
            </select>
          </div>
          <div class="flex gap-2 mt-4">
            <button class="btn btn-primary" @click="saveUser">Сохранить</button>
            <button class="btn btn-ghost" @click="editUser = null">Отмена</button>
          </div>
        </div>
      </div>

    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { accountsApi } from '@/api/index.js'

const users   = ref([])
const loading = ref(true)
const editUser = ref(null)

onMounted(async () => {
  try { users.value = await accountsApi.users() }
  finally { loading.value = false }
})

async function updateAccess(id, app_access) {
  await accountsApi.updateUser(id, { app_access })
}

async function approve(id) {
  await accountsApi.approveUser(id, { is_approved: true })
  const u = users.value.find(u => u.id === id)
  if (u) u.is_approved = true
}

async function saveUser() {
  const u = editUser.value
  await accountsApi.updateUser(u.id, { role: u.role, app_access: u.app_access })
  users.value = users.value.map(x => x.id === u.id ? { ...x, ...u } : x)
  editUser.value = null
}

function roleClass(r) {
  if (r === 'admin')  return 'badge-danger'
  if (r === 'editor') return 'badge-budget'
  return 'badge-muted'
}
</script>

<style scoped>
.page-header { display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.page-title  { font-size: 1.5rem; font-weight: 700; letter-spacing: -.02em; }

.user-ava {
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--surface-2); color: var(--text-2);
  border: 1px solid var(--border-2);
  font-weight: 700; font-size: .8rem;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.6);
  display: flex; align-items: center; justify-content: center;
  z-index: 200;
  padding: 1rem;
}
.modal-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 28px;
  width: 100%; max-width: 400px;
}
.mt-4 { margin-top: 20px; }
</style>
