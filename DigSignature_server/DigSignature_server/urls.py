# DigSignature_server/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),                    # Dashboard y configuración
    path('players/', include('players.urls')),         # Gestión de players y grupos
    path('content/', include('content.urls')),         # Gestión de assets y layouts  
    path('playlists/', include('playlists.urls')),     # Gestión de playlists
    path('scheduling/', include('scheduling.urls')),   # Programación y despliegues
]

# Servir archivos media y static en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)