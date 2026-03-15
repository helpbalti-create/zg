# Здоровый Город — Vue.js Frontend

Единый Vue 3 фронтенд для всех модулей: Бюджет, CRM-Люди, Пользователи.

## Структура проекта

```
zg-vue/
├── index.html
├── vite.config.js          # Vite + прокси на Django :8000
├── package.json
└── src/
    ├── main.js
    ├── App.vue
    ├── styles/
    │   └── global.css      # Единая тёмная дизайн-система
    ├── api/
    │   └── index.js        # fetch-клиент + CSRF + namespaces
    ├── stores/
    │   └── auth.js         # Pinia — аутентификация
    ├── router/
    │   └── index.js        # vue-router + guards по ролям
    ├── components/
    │   └── AppLayout.vue   # Топнав + layout оболочка
    └── views/
        ├── PortalView.vue
        ├── auth/
        │   ├── LoginView.vue
        │   └── RegisterView.vue
        ├── budget/
        │   ├── ProjectListView.vue
        │   ├── ProjectDetailView.vue
        │   ├── ProjectFormView.vue
        │   └── ExpenseFormView.vue
        ├── people/
        │   ├── PersonListView.vue
        │   ├── PersonDetailView.vue
        │   ├── PersonFormView.vue
        │   ├── FamilyListView.vue
        │   └── FamilyDetailView.vue
        └── accounts/
            ├── UserListView.vue
            └── ProfileView.vue
```

## Запуск фронтенда

```bash
cd zg-vue
npm install
npm run dev        # http://localhost:3000
npm run build      # production build → dist/
```

Vite автоматически проксирует `/api/*`, `/admin/*`, `/media/*` → `http://127.0.0.1:8000`

---

## Необходимые изменения в Django

### 1. Установить DRF

```bash
pip install djangorestframework djangorestframework-simplejwt
```

### 2. settings.py

```python
INSTALLED_APPS += ['rest_framework', 'corsheaders']

MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware', ...MIDDLEWARE]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# CORS (только для разработки)
CORS_ALLOWED_ORIGINS = ['http://localhost:3000']
CORS_ALLOW_CREDENTIALS = True
```

### 3. Добавить API URLs в config/urls.py

```python
from django.urls import path, include

urlpatterns = [
    ...
    path('api/', include('api_urls')),  # см. ниже
]
```

### 4. API endpoints (что ожидает Vue)

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/auth/login/` | Вход |
| POST | `/api/auth/logout/` | Выход |
| GET  | `/api/auth/me/` | Текущий пользователь |
| POST | `/api/auth/register/` | Регистрация |
| GET  | `/api/budget/projects/` | Список проектов |
| GET  | `/api/budget/projects/:id/` | Проект с секциями/категориями |
| POST | `/api/budget/projects/` | Создать проект |
| PATCH| `/api/budget/projects/:id/` | Обновить |
| GET  | `/api/budget/projects/:id/expenses/` | Расходы проекта |
| POST | `/api/budget/expenses/` | Создать расход |
| PATCH| `/api/budget/expenses/:id/` | Обновить расход |
| DELETE| `/api/budget/expenses/:id/` | Удалить расход |
| GET  | `/api/budget/projects/:id/corrections/` | Корректировки |
| GET  | `/api/budget/projects/:id/export/` | Excel файл |
| GET  | `/api/people/persons/` | Список людей (`?q=`) |
| GET  | `/api/people/persons/:id/` | Детали (grouped_fields, families, rels) |
| POST | `/api/people/persons/` | Создать |
| PATCH| `/api/people/persons/:id/` | Обновить |
| DELETE| `/api/people/persons/:id/` | Удалить |
| GET  | `/api/people/families/` | Список семей |
| GET  | `/api/people/families/:id/` | Детали семьи с членами |
| POST | `/api/people/members/` | Добавить в семью |
| DELETE| `/api/people/members/:id/` | Убрать из семьи |
| POST | `/api/people/relationships/` | Добавить связь |
| DELETE| `/api/people/relationships/:id/` | Удалить связь |
| GET  | `/api/people/field-categories/` | Категории полей с полями |
| GET  | `/api/accounts/users/` | Список пользователей (admin) |
| PATCH| `/api/accounts/users/:id/` | Обновить пользователя |
| POST | `/api/accounts/users/:id/approve/` | Одобрить |

---

## Дизайн-система

Все компоненты используют CSS-переменные из `global.css`:

```css
--bg, --surface, --surface-2   /* фоны */
--border, --border-2           /* границы */
--text, --text-2, --muted      /* текст */
--budget, --budget-dim         /* акцент: бюджет (синий) */
--people, --people-dim         /* акцент: люди (зелёный) */
--success, --warning, --danger /* статусы */
```

Шрифты: **Onest** (UI) + **JetBrains Mono** (коды, технические данные)

---

## Production build

```bash
npm run build
# → dist/ скопировать в Django STATIC_ROOT или раздавать через nginx
```

Для production Django должен раздавать `dist/index.html` на все non-API пути:

```python
# config/urls.py — добавить в самый конец
from django.views.generic import TemplateView
urlpatterns += [re_path(r'^(?!api|admin|media).*', TemplateView.as_view(template_name='index.html'))]
```
