import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const routes = [
  // ── Auth ────────────────────────────────────────────
  {
    path: '/oauth/callback',
    name: 'oauth-callback',
    component: () => import('@/views/auth/OAuthCallbackView.vue'),
    meta: { public: true }
  },
{
  path: '/login',
  name: 'login',
  component: () => import('@/views/auth/LoginView.vue'),
  meta: { public: true }
},
{
  path: '/register',
  name: 'register',
  component: () => import('@/views/auth/RegisterView.vue'),
  meta: { public: true }
},

// ── Portal ───────────────────────────────────────────
{
  path: '/',
  name: 'portal',
  component: () => import('@/views/PortalView.vue')
},

// ── Budget ───────────────────────────────────────────
{
  path: '/budget',
  name: 'budget',
  component: () => import('@/views/budget/ProjectListView.vue'),
  meta: { app: 'budget' }
},
{
  path: '/budget/:id',
  name: 'project-detail',
  component: () => import('@/views/budget/ProjectDetailView.vue'),
  meta: { app: 'budget' }
},
{
  path: '/budget/new',
  name: 'project-create',
  component: () => import('@/views/budget/ProjectFormView.vue'),
  meta: { app: 'budget', requiresEdit: true }
},
{
  path: '/budget/:projId/expense/new',
  name: 'expense-create',
  component: () => import('@/views/budget/ExpenseFormView.vue'),
  meta: { app: 'budget', requiresEdit: true }
},
{
  path: '/budget/expense/:id/edit',
  name: 'expense-edit',
  component: () => import('@/views/budget/ExpenseFormView.vue'),
  meta: { app: 'budget', requiresEdit: true }
},

// ── People ───────────────────────────────────────────
{
  path: '/people',
  name: 'people',
  component: () => import('@/views/people/PersonListView.vue'),
  meta: { app: 'people' }
},
{
  path: '/people/:id',
  name: 'person-detail',
  component: () => import('@/views/people/PersonDetailView.vue'),
  meta: { app: 'people' }
},
{
  path: '/people/new',
  name: 'person-create',
  component: () => import('@/views/people/PersonFormView.vue'),
  meta: { app: 'people' }
},
{
  path: '/people/:id/edit',
  name: 'person-edit',
  component: () => import('@/views/people/PersonFormView.vue'),
  meta: { app: 'people' }
},
{
  path: '/families',
  name: 'families',
  component: () => import('@/views/people/FamilyListView.vue'),
  meta: { app: 'people' }
},
{
  path: '/families/:id',
  name: 'family-detail',
  component: () => import('@/views/people/FamilyDetailView.vue'),
  meta: { app: 'people' }
},

// ── Accounts ─────────────────────────────────────────
{
  path: '/users',
  name: 'users',
  component: () => import('@/views/accounts/UserListView.vue'),
  meta: { requiresAdmin: true }
},
{
  path: '/profile',
  name: 'profile',
  component: () => import('@/views/accounts/ProfileView.vue')
},
]

const router = createRouter({
  history: createWebHistory(),
                            routes,
                            scrollBehavior: () => ({ top: 0 })
})

// ── Navigation guard ─────────────────────────────────────────────────────────
router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (!auth.user && !auth.loading) await auth.fetchMe()

    if (to.meta.public) return true

      if (!auth.isAuthenticated) return { name: 'login', query: { next: to.fullPath } }

      if (to.meta.requiresAdmin && !auth.isAdmin) return { name: 'portal' }

      if (to.meta.app === 'budget' && !auth.canBudget && !auth.isAdmin)
        return { name: 'portal' }

        if (to.meta.app === 'people' && !auth.canPeople && !auth.isAdmin)
          return { name: 'portal' }
})

export default router
