from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from accounts.urls import api_urlpatterns
from two_factor.urls import urlpatterns as tf_urls
from admin_site import admin_site  # кастомный AdminSite

urlpatterns = [
    # Кастомный AdminSite вместо стандартного
    path('admin/', admin_site.urls),

    # Портал — главная страница
    path('', include('core.urls', namespace='core')),

    # Web auth (session-based + 2FA)
    path('accounts/', include('accounts.urls')),

    # Two-factor auth UI
    path('', include(tf_urls)),

    # Social OAuth2
    path('oauth/signup/', RedirectView.as_view(pattern_name='register', permanent=False)),
    path('oauth/', include('allauth.urls')),

    # Budget module
    path('budget/', include('budget.urls')),

    path('people/', include('people.urls', namespace='people')),
] + api_urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
