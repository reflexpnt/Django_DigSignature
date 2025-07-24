# admin.py para app `core` o `system`
from django.contrib import admin
from .models import SystemSettings, ActivityLog

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ("Identificación", {
            'fields': ('installation_name',)
        }),
        ("Upload", {
            'fields': ('max_file_size_mb', 'allowed_file_types'),
        }),
        ("Conversión", {
            'fields': ('auto_convert_videos', 'video_quality', 'generate_thumbnails'),
        }),
        ("Sincronización", {
            'fields': ('default_sync_interval',),
        }),
        ("Servidor", {
            'fields': ('server_name', 'server_port'),
        }),
        ("Tiempos", {
            'fields': ('created_at', 'updated_at'),
        }),
    )

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_repr')
    search_fields = ('user', 'model_name', 'object_repr', 'details')
    list_filter = ('action', 'timestamp')
    readonly_fields = [f.name for f in ActivityLog._meta.fields]
