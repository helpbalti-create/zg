from django.urls import path
from . import views
from .api_views import (
    JWTLoginView, JWTRefreshView, LogoutView,
    MeView, ChangePasswordView, RegisterView,
    UserListView, UserDetailView, UserApproveView,
)




urlpatterns = [
    path('register/', views.register, name='register'),
    path('pending/', views.pending_approval, name='pending_approval'),
    path('logout/', views.logout_view, name='accounts_logout'),
    path('profile/', views.profile, name='profile'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('oauth/success/', views.oauth_success, name='oauth_success'),
]

api_urlpatterns = [
    path('api/auth/login/', JWTLoginView.as_view(), name='api_login'),
    path('api/auth/refresh/', JWTRefreshView.as_view(), name='api_token_refresh'),
    path('api/auth/logout/', LogoutView.as_view(), name='api_logout'),
    path('api/auth/me/', MeView.as_view(), name='api_me'),
    path('api/auth/change-password/', ChangePasswordView.as_view(), name='api_change_password'),
    path('api/auth/register/', RegisterView.as_view(), name='api_register'),
    path('api/accounts/users/',               UserListView.as_view(),    name='api_user_list'),
    path('api/accounts/users/<int:pk>/',      UserDetailView.as_view(),  name='api_user_detail'),
    path('api/accounts/users/<int:pk>/approve/', UserApproveView.as_view(), name='api_user_approve'),
]
