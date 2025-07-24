from django.urls import path
from . import views

urlpatterns = [
    # Gestión de horarios
    path('', views.schedules_list, name='schedules_list'),
    path('create/', views.schedule_create, name='schedule_create'),
    path('<int:pk>/', views.schedule_detail, name='schedule_detail'),
    path('<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),
    
    # Calendario de programación
    path('calendar/', views.schedule_calendar, name='schedule_calendar'),
    path('calendar/month/<int:year>/<int:month>/', views.schedule_calendar_month, name='schedule_calendar_month'),
    
    # Gestión de despliegues
    path('deployments/', views.deployments_list, name='deployments_list'),
    path('deployments/<int:pk>/', views.deployment_detail, name='deployment_detail'),
    path('deployments/<int:pk>/cancel/', views.deployment_cancel, name='deployment_cancel'),
    
    # Despliegue masivo
    path('deploy/', views.mass_deploy, name='mass_deploy'),
    path('deploy/groups/', views.deploy_to_groups, name='deploy_to_groups'),
    
    # API endpoints para HTMX
    path('api/deployments/<int:pk>/progress/', views.deployment_progress, name='deployment_progress'),
    path('api/schedule/conflicts/', views.check_schedule_conflicts, name='check_schedule_conflicts'),
]