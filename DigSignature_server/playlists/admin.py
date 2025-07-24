# playlists/admin.py - Admin interface basada en la funcionalidad del original
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponse
from .models import Playlist, PlaylistItem, PlaylistSchedule, PlaylistStats

class PlaylistItemInline(admin.TabularInline):
    model = PlaylistItem
    extra = 0
    readonly_fields = ('effective_duration', 'is_currently_valid', 'created_at')
    ordering = ['zone', 'order']
    
    fieldsets = (
        (None, {
            'fields': (
                'asset', 'zone', 'order', 'duration', 'effective_duration',
                'fullscreen', 'transition_effect'
            )
        }),
    )
    
    def effective_duration(self, obj):
        duration = obj.effective_duration
        if obj.asset.is_video() and obj.asset.duration:
            return format_html(
                '<span style="color: #28a745;">{} (video)</span>',
                obj.asset.duration_human
            )
        return f"{duration}s"
    effective_duration.short_description = 'Effective Duration'
    
    def is_currently_valid(self, obj):
        if obj.is_currently_valid:
            return format_html('<span style="color: #28a745;">✓ Valid</span>')
        else:
            return format_html('<span style="color: #dc3545;">✗ Invalid</span>')
    is_currently_valid.short_description = 'Valid Now'

class PlaylistScheduleInline(admin.TabularInline):
    model = PlaylistSchedule
    extra = 0
    readonly_fields = ('is_active_now',)
    
    def is_active_now(self, obj):
        if obj.is_active_now():
            return format_html('<span style="color: #28a745;">🟢 Active</span>')
        else:
            return format_html('<span style="color: #6c757d;">⚫ Inactive</span>')
    is_active_now.short_description = 'Active Now'

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'layout', 'item_count', 'total_duration_display', 
        'is_advertisement', 'ticker_status', 'groups_using', 'created_at'
    )
    list_filter = ('is_advertisement', 'shuffle_enabled', 'repeat_enabled', 'ticker_enabled', 'layout')
    search_fields = ('name', 'description')
    readonly_fields = (
        'item_count', 'total_duration', 'created_at', 'updated_at', 
        'sync_hash', 'asset_count_by_zone_display'
    )
    inlines = [PlaylistItemInline, PlaylistScheduleInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'layout')
        }),
        ('Playlist Configuration', {
            'fields': ('is_advertisement', 'ad_interval', 'shuffle_enabled', 'repeat_enabled', 'merge_alternate_assets')
        }),
        ('Ticker Configuration', {
            'fields': ('ticker_enabled', 'ticker_text', 'ticker_speed', 'ticker_position'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('item_count', 'total_duration', 'asset_count_by_zone_display'),
            'classes': ('collapse',)
        }),
        ('Synchronization', {
            'fields': ('sync_hash',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['duplicate_playlists', 'deploy_to_groups', 'calculate_sync_hashes']
    
    def total_duration_display(self, obj):
        duration = obj.total_duration
        if duration == 0:
            return '—'
        
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    total_duration_display.short_description = 'Duration'
    
    def ticker_status(self, obj):
        if obj.ticker_enabled:
            return format_html(
                '<span style="color: #28a745;">🎯 Enabled</span>'
            )
        return format_html('<span style="color: #6c757d;">⚫ Disabled</span>')
    ticker_status.short_description = 'Ticker'
    
    def groups_using(self, obj):
        # Groups usando esta playlist como default
        default_groups = obj.default_for_groups.all()
        # Groups con schedules de esta playlist
        scheduled_groups = set()
        for schedule in obj.schedules.all():
            scheduled_groups.add(schedule.group)
        
        all_groups = set(default_groups) | scheduled_groups
        
        if not all_groups:
            return '—'
        
        html = ''
        for group in list(all_groups)[:3]:  # Mostrar máximo 3
            color = '#28a745' if group in default_groups else '#17a2b8'
            html += format_html(
                '<span style="background-color: {}; color: white; padding: 1px 4px; border-radius: 2px; font-size: 11px; margin-right: 2px;">{}</span>',
                color, group.name
            )
        
        remaining = len(all_groups) - 3
        if remaining > 0:
            html += f' +{remaining}'
        
        return format_html(html)
    groups_using.short_description = 'Used by Groups'
    
    def sync_hash(self, obj):
        hash_value = obj.get_sync_hash()
        return format_html(
            '<code style="background: #f8f9fa; padding: 2px 6px; border-radius: 3px;">{}</code>',
            hash_value[:16] + '...'
        )
    sync_hash.short_description = 'Sync Hash'
    
    def asset_count_by_zone_display(self, obj):
        zone_counts = obj.asset_count_by_zone
        if not zone_counts:
            return 'No assets'
        
        html = '<div style="font-family: monospace;">'
        for zone, count in zone_counts.items():
            html += f'<strong>{zone}:</strong> {count} assets<br>'
        html += '</div>'
        
        return format_html(html)
    asset_count_by_zone_display.short_description = 'Assets by Zone'
    
    def duplicate_playlists(self, request, queryset):
        """Duplicar playlists seleccionadas"""
        count = 0
        for playlist in queryset:
            # Crear copia de la playlist
            new_playlist = Playlist.objects.create(
                name=f"{playlist.name} (Copy)",
                description=playlist.description,
                layout=playlist.layout,
                is_advertisement=playlist.is_advertisement,
                ad_interval=playlist.ad_interval,
                ticker_enabled=playlist.ticker_enabled,
                ticker_text=playlist.ticker_text,
                ticker_speed=playlist.ticker_speed,
                ticker_position=playlist.ticker_position,
                shuffle_enabled=playlist.shuffle_enabled,
                repeat_enabled=playlist.repeat_enabled,
                merge_alternate_assets=playlist.merge_alternate_assets
            )
            
            # Copiar items
            for item in playlist.items.all():
                PlaylistItem.objects.create(
                    playlist=new_playlist,
                    asset=item.asset,
                    duration=item.duration,
                    zone=item.zone,
                    order=item.order,
                    fullscreen=item.fullscreen,
                    transition_effect=item.transition_effect,
                    asset_ticker=item.asset_ticker,
                    valid_from=item.valid_from,
                    valid_until=item.valid_until
                )
            
            count += 1
        
        self.message_user(request, f'Duplicated {count} playlists successfully.')
    duplicate_playlists.short_description = 'Duplicate selected playlists'
    
    def deploy_to_groups(self, request, queryset):
        """Crear deployment para grupos que usan estas playlists"""
        from scheduling.models import Deployment
        
        # Obtener todos los grupos que usan estas playlists
        groups_to_deploy = set()
        for playlist in queryset:
            for group in playlist.default_for_groups.all():
                groups_to_deploy.add(group)
            for schedule in playlist.schedules.all():
                groups_to_deploy.add(schedule.group)
        
        # Crear deployments
        count = 0
        for group in groups_to_deploy:
            deployment = Deployment.objects.create(
                name=f"Manual deployment to {group.name}",
                group=group,
                created_by=request.user.username if hasattr(request.user, 'username') else 'admin'
            )
            deployment.playlists.set(queryset)
            count += 1
        
        self.message_user(request, f'Created {count} deployments for selected playlists.')
    deploy_to_groups.short_description = 'Deploy to groups using these playlists'
    
    def calculate_sync_hashes(self, request, queryset):
        """Recalcular sync hashes"""
        count = 0
        for playlist in queryset:
            # Forzar recálculo del hash
            hash_value = playlist.get_sync_hash()
            count += 1
        
        self.message_user(request, f'Recalculated sync hashes for {count} playlists.')
    calculate_sync_hashes.short_description = 'Recalculate sync hashes'

@admin.register(PlaylistItem)
class PlaylistItemAdmin(admin.ModelAdmin):
    list_display = (
        'playlist', 'asset', 'zone', 'order', 'duration', 'effective_duration_display',
        'transition_effect', 'is_currently_valid_display'
    )
    list_filter = ('zone', 'transition_effect', 'fullscreen', 'playlist__layout')
    search_fields = ('playlist__name', 'asset__name')
    readonly_fields = ('effective_duration', 'created_at')
    
    fieldsets = (
        ('Assignment', {
            'fields': ('playlist', 'asset', 'zone', 'order')
        }),
        ('Display Configuration', {
            'fields': ('duration', 'effective_duration', 'fullscreen', 'transition_effect')
        }),
        ('Advanced', {
            'fields': ('asset_ticker', 'valid_from', 'valid_until'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def effective_duration_display(self, obj):
        duration = obj.effective_duration
        if obj.asset.is_video() and obj.asset.duration:
            return format_html(
                '<span style="color: #28a745;" title="Video duration used">{}</span>',
                obj.asset.duration_human
            )
        return f"{duration}s"
    effective_duration_display.short_description = 'Effective Duration'
    
    def is_currently_valid_display(self, obj):
        if obj.is_currently_valid:
            return format_html('<span style="color: #28a745;">✓</span>')
        else:
            return format_html('<span style="color: #dc3545;">✗</span>')
    is_currently_valid_display.short_description = 'Valid'

@admin.register(PlaylistSchedule)
class PlaylistScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'playlist', 'group', 'schedule_display', 'days_display', 
        'priority', 'is_active', 'is_active_now_display'
    )
    list_filter = ('is_active', 'priority', 'days_of_week')
    search_fields = ('playlist__name', 'group__name')
    readonly_fields = ('created_at', 'updated_at', 'is_active_now_display')
    
    fieldsets = (
        ('Assignment', {
            'fields': ('playlist', 'group', 'priority', 'is_active')
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time', 'days_of_week')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active_now_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def schedule_display(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    schedule_display.short_description = 'Schedule'
    
    def days_display(self, obj):
        if not obj.days_of_week:
            return 'No days set'
        
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        days = [day_names[day-1] for day in sorted(obj.days_of_week) if 1 <= day <= 7]
        return ', '.join(days)
    days_display.short_description = 'Days'
    
    def is_active_now_display(self, obj):
        if obj.is_active_now():
            return format_html('<span style="color: #28a745;">🟢 Active Now</span>')
        else:
            return format_html('<span style="color: #6c757d;">⚫ Not Active</span>')
    is_active_now_display.short_description = 'Current Status'

@admin.register(PlaylistStats)
class PlaylistStatsAdmin(admin.ModelAdmin):
    list_display = (
        'playlist', 'player', 'played_at', 'duration_played_display', 
        'completed', 'items_played', 'errors_count'
    )
    list_filter = ('completed', 'played_at', 'playlist', 'player__group')
    search_fields = ('playlist__name', 'player__name')
    readonly_fields = ('played_at', 'duration_played_display')
    date_hierarchy = 'played_at'
    
    fieldsets = (
        ('Playback Info', {
            'fields': ('playlist', 'player', 'played_at')
        }),
        ('Statistics', {
            'fields': ('duration_played', 'duration_played_display', 'completed', 'items_played', 'errors_count')
        }),
    )
    
    def duration_played_display(self, obj):
        duration = obj.duration_played
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    duration_played_display.short_description = 'Duration Played'
    
    def has_add_permission(self, request):
        return False  # Stats are created by the system
    
    def has_change_permission(self, request, obj=None):
        return False  # Stats shouldn't be modified