"""
core/access.py
==============
Миксины и декораторы безопасности для ограничения доступа по app_access.

Defense-in-depth: три уровня защиты
  1. @require_app_access / AppAccessMixin — на уровне views
  2. AppAccessAdminMixin — на уровне каждого ModelAdmin (скрывает из меню + блокирует URL)
  3. base.html — показывает только нужные пункты меню

Использование в views:
    @require_app_access('budget')
    def my_view(request): ...

    class MyView(BudgetAccessMixin, View): ...

Использование в admin:
    class MyModelAdmin(AppAccessAdminMixin, admin.ModelAdmin):
        required_app_access = 'budget'
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


# ──────────────────────────────────────────────────────────────────────────────
# Декоратор для function-based views
# ──────────────────────────────────────────────────────────────────────────────

def require_app_access(app: str):
    """
    Декоратор: требует аутентификацию + is_approved + has_app_access(app).

        @require_app_access('budget')
        def my_view(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not getattr(user, 'is_approved', False):
                raise PermissionDenied('Ваш аккаунт ещё не подтверждён администратором.')
            if not user.has_app_access(app):
                raise PermissionDenied(
                    f'У вас нет доступа к разделу «{app}». '
                    f'Обратитесь к администратору.'
                )
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


# ──────────────────────────────────────────────────────────────────────────────
# Миксины для class-based views
# ──────────────────────────────────────────────────────────────────────────────

class AppAccessMixin(LoginRequiredMixin):
    """Базовый миксин. Установите required_app = 'budget' или 'people'."""
    required_app: str = ''

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        user = request.user
        if not getattr(user, 'is_approved', False):
            raise PermissionDenied('Ваш аккаунт ещё не подтверждён.')
        if self.required_app and not user.has_app_access(self.required_app):
            raise PermissionDenied(
                f'Доступ к разделу «{self.required_app}» запрещён для вашего аккаунта.'
            )
        return super().dispatch(request, *args, **kwargs)


class BudgetAccessMixin(AppAccessMixin):
    required_app = 'budget'


class PeopleAccessMixin(AppAccessMixin):
    required_app = 'people'


# ──────────────────────────────────────────────────────────────────────────────
# Миксин для ModelAdmin — второй уровень защиты (admin-уровень)
# ──────────────────────────────────────────────────────────────────────────────

class AppAccessAdminMixin:
    """
    Добавьте к ModelAdmin и укажите required_app_access.

        class ExpenseAdmin(AppAccessAdminMixin, admin.ModelAdmin):
            required_app_access = 'budget'

    Эффекты:
      - Раздел исчезает из sidebar если у пользователя нет доступа
      - Прямые URL запросы возвращают «недостаточно прав»
    """
    required_app_access: str = ''

    def _has_access(self, request) -> bool:
        user = request.user
        if user.is_superuser:
            return True
        if not self.required_app_access:
            return True
        return getattr(user, 'has_app_access', lambda _: False)(self.required_app_access)

    # has_module_perms определяет виден ли раздел в sidebar
    def has_module_perms(self, request):
        return self._has_access(request) and super().has_module_perms(request)

    def has_view_permission(self, request, obj=None):
        return self._has_access(request) and super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        return self._has_access(request) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._has_access(request) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self._has_access(request) and super().has_delete_permission(request, obj)
