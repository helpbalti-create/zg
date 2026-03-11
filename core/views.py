"""
core/views.py
=============
Портальная страница — точка входа после логина.
Показывает карточки приложений к которым есть доступ.
"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render


@login_required
def portal(request):
    """Главная страница — показывает доступные приложения."""
    user = request.user

    if not getattr(user, 'is_approved', False):
        return render(request, 'core/pending_approval.html', status=403)

    apps = []
    if user.has_app_access('budget'):
        apps.append({
            'slug':        'budget',
            'title':       'Бюджет',
            'description': 'Управление проектами, бюджетными статьями и расходами.',
            'icon':        '💰',
            'url':         '/budget/',
            'color':       '#1a56db',
        })
    if user.has_app_access('people'):
        apps.append({
            'slug':        'people',
            'title':       'CRM — Люди',
            'description': 'База людей, семьи, роли и связи.',
            'icon':        '👥',
            'url':         '/people/',
            'color':       '#057a55',
        })

    return render(request, 'core/portal.html', {'apps': apps})


def permission_denied_view(request, exception=None):
    return render(request, 'core/403.html', status=403)


def not_found_view(request, exception=None):
    return render(request, 'core/404.html', status=404)
