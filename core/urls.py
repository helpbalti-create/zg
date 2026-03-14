from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    # Старый алиас portal — на случай если где-то ещё есть ссылки
    path('portal/', views.home, name='portal'),
]
