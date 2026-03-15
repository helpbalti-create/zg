from django.urls import path
from .api_views import (
    JWTLoginView, JWTRefreshView, LogoutView,
    MeView, ChangePasswordView, RegisterView,
)

# Эти пути подключаются через *auth_api в config/urls.py
urlpatterns = []  # не используется напрямую

# Экспортируем как api_urlpatterns — подключается в config/urls.py через *auth_api
api_urlpatterns = [
    path('api/auth/login/',           JWTLoginView.as_view(),      name='api_login'),
    path('api/auth/refresh/',         JWTRefreshView.as_view(),    name='api_token_refresh'),
    path('api/auth/logout/',          LogoutView.as_view(),        name='api_logout'),
    path('api/auth/me/',              MeView.as_view(),            name='api_me'),
    path('api/auth/change-password/', ChangePasswordView.as_view(),name='api_change_password'),
    path('api/auth/register/',        RegisterView.as_view(),      name='api_register'),
]
