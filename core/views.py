"""
core/views.py
=============
Django-маршруты `/` и `/portal/` теперь редиректят на Vue-фронтенд.

Вся визуальная часть живёт на FRONTEND_URL (Vue SPA).
Django отвечает только за API (/api/*), OAuth (/oauth/*) и Admin (/admin/).
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def _frontend(path: str = '') -> str:
    """Строит абсолютный URL на Vue-фронтенд."""
    base = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000').rstrip('/')
    return f'{base}/{path.lstrip("/")}'


@login_required
def home(request):
    """
    Старая точка входа Django — теперь просто редиректит на Vue.
    Браузер попадает сюда только если зашёл напрямую на 127.0.0.1:8000/.
    """
    return redirect(_frontend('/'))


def permission_denied_view(request, exception=None):
    return render(request, 'core/403.html', {'exception': exception}, status=403)


def not_found_view(request, exception=None):
    return render(request, 'core/404.html', status=404)
