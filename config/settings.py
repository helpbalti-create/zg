"""
config/settings.py — production-ready secure configuration.

All secrets are read from environment variables (via python-decouple).
Copy .env.example → .env and fill in your values before running.
"""
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── SECRETS FROM ENVIRONMENT ─────────────────────────────────────────────────
# Generate: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = config('SECRET_KEY')

# FIX: Separate signing key for JWT tokens.
# Rotating this invalidates all tokens without affecting sessions/CSRF.
# Generate: python -c "import secrets; print(secrets.token_hex(64))"
JWT_SIGNING_KEY = config('JWT_SIGNING_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

# Comma-separated in .env:  ALLOWED_HOSTS=example.com,www.example.com
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# ─── INSTALLED APPS ────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',          # required by allauth


    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',

    'axes',                          # brute-force protection

    'django_otp',                    # 2FA base
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'two_factor',                    # 2FA UI

    # Project apps
    'accounts.apps.AccountsConfig',
    'budget',
    'core',
    'people',

    'corsheaders',
]

SITE_ID = 1

# ─── MIDDLEWARE ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',           # 2FA — after AuthMiddleware
    'allauth.account.middleware.AccountMiddleware',  # allauth
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',                # brute-force — MUST be last
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # required by allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ─── DATABASE ──────────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ─── CUSTOM USER MODEL ─────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.CustomUser'

# ─── AUTHENTICATION BACKENDS ───────────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',              # axes — MUST be first
    'accounts.backends.EmailBackend',                   # email-based login
    'allauth.account.auth_backends.AuthenticationBackend',  # social auth
]

# ─── PASSWORD HASHING — ARGON2 (OWASP recommended) ────────────────────────────
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',      # primary
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',      # fallback / migration
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# ─── PASSWORD VALIDATORS ───────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {'user_attributes': ('email', 'full_name'), 'max_similarity': 0.5},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 10},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'accounts.validators.UppercaseValidator',
    },
    {
        'NAME': 'accounts.validators.SpecialCharValidator',
    },
]

# ─── JWT — djangorestframework-simplejwt ───────────────────────────────────────
# FIX: SIGNING_KEY now uses dedicated JWT_SIGNING_KEY, NOT the Django SECRET_KEY.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),    # Short-lived — reduce exposure window
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,                     # New refresh token on each use
    'BLACKLIST_AFTER_ROTATION': True,                  # Invalidate old refresh token
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': JWT_SIGNING_KEY,                    # FIX: separate key, not SECRET_KEY

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',

    'TOKEN_OBTAIN_SERIALIZER': 'accounts.serializers.CustomTokenObtainPairSerializer',
}

# ─── DRF — Rate Limiting (throttling) ─────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/hour',    # Anonymous: 20 requests/hour
        'user': '100/hour',   # Authenticated: 100/hour
        'login': '5/minute',  # Login endpoint: 5 attempts/minute
    },
}

# ─── DJANGO-AXES — Brute-force protection ──────────────────────────────────────
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5                          # Block after 5 failed attempts
AXES_COOLOFF_TIME = timedelta(minutes=30)       # Auto-unblock after 30 min
AXES_LOCKOUT_PARAMETERS = ['ip_address', 'username']  # Track by IP + email
AXES_RESET_ON_SUCCESS = True                    # Reset counter on successful login
AXES_LOCKOUT_TEMPLATE = 'accounts/lockout.html'
AXES_VERBOSE = False
AXES_SENSITIVE_PARAMETERS = ['password']        # Never log passwords in failed attempts

# ─── DJANGO-ALLAUTH (Social OAuth2) ────────────────────────────────────────────
# allauth >= 0.63 uses new-style settings
ACCOUNT_LOGIN_METHODS = {'email'}                               # replaces ACCOUNT_AUTHENTICATION_METHOD
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*'] # replaces EMAIL_REQUIRED + USERNAME_REQUIRED
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = False
# FIX: Critical — without this allauth tries to access CustomUser.username → FieldDoesNotExist
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID', default=''),
            'secret':    config('GOOGLE_CLIENT_SECRET', default=''),
            'key':       '',
        },
    },
    'github': {
        'SCOPE': ['user:email'],
        'APP': {
            'client_id': config('GITHUB_CLIENT_ID', default=''),
            'secret':    config('GITHUB_CLIENT_SECRET', default=''),
        },
    },
}

# ─── TWO-FACTOR AUTH ────────────────────────────────────────────────────────────
TWO_FACTOR_PATCH_ADMIN = True
TWO_FACTOR_CALL_GATEWAY = None
TWO_FACTOR_SMS_GATEWAY = None
LOGIN_URL = '/oauth/login/'  # allauth login page — must be a real Django URL
LOGIN_REDIRECT_URL    = '/accounts/oauth/success/'  # после Google/GitHub → JWT → Vue
LOGOUT_REDIRECT_URL   = '/login'
SOCIALACCOUNT_ADAPTER = 'accounts.social_adapter.SocialAccountAdapter'
ACCOUNT_ADAPTER       = 'accounts.social_adapter.AccountAdapter'
SOCIALACCOUNT_AUTO_SIGNUP = True

# ─── SECURITY SETTINGS ─────────────────────────────────────────────────────────
# Production HTTPS hardening (only when DEBUG=False)
# FIX: All HTTPS settings are guarded by DEBUG check.
#      Running with DEBUG=False locally will activate SECURE_SSL_REDIRECT
#      and break plain HTTP dev server. Set DEBUG=True in your .env for local dev.
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000           # 1 year HSTS
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True               # Force HTTPS (production only)
    SESSION_COOKIE_SECURE = True             # Session cookie over HTTPS only
    CSRF_COOKIE_SECURE = True                # CSRF cookie over HTTPS only

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Session hardening
SESSION_COOKIE_HTTPONLY = True               # JS cannot access session cookie
SESSION_COOKIE_AGE = 3600                    # 1-hour session timeout
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# FIX: Was True — WRONG. When CSRF_COOKIE_HTTPONLY=True, JavaScript cannot
#      read the CSRF token, silently breaking all AJAX/fetch POST requests.
#      Must stay False (Django's default) so JS can include it in requests.
CSRF_COOKIE_HTTPONLY = False

# CSRF_TRUSTED_ORIGINS = config(
#     'CSRF_TRUSTED_ORIGINS',
#     default='http://127.0.0.1:8000,http://localhost:8000',
#     cast=Csv(),
# )
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://localhost:3000',
]

# ─── LOCALIZATION ──────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Chisinau'
USE_I18N = True
USE_TZ = True

# ─── STATIC / MEDIA ────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
_STATIC_DIR = BASE_DIR / 'static'
STATICFILES_DIRS = [_STATIC_DIR] if _STATIC_DIR.exists() else []
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── EMAIL ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@zdravy-gorod.md')


# ─── ERROR HANDLERS ────────────────────────────────────────────────────────────
handler403 = 'core.views.permission_denied_view'


CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000', cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# ─── FRONTEND URL ──────────────────────────────────────────────────────────────
# Where the Vue SPA is hosted. Used to build the post-OAuth redirect URL.
# Dev:  http://localhost:3000
# Prod: https://zdravy-gorod.md
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000').rstrip('/')


SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_DOMAIN = None

AXES_WHITELIST_CALLABLE = 'accounts.utils.axes_oauth_whitelist'
AXES_NEVER_LOCKOUT_GET = True

