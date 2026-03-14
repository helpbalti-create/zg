from django.urls import path
from . import views
from .api_views import (
    JWTLoginView, JWTRefreshView, LogoutView,
    MeView, ChangePasswordView,
)

urlpatterns = [
    path('register/', views.register, name='register'),
    path('pending/', views.pending_approval, name='pending_approval'),
    path('logout/', views.logout_view, name='accounts_logout'),
    path('profile/', views.profile, name='profile'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
]

api_urlpatterns = [
    path('api/auth/login/', JWTLoginView.as_view(), name='api_login'),
    path('api/auth/refresh/', JWTRefreshView.as_view(), name='api_token_refresh'),
    path('api/auth/logout/', LogoutView.as_view(), name='api_logout'),
    path('api/auth/me/', MeView.as_view(), name='api_me'),
    path('api/auth/change-password/', ChangePasswordView.as_view(), name='api_change_password'),
]
