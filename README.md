# 🏥 Здоровый Город — Система учёта НКО

## ⚡ Быстрый старт

### 1. Установить все зависимости
```bash
pip install -r requirements.txt
```

### 2. Удалить старую базу (если есть) и применить миграции
```bash
del db.sqlite3          # Windows
rm db.sqlite3           # Mac/Linux

python manage.py migrate
```

### 3. Создать суперпользователя (вводить EMAIL, не username!)
```bash
python manage.py createsuperuser
# Email: admin@example.com
# Full name: Иванов Иван
# Password: (минимум 10 символов, заглавная, спецсимвол)
```

### 4. Запустить
```bash
python manage.py runserver
```
Открыть: **http://127.0.0.1:8000**

---

## 🔐 Архитектура безопасности

### 1. Email как логин (без username)
- `USERNAME_FIELD = 'email'`
- Кастомный `CustomUserManager` с `create_superuser`
- `EmailBackend` — аутентификация по email + защита от timing attacks

### 2. Хеширование паролей — Argon2
```python
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # primary
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',  # fallback
]
```
Требования к паролю: мин. 10 символов + заглавная + спецсимвол.

### 3. JWT-аутентификация (для API)
| Эндпоинт | Метод | Описание |
|---|---|---|
| `/api/auth/login/` | POST | Получить access + refresh токены |
| `/api/auth/refresh/` | POST | Обновить access токен |
| `/api/auth/logout/` | POST | Blacklist refresh токена |
| `/api/auth/me/` | GET/PATCH | Профиль текущего пользователя |
| `/api/auth/change-password/` | POST | Сменить пароль |

- Access token: **15 минут**
- Refresh token: **7 дней**, rotate + blacklist
- Throttle на логин: **5 запросов/минуту**

Пример запроса:
```bash
POST /api/auth/login/
{"email": "user@example.com", "password": "MyPassword123!"}

# Response:
{"access": "eyJ...", "refresh": "eyJ..."}

# Использование:
Authorization: Bearer eyJ...
```

### 4. Социальная авторизация (OAuth2)
Настрой в Django Admin → Sites → Social Applications:

**Google:**
1. https://console.cloud.google.com → Create OAuth 2.0 Client
2. Redirect URI: `http://localhost:8000/oauth/google/login/callback/`
3. В `settings.py` → `SOCIALACCOUNT_PROVIDERS.google.APP`

**GitHub:**
1. https://github.com/settings/developers → New OAuth App
2. Callback URL: `http://localhost:8000/oauth/github/login/callback/`
3. В `settings.py` → `SOCIALACCOUNT_PROVIDERS.github.APP`

### 5. Защита от брутфорса — django-axes
- Блокировка после **5 неудачных попыток** (по IP + email)
- Автоматическая разблокировка через **30 минут**
- Страница блокировки: `templates/accounts/lockout.html`
- Управление в Django Admin → Axes → Access Attempts

```bash
# Ручная разблокировка IP:
python manage.py axes_reset --ip 192.168.1.1
```

### 6. Двухфакторная аутентификация (2FA TOTP)
- Подключи Google Authenticator или Authy
- Настройка: http://localhost:8000/account/two_factor/setup/
- Резервные коды: http://localhost:8000/account/two_factor/backup/tokens/
- `TWO_FACTOR_PATCH_ADMIN = True` — защищает и /admin/

---

## 🛡️ OWASP Top 10 — что закрыто

| # | Уязвимость | Защита |
|---|---|---|
| A01 | Broken Access Control | Role-based + department isolation |
| A02 | Cryptographic Failures | Argon2 hashing, HTTPS в production |
| A03 | Injection | Django ORM (параметризованные запросы) |
| A05 | Security Misconfiguration | Strict settings, HSTS, secure cookies |
| A07 | Auth Failures | Axes brute-force, JWT blacklist, 2FA |
| A09 | Logging Failures | last_login_ip, password_changed_at |

---

## 👥 Роли пользователей

| Роль | Возможности |
|------|-------------|
| **Администратор** | Полный доступ, управление пользователями |
| **Редактор** | Чтение + запись в своём отделе |
| **Просмотр** | Только чтение в своём отделе |

Новые пользователи ждут `is_approved=True` от администратора.
Подтвердить: Django Admin → Users → is_approved ✓
