# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),
    
    # Configuración del sistema
    path('settings/', views.settings_view, name='settings_view'),  # ✅ Agregado
    
    # Log de actividades
    path('activity-log/', views.activity_log, name='activity_log'),  # ✅ Agregado
    
    # API endpoints para HTMX (actualizaciones en tiempo real)
    path('api/dashboard/players-status/', views.dashboard_players_status, name='dashboard_players_status'),
    path('api/system/health/', views.system_health, name='system_health'),
]