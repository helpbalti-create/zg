"""
core/views.py
=============
Вместо портала — редирект на первое доступное приложение.
Если доступа нет — страница ожидания.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def home(request):
    """
    Точка входа после логина.
    Перенаправляет сразу в нужное приложение — без промежуточного портала.
    """
    user = request.user

    # Ещё не одобрен администратором
    if not getattr(user, 'is_approved', False):
        return render(request, 'core/pending_approval.html')

    # Редирект в первое доступное приложение
    if user.has_app_access('budget'):
        return redirect('/budget/')
    if user.has_app_access('people'):
        return redirect('/people/')

    # Доступ есть, но ни одно приложение не назначено
    return render(request, 'core/no_apps.html')


def permission_denied_view(request, exception=None):
    return render(request, 'core/403.html', {'exception': exception}, status=403)


def not_found_view(request, exception=None):
    return render(request, 'core/404.html', status=404)
