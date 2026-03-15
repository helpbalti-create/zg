from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
)
from .utils import get_client_ip

User = get_user_model()


# ── Throttle ──────────────────────────────────────────────────────────────────

class LoginThrottle(AnonRateThrottle):
    scope = 'login'


# ── Auth views ────────────────────────────────────────────────────────────────

class JWTLoginView(TokenObtainPairView):
    """POST /api/auth/login/ — возвращает access + refresh токены."""
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginThrottle]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            email = request.data.get('email', '').strip().lower()
            try:
                user = User.objects.get(email=email)
                User.objects.filter(pk=user.pk).update(last_login_ip=get_client_ip(request))
            except User.DoesNotExist:
                pass
        return response


class JWTRefreshView(TokenRefreshView):
    """POST /api/auth/refresh/ — обновить access токен."""
    pass


class LogoutView(APIView):
    """POST /api/auth/logout/ — инвалидировать refresh токен."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'refresh token обязателен.'}, status=400)
        try:
            RefreshToken(refresh_token).blacklist()
        except Exception:
            return Response({'detail': 'Неверный или просроченный токен.'}, status=400)
        return Response({'detail': 'Вы вышли из системы.'})


class MeView(APIView):
    """GET/PATCH /api/auth/me/ — профиль текущего пользователя."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    def patch(self, request):
        s = UserProfileSerializer(request.user, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)


class RegisterView(APIView):
    """POST /api/auth/register/ — регистрация нового пользователя."""
    permission_classes = [AllowAny]

    def post(self, request):
        email     = request.data.get('email', '').strip().lower()
        full_name = request.data.get('full_name', '').strip()
        password1 = request.data.get('password1', '')
        password2 = request.data.get('password2', '')

        errors = {}
        if not email:
            errors['email'] = ['Email обязателен.']
        elif User.objects.filter(email=email).exists():
            errors['email'] = ['Пользователь с таким email уже существует.']

        if not full_name:
            errors['full_name'] = ['Имя обязательно.']

        if not password1:
            errors['password1'] = ['Пароль обязателен.']
        elif password1 != password2:
            errors['password2'] = ['Пароли не совпадают.']

        if errors:
            return Response(errors, status=400)

        # Валидация пароля через Django validators
        try:
            temp_user = User(email=email, full_name=full_name)
            validate_password(password1, temp_user)
        except ValidationError as e:
            return Response({'password1': e.messages}, status=400)

        user = User.objects.create_user(
            email=email,
            full_name=full_name,
            password=password1,
            is_approved=False,  # ждёт одобрения администратора
        )
        return Response(
            {'detail': 'Аккаунт создан. Ожидайте одобрения администратора.'},
            status=201,
        )


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = ChangePasswordSerializer(data=request.data, context={'request': request})
        if not s.is_valid():
            return Response(s.errors, status=400)

        new_password = s.validated_data['new_password']
        try:
            validate_password(new_password, request.user)
        except ValidationError as e:
            return Response({'new_password': e.messages}, status=400)

        request.user.set_password(new_password)
        request.user.password_changed_at = timezone.now()
        request.user.save(update_fields=['password', 'password_changed_at'])

        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
            for token in OutstandingToken.objects.filter(user=request.user):
                RefreshToken(token.token).blacklist()
        except Exception:
            pass

        return Response({'detail': 'Пароль успешно изменён. Войдите снова.'})


# ── Admin: Users ──────────────────────────────────────────────────────────────

class UserListView(APIView):
    """GET /api/accounts/users/ — список всех пользователей (только admin)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser and request.user.role != 'admin':
            return Response({'detail': 'Нет доступа.'}, status=403)
        users = User.objects.select_related('department').order_by('-date_joined')
        return Response(UserProfileSerializer(users, many=True).data)


class UserDetailView(APIView):
    """PATCH /api/accounts/users/:pk/ — обновить пользователя."""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not request.user.is_superuser and request.user.role != 'admin':
            return Response({'detail': 'Нет доступа.'}, status=403)
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Не найден.'}, status=404)

        # Разрешаем менять роль и доступ к приложению
        allowed = ('role', 'app_access', 'position', 'phone', 'is_approved')
        for field in allowed:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
        return Response(UserProfileSerializer(user).data)


class UserApproveView(APIView):
    """POST /api/accounts/users/:pk/approve/ — одобрить пользователя."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_superuser and request.user.role != 'admin':
            return Response({'detail': 'Нет доступа.'}, status=403)
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Не найден.'}, status=404)

        user.is_approved = True
        if 'app_access' in request.data:
            user.app_access = request.data['app_access']
        user.save()
        return Response({'detail': 'Пользователь одобрен.', 'user': UserProfileSerializer(user).data})
