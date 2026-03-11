from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from axes.handlers.proxy import AxesProxyHandler
from axes.helpers import get_lockout_response

from .forms import RegisterForm, EmailLoginForm, UserEditForm, AdminUserEditForm
from .models import CustomUser, Department
from .utils import get_client_ip


def _ensure_departments():
    """Create default departments if they don't exist yet."""
    defaults = [
        ('budget', 'Бюджет и финансы'),
        ('social', 'Социальная помощь'),
        ('events', 'Мероприятия'),
        ('volunteers', 'Волонтёры'),
        ('admin', 'Администрация'),
    ]
    for name, display in defaults:
        Department.objects.get_or_create(name=name, defaults={'display_name': display})


def register(request):
    if request.user.is_authenticated:
        return redirect('core:portal')

    _ensure_departments()

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                '✅ Регистрация прошла успешно! Ожидайте подтверждения администратором.',
            )
            return redirect('two_factor:login')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:portal')

    # Check if IP is locked by axes
    if AxesProxyHandler.is_locked(request):
        return get_lockout_response(request=request, credentials={})

    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            if not user.is_approved:
                messages.error(request, '⏳ Ваш аккаунт ещё не подтверждён администратором.')
                return render(request, 'accounts/login.html', {'form': form})

            login(request, user, backend='accounts.backends.EmailBackend')

            # Track IP using spoofing-resistant helper
            ip = get_client_ip(request)
            CustomUser.objects.filter(pk=user.pk).update(last_login_ip=ip)

            messages.success(request, f'Добро пожаловать, {user.get_short_name()}!')
            return redirect(request.GET.get('next', 'core:portal'))
        else:
            messages.error(request, '❌ Неверный email или пароль.')
    else:
        form = EmailLoginForm(request)

    return render(request, 'accounts/login.html', {'form': form})


# FIX: Was a plain function accepting GET — CSRF vulnerability.
#      A link/image on a third-party site could silently log out the user.
#      @require_POST enforces that logout only happens via POST with CSRF token.
@require_POST
def logout_view(request):
    logout(request)
    return redirect('two_factor:login')


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Профиль обновлён.')
            return redirect('profile')
    else:
        form = UserEditForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def user_list(request):
    if not (request.user.is_superuser or request.user.role == CustomUser.ROLE_ADMIN):
        return render(request, 'core/403.html', status=403)

    users = CustomUser.objects.all().select_related('department').order_by('full_name')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
def user_edit(request, pk):
    if not (request.user.is_superuser or request.user.role == CustomUser.ROLE_ADMIN):
        return render(request, 'core/403.html', status=403)

    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Пользователь {user.full_name} обновлён.')
            return redirect('user_list')
    else:
        form = AdminUserEditForm(instance=user)

    return render(request, 'accounts/user_edit.html', {'form': form, 'edited_user': user})
