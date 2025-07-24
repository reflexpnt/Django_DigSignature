from django.urls import path
from . import views

urlpatterns = [
    # Gestión de playlists
    path('', views.playlists_list, name='playlists_list'),
    path('create/', views.playlist_create, name='playlist_create'),
    path('<int:pk>/', views.playlist_detail, name='playlist_detail'),
    path('<int:pk>/edit/', views.playlist_edit, name='playlist_edit'),
    path('<int:pk>/delete/', views.playlist_delete, name='playlist_delete'),
    path('<int:pk>/duplicate/', views.playlist_duplicate, name='playlist_duplicate'),
    
    # Acciones de playlists
    path('<int:pk>/deploy/', views.playlist_deploy, name='playlist_deploy'),
    path('<int:pk>/preview/', views.playlist_preview, name='playlist_preview'),
    
    # Gestión de items de playlist
    path('<int:playlist_pk>/items/add/', views.playlist_item_add, name='playlist_item_add'),
    path('<int:playlist_pk>/items/<int:item_pk>/edit/', views.playlist_item_edit, name='playlist_item_edit'),
    path('<int:playlist_pk>/items/<int:item_pk>/delete/', views.playlist_item_delete, name='playlist_item_delete'),
    path('<int:playlist_pk>/items/reorder/', views.playlist_items_reorder, name='playlist_items_reorder'),
    
    # API endpoints para builder
    path('api/<int:pk>/assets/', views.playlist_available_assets, name='playlist_available_assets'),
]