from django.contrib import admin
from .models import Group, Player

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'default_playlist', 'sync_interval', 'resolution', 'orientation', 'audio_enabled')
    search_fields = ('name',)
    list_filter = ('resolution', 'orientation', 'audio_enabled')

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'device_id', 'group', 'status', 'last_seen', 'ip_address')
    search_fields = ('name', 'device_id', 'mac_address')
    list_filter = ('status', 'group')
    readonly_fields = ('last_seen', 'last_sync', 'created_at', 'updated_at')