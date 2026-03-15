// In development the Vite proxy rewrites /api → Django, so a relative path
// avoids CORS entirely. In production Nginx does the same proxying, so the
// relative path still works. Only set VITE_API_BASE_URL if the API lives on
// a completely separate domain (e.g. https://api.zdravy-gorod.md).
const BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

// Хранение токенов
function getAccess()  { return localStorage.getItem('access') }
function getRefresh() { return localStorage.getItem('refresh') }
function saveTokens(a, r) {
  localStorage.setItem('access', a)
  if (r) localStorage.setItem('refresh', r)
}
function clearTokens() {
  localStorage.removeItem('access')
  localStorage.removeItem('refresh')
}

async function request(method, url, data = null) {
  const headers = { 'Content-Type': 'application/json' }
  if (getAccess()) headers['Authorization'] = `Bearer ${getAccess()}`

    const config = { method, headers }
    if (data !== null) config.body = JSON.stringify(data)

      let res = await fetch(`${BASE}${url}`, config)

      // Если access просрочен — попробовать обновить через refresh
      if (res.status === 401 && getRefresh()) {
        const refreshRes = await fetch(`${BASE}/auth/refresh/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh: getRefresh() })
        })
        if (refreshRes.ok) {
          const data = await refreshRes.json()
          saveTokens(data.access, data.refresh)
          headers['Authorization'] = `Bearer ${data.access}`
          res = await fetch(`${BASE}${url}`, { method, headers, body: config.body })
        } else {
          clearTokens()
          window.location.href = '/login'
          return
        }
      }

      if (res.status === 204) return null
        const json = await res.json().catch(() => ({}))
        if (!res.ok) {
          const err = new Error(json.detail || `HTTP ${res.status}`)
          err.status = res.status
          err.data = json
          throw err
        }
        return json
}

export const api = {
  get:    (url)       => request('GET',    url),
  post:   (url, data) => request('POST',   url, data),
  put:    (url, data) => request('PUT',    url, data),
  patch:  (url, data) => request('PATCH',  url, data),
  delete: (url)       => request('DELETE', url),
}

export const authApi = {
  login:   (data) => api.post('/auth/login/', data),
  logout:  (data) => api.post('/auth/logout/', data),
  me:      ()     => api.get('/auth/me/'),
  refresh: ()     => api.post('/auth/refresh/', { refresh: getRefresh() }),
}

export { saveTokens, clearTokens, getAccess }

// остальные namespaces остаются без изменений
export const budgetApi = {
  projects:        ()      => api.get('/budget/projects/'),
  project:         (id)    => api.get(`/budget/projects/${id}/`),
  createProject:   (data)  => api.post('/budget/projects/', data),
  updateProject:   (id, d) => api.patch(`/budget/projects/${id}/`, d),
  completeProject: (id, d) => api.post(`/budget/projects/${id}/complete/`, d),
  expenses:        (id)    => api.get(`/budget/projects/${id}/expenses/`),
  createExpense:   (data)  => api.post('/budget/expenses/', data),
  updateExpense:   (id, d) => api.patch(`/budget/expenses/${id}/`, d),
  deleteExpense:   (id)    => api.delete(`/budget/expenses/${id}/`),
  categories:      (id)    => api.get(`/budget/projects/${id}/categories/`),
  createCategory:  (data)  => api.post('/budget/categories/', data),
  corrections:     (id)    => api.get(`/budget/projects/${id}/corrections/`),
  createCorrection:(data)  => api.post('/budget/corrections/', data),
}

export const peopleApi = {
  persons:          (p)    => api.get(`/people/persons/?${new URLSearchParams(p||{})}`),
  person:           (id)   => api.get(`/people/persons/${id}/`),
  createPerson:     (data) => api.post('/people/persons/', data),
  updatePerson:     (id,d) => api.patch(`/people/persons/${id}/`, d),
  deletePerson:     (id)   => api.delete(`/people/persons/${id}/`),
  families:         (p)    => api.get(`/people/families/?${new URLSearchParams(p||{})}`),
  family:           (id)   => api.get(`/people/families/${id}/`),
  createFamily:     (data) => api.post('/people/families/', data),
  updateFamily:     (id,d) => api.patch(`/people/families/${id}/`, d),
  deleteFamily:     (id)   => api.delete(`/people/families/${id}/`),
  addMember:        (data) => api.post('/people/members/', data),
  removeMember:     (id)   => api.delete(`/people/members/${id}/`),
  addRelationship:  (data) => api.post('/people/relationships/', data),
  deleteRelationship:(id)  => api.delete(`/people/relationships/${id}/`),
  fieldCategories:  ()     => api.get('/people/field-categories/'),
}

export const accountsApi = {
  users:       ()      => api.get('/accounts/users/'),
  updateUser:  (id, d) => api.patch(`/accounts/users/${id}/`, d),
  approveUser: (id, d) => api.post(`/accounts/users/${id}/approve/`, d),
}
