# scheduling/urls.py - URLs para las APIs de sincronización
from django.urls import path
from . import views

urlpatterns = [
    # API v1 para dispositivos Android - equivalente al WebSocket del original
    path('api/v1/device/check_server/', views.device_check_server, name='device_check_server'),
    path('api/v1/device/sync_confirmation/', views.device_sync_confirmation, name='device_sync_confirmation'),
    path('api/v1/device/emergency_ack/', views.emergency_message_acknowledgment, name='emergency_message_acknowledgment'),
    
    # APIs para descarga de assets - equivalente al sistema de archivos del original
    path('api/v1/assets/<int:asset_id>/download/', views.asset_download, name='asset_download'),
    path('api/v1/assets/<int:asset_id>/thumbnail/', views.asset_thumbnail, name='asset_thumbnail'),
]