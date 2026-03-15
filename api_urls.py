from django.urls import path, include

urlpatterns = [
    path('auth/',     include('accounts.api_urls')),
    path('budget/',   include('budget.api_urls')),
    path('people/',   include('people.api_urls')),
    path('accounts/', include('accounts.api_urls_admin')),
]
