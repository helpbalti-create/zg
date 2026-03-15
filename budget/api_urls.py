from django.urls import path
from . import api_views

urlpatterns = [
    path('projects/',                          api_views.ProjectListView.as_view()),
    path('projects/<int:pk>/',                 api_views.ProjectDetailView.as_view()),
    path('projects/<int:pk>/expenses/',        api_views.ProjectExpensesView.as_view()),
    path('projects/<int:pk>/corrections/',     api_views.ProjectCorrectionsView.as_view()),
    path('projects/<int:pk>/export/',          api_views.ExportExcelView.as_view()),
    path('projects/<int:pk>/complete/',        api_views.ProjectCompleteView.as_view()),
    path('expenses/',                          api_views.ExpenseCreateView.as_view()),
    path('expenses/<int:pk>/',                 api_views.ExpenseDetailView.as_view()),
    path('categories/',                        api_views.CategoryCreateView.as_view()),
    path('categories/<int:pk>/',               api_views.CategoryDetailView.as_view()),
    path('corrections/',                       api_views.CorrectionCreateView.as_view()),
]
