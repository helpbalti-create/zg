from django.urls import path
from . import api_views

urlpatterns = [
    path('persons/',                    api_views.PersonListView.as_view()),
    path('persons/<int:pk>/',           api_views.PersonDetailView.as_view()),
    path('families/',                   api_views.FamilyListView.as_view()),
    path('families/<int:pk>/',          api_views.FamilyDetailView.as_view()),
    path('members/',                    api_views.MemberCreateView.as_view()),
    path('members/<int:pk>/',           api_views.MemberDeleteView.as_view()),
    path('relationships/',              api_views.RelationshipCreateView.as_view()),
    path('relationships/<int:pk>/',     api_views.RelationshipDeleteView.as_view()),
    path('field-categories/',           api_views.FieldCategoryListView.as_view()),
]
