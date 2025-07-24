from django.urls import path
from . import views

urlpatterns = [
    # Gestión de assets
    path('assets/', views.assets_list, name='assets_list'),
    path('assets/upload/', views.asset_upload, name='asset_upload'),
    path('assets/add-link/', views.asset_add_link, name='asset_add_link'),
    path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/<int:pk>/edit/', views.asset_edit, name='asset_edit'),
    path('assets/<int:pk>/delete/', views.asset_delete, name='asset_delete'),
    path('assets/<int:pk>/download/', views.asset_download, name='asset_download'),
    
    # Gestión de labels
    path('labels/', views.labels_list, name='labels_list'),
    path('labels/create/', views.label_create, name='label_create'),
    path('labels/<int:pk>/edit/', views.label_edit, name='label_edit'),
    path('labels/<int:pk>/delete/', views.label_delete, name='label_delete'),
    
    # Gestión de layouts
    path('layouts/', views.layouts_list, name='layouts_list'),
    path('layouts/create/', views.layout_create, name='layout_create'),
    path('layouts/<int:pk>/', views.layout_detail, name='layout_detail'),
    path('layouts/<int:pk>/edit/', views.layout_edit, name='layout_edit'),
    path('layouts/<int:pk>/delete/', views.layout_delete, name='layout_delete'),
    
    # API endpoints para HTMX
    path('api/assets/progress/<str:upload_id>/', views.upload_progress, name='upload_progress'),
]