from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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
from .utils import get_client_ip  # FIX: use shared spoofing-resistant helper

User = get_user_model()


class LoginThrottle(AnonRateThrottle):
    """Strict throttle for login endpoint: 5 req/min."""
    scope = 'login'


class JWTLoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Returns access + refresh JWT tokens.
    Rate-limited: 5 attempts/minute per IP.
    Protected by django-axes (blocks after 5 total failures).
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginThrottle]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # Track last login IP using spoofing-resistant helper
            email = request.data.get('email', '').strip().lower()
            try:
                user = User.objects.get(email=email)
                ip = get_client_ip(request)  # FIX: removed duplicate local function
                User.objects.filter(pk=user.pk).update(last_login_ip=ip)
            except User.DoesNotExist:
                pass

        return response


class JWTRefreshView(TokenRefreshView):
    """POST /api/auth/refresh/ — get new access token using refresh token."""
    pass


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklists the refresh token — stateless logout.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'refresh token обязателен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {'detail': 'Неверный или просроченный токен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({'detail': 'Вы вышли из системы.'}, status=status.HTTP_200_OK)


class MeView(APIView):
    """GET/PATCH /api/auth/me/ — current user profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/ — change password with validation."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_password = serializer.validated_data['new_password']

        # Run all Django password validators
        try:
            validate_password(new_password, request.user)
        except ValidationError as e:
            return Response({'new_password': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.password_changed_at = timezone.now()
        request.user.save(update_fields=['password', 'password_changed_at'])

        # Blacklist all existing refresh tokens (force re-login on all devices)
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
            tokens = OutstandingToken.objects.filter(user=request.user)
            for token in tokens:
                t = RefreshToken(token.token)
                t.blacklist()
        except Exception:
            pass

        return Response({'detail': 'Пароль успешно изменён. Войдите снова.'})
