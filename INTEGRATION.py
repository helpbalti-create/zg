# ════════════════════════════════════════════════════════
# ИЗМЕНЕНИЯ В settings.py
# ════════════════════════════════════════════════════════

INSTALLED_APPS = [
    # Заменить 'django.contrib.admin' на кастомный AdminSite:
    'django.contrib.admin',   # оставить как есть — нужен для шаблонов

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Проект
    'accounts',
    'budget',
    'people',
    'core',              # ← добавить
]

# После Login перенаправлять на портал
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/account/login/'    # или 'two_factor:login' если используется 2FA

# Обработчики ошибок
handler403 = 'core.views.permission_denied_view'
handler404 = 'core.views.not_found_view'


# ════════════════════════════════════════════════════════
# ИЗМЕНЕНИЯ В urls.py (корневой)
# ════════════════════════════════════════════════════════

from django.contrib import admin
from django.urls import path, include
from zdoroviy_gorod.admin_site import admin_site  # ← кастомный AdminSite

urlpatterns = [
    # Кастомный AdminSite вместо стандартного
    path('admin/', admin_site.urls),              # ← заменить admin.site.urls

    # Портал (главная страница)
    path('', include('core.urls', namespace='core')),

    # Существующие маршруты
    path('accounts/', include('accounts.urls')),
    path('people/', include('people.urls', namespace='people')),
    # path('budget/', include('budget.urls')),    # если есть urls у budget

    # 2FA (если используется)
    # path('account/', include('two_factor.urls', 'two_factor')),
]


# ════════════════════════════════════════════════════════
# РЕГИСТРАЦИЯ МОДЕЛЕЙ В КАСТОМНОМ AdminSite
# ════════════════════════════════════════════════════════
#
# В каждом admin.py нужно добавить регистрацию в admin_site:
#
# В accounts/admin.py:
#   from zdoroviy_gorod.admin_site import admin_site
#   admin_site.register(CustomUser, CustomUserAdmin)
#   admin_site.register(Department, DepartmentAdmin)
#
# В budget/admin.py:
#   from zdoroviy_gorod.admin_site import admin_site
#   admin_site.register(Project, ProjectAdmin)
#   # ... и т.д.
#
# В people/admin.py:
#   from zdoroviy_gorod.admin_site import admin_site
#   admin_site.register(Person, PersonAdmin)
#   # ... и т.д.
#
# ВАЖНО: @admin.register(Model) работает с django.contrib.admin.site
# Для кастомного сайта используйте admin_site.register(Model, ModelAdmin)
# ════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════
# КАК ИСПОЛЬЗОВАТЬ МИКСИНЫ В VIEWS
# ════════════════════════════════════════════════════════

# Function-based view:
#   from core.access import require_app_access
#
#   @require_app_access('budget')
#   def budget_dashboard(request):
#       ...

# Class-based view:
#   from core.access import BudgetAccessMixin, PeopleAccessMixin
#
#   class BudgetView(BudgetAccessMixin, TemplateView):
#       template_name = 'budget/dashboard.html'

# ════════════════════════════════════════════════════════
# ПРИМЕНИТЬ МИГРАЦИИ
# ════════════════════════════════════════════════════════
#
#   python manage.py migrate accounts
#   python manage.py migrate people
