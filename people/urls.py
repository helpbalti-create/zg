from django.urls import path
from . import views

app_name = 'people'

urlpatterns = [
    # Dashboard
    path('',                              views.dashboard,             name='dashboard'),

    # People
    path('people/',                       views.person_list,           name='person_list'),
    path('people/add/',                   views.person_create,         name='person_create'),
    path('people/<int:pk>/',              views.person_detail,         name='person_detail'),
    path('people/<int:pk>/edit/',         views.person_edit,           name='person_edit'),
    path('people/<int:pk>/delete/',       views.person_delete,         name='person_delete'),

    # Relationships
    path('people/<int:pk>/link/',         views.person_add_relationship, name='person_add_relationship'),
    path('relationship/<int:pk>/delete/', views.relationship_delete,   name='relationship_delete'),

    # Families
    path('families/',                     views.family_list,           name='family_list'),
    path('families/add/',                 views.family_create,         name='family_create'),
    path('families/<int:pk>/',            views.family_detail,         name='family_detail'),
    path('families/<int:pk>/edit/',       views.family_edit,           name='family_edit'),
    path('families/<int:pk>/delete/',     views.family_delete,         name='family_delete'),
    path('families/<int:pk>/add-member/', views.family_add_member,     name='family_add_member'),
    path('families/<int:family_pk>/remove/<int:person_pk>/',
                                          views.family_remove_member,  name='family_remove_member'),
]
