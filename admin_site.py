"""
zdoroviy_gorod/admin_site.py
============================
Кастомный AdminSite с изоляцией по app_access.

Принцип «defense-in-depth»:
  1. get_app_list()       — скрывает чужие приложения из меню (UX)
  2. has_permission()     — блокирует не-staff и не-approved пользователей
  3. AppAccessAdminMixin  — каждый ModelAdmin дополнительно проверяет app_access
                            (защита если кто-то угадает URL)

Карта: app_access → разрешённые django app_label
"""

from django.contrib.admin import AdminSite
from django.conf import settings

# app_label → required app_access values
APP_LABEL_ACCESS: dict[str, list[str]] = {
    # Budget app models
    'budget':   ['budget', 'all'],
    # CRM / people models
    'people':   ['people', 'all'],
    # accounts & auth — superusers only via is_staff
    'accounts': ['all'],
    'auth':     ['all'],
}


class AppAwareAdminSite(AdminSite):
    """
    Расширенный AdminSite:
      - скрывает разделы, к которым у пользователя нет доступа
      - не выбрасывает 403 на весь сайт — только скрывает лишнее
    """
    site_header  = '🏙 Здоровый Город — Управление'
    site_title   = 'Здоровый Город'
    index_title  = 'Панель администратора'

    @property
    def site_url(self):
        # "View site" button → Vue frontend, not the Django server.
        # Reads FRONTEND_URL from .env so it works in both dev and prod.
        return getattr(settings, 'FRONTEND_URL', 'http://localhost:3000') + '/'

    def has_permission(self, request):
        """Пользователь должен быть активным, подтверждённым и staff."""
        user = request.user
        return (
            user.is_active
            and user.is_authenticated
            and getattr(user, 'is_approved', False)
            and user.is_staff
        )

    def get_app_list(self, request, app_label=None):
        """Возвращает только те разделы, к которым есть доступ."""
        app_list = super().get_app_list(request, app_label)
        user = request.user
        if user.is_superuser:
            return app_list

        user_access = getattr(user, 'app_access', 'budget')
        filtered = []
        for app in app_list:
            label    = app.get('app_label', '')
            allowed  = APP_LABEL_ACCESS.get(label, ['all'])
            if user_access in allowed or user_access == 'all':
                filtered.append(app)
        return filtered


class AppAccessAdminMixin:
    """
    Миксин для ModelAdmin — второй уровень защиты.
    Укажи required_app_access = 'budget' или 'people'.

    Пример:
        class ExpenseAdmin(AppAccessAdminMixin, admin.ModelAdmin):
            required_app_access = 'budget'
    """
    required_app_access: str = ''  # override in subclass

    def _check_access(self, request) -> bool:
        user = request.user
        if user.is_superuser:
            return True
        if not self.required_app_access:
            return True
        return getattr(user, 'has_app_access', lambda _: False)(self.required_app_access)

    def has_view_permission(self, request, obj=None):
        return self._check_access(request) and super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        return self._check_access(request) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._check_access(request) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self._check_access(request) and super().has_delete_permission(request, obj)

    def has_module_perms(self, request, app_label):
        return self._check_access(request)


# Singleton — используется вместо django.contrib.admin.site
admin_site = AppAwareAdminSite(name='admin')
