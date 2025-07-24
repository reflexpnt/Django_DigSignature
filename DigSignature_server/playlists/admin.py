# admin.py para app `playlists`
from django.contrib import admin
from .models import Playlist, PlaylistItem

class PlaylistItemInline(admin.TabularInline):
    model = PlaylistItem
    extra = 0
    readonly_fields = ('created_at',)
    ordering = ['order']

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'layout', 'is_advertisement', 'item_count', 'total_duration')
    search_fields = ('name',)
    list_filter = ('is_advertisement', 'shuffle_enabled', 'repeat_enabled')
    inlines = [PlaylistItemInline]
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PlaylistItem)
class PlaylistItemAdmin(admin.ModelAdmin):
    list_display = ('playlist', 'asset', 'zone', 'duration', 'order', 'transition_effect', 'fullscreen')
    list_filter = ('playlist', 'zone', 'transition_effect', 'fullscreen')
    search_fields = ('playlist__name', 'asset__name')
    ordering = ['playlist', 'order']
