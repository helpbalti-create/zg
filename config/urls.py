from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.urls import api_urlpatterns as auth_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oauth/', include('allauth.urls')),              # Google/GitHub OAuth
    path('accounts/', include('accounts.urls')),
    path('', include('core.urls')),
    path('', include('budget.urls')),
    path('people/', include('people.urls')),

    # ── REST API для Vue фронтенда ──────────────────────────────────────────
    *auth_api,                                          # /api/auth/...
    path('api/budget/',   include('budget.api_urls')),  # /api/budget/...
    path('api/people/',   include('people.api_urls')),  # /api/people/...
    path('api/accounts/', include('accounts.api_urls_admin')),  # /api/accounts/...
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
