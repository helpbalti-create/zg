from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('new/', views.project_create, name='project_create'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('<int:pk>/complete/', views.project_complete, name='project_complete'),
    path('<int:project_pk>/export/', views.export_excel, name='export_excel'),

    path('<int:project_pk>/sections/new/', views.section_create, name='section_create'),
    path('sections/<int:pk>/edit/', views.section_edit, name='section_edit'),

    path('<int:project_pk>/categories/new/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),

    path('<int:project_pk>/expenses/add/', views.expense_add, name='expense_add'),
    path('expenses/<int:pk>/', views.expense_detail, name='expense_detail'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),

    path('<int:project_pk>/corrections/add/', views.correction_add, name='correction_add'),
    path('<int:project_pk>/import-expenses/', views.import_expenses_preview, name='import_expenses'),
    path('import/', views.full_import, name='full_import'),
]