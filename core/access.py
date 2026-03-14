"""
core/access.py
==============
Миксины и декораторы для ограничения доступа по app_access.

Принцип: если у пользователя нет доступа к приложению —
он получает 404, а не 403. Он не знает о существовании раздела.
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404


def require_app_access(app: str):
    """
    Декоратор для function-based views.
    Нет доступа → 404 (пользователь не знает о существовании раздела).
    Не одобрен → 403.

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
                raise Http404  # не 403 — пользователь не должен знать что раздел существует
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


class AppAccessMixin(LoginRequiredMixin):
    """Базовый миксин для class-based views. Установите required_app = 'budget' или 'people'."""
    required_app: str = ''

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        user = request.user
        if not getattr(user, 'is_approved', False):
            raise PermissionDenied('Ваш аккаунт ещё не подтверждён.')
        if self.required_app and not user.has_app_access(self.required_app):
            raise Http404  # тихо — раздел «не существует» для этого пользователя
        return super().dispatch(request, *args, **kwargs)


class BudgetAccessMixin(AppAccessMixin):
    required_app = 'budget'


class PeopleAccessMixin(AppAccessMixin):
    required_app = 'people'


class AppAccessAdminMixin:
    """
    Миксин для ModelAdmin — второй уровень защиты.

        class ExpenseAdmin(AppAccessAdminMixin, admin.ModelAdmin):
            required_app_access = 'budget'
    """
    required_app_access: str = ''

    def _has_access(self, request) -> bool:
        user = request.user
        if user.is_superuser:
            return True
        if not self.required_app_access:
            return True
        return getattr(user, 'has_app_access', lambda _: False)(self.required_app_access)

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
