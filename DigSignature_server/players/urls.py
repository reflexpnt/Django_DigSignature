from django.urls import path
from . import views

urlpatterns = [
    # Lista y gestión de players
    path('', views.players_list, name='players_list'),
    path('register/', views.player_register, name='player_register'),
    path('<int:pk>/', views.player_detail, name='player_detail'),
    path('<int:pk>/edit/', views.player_edit, name='player_edit'),
    path('<int:pk>/delete/', views.player_delete, name='player_delete'),
    
    # Acciones de players
    path('<int:pk>/sync/', views.player_sync, name='player_sync'),
    path('<int:pk>/screenshot/', views.player_screenshot, name='player_screenshot'),
    
    # Gestión de grupos
    path('groups/', views.groups_list, name='groups_list'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    path('groups/<int:pk>/edit/', views.group_edit, name='group_edit'),
    path('groups/<int:pk>/delete/', views.group_delete, name='group_delete'),
    path('groups/<int:pk>/deploy/', views.group_deploy, name='group_deploy'),
]