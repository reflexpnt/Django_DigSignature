from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Group, Player, SyncLog, DeviceLog

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'default_playlist', 'player_count', 'online_players',
        'sync_interval', 'resolution', 'orientation', 'audio_enabled'
    )
    list_filter = ('resolution', 'orientation', 'audio_enabled', 'tv_control')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Playlist Configuration', {
            'fields': ('default_playlist',)
        }),
        ('Display Settings', {
            'fields': ('resolution', 'orientation', 'audio_enabled')
        }),
        ('Sync Configuration', {
            'fields': ('sync_interval', 'screenshot_interval', 'tv_control')
        }),
        ('Location Settings', {
            'fields': ('default_timezone',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def online_players(self, obj):
        online = obj.online_player_count
        total = obj.player_count
        
        if total == 0:
            return "No players"
        
        percentage = int((online / total) * 100) if total > 0 else 0
        
        if percentage == 100:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{}/{} ({}%)</span>',
            color, online, total, percentage
        )
    
    online_players.short_description = 'Online Players'


class SyncLogInline(admin.TabularInline):
    model = SyncLog
    extra = 0
    readonly_fields = ('timestamp', 'status', 'duration_display', 'bytes_transferred_display')
    fields = ('timestamp', 'status', 'assets_synced', 'duration_display', 'bytes_transferred_display')
    ordering = ['-timestamp']
    
    def has_add_permission(self, request, obj=None):
        return False  # No permitir agregar logs manualmente


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'device_id', 'group', 'status_display', 'last_sync_display',
        'battery_display', 'signal_display', 'sync_failures', 'app_version'
    )
    list_filter = (
        'status', 'group', 'connection_type', 'custom_resolution', 
        'custom_orientation', 'firmware_version'
    )
    search_fields = ('name', 'device_id', 'location', 'notes')
    readonly_fields = (
        'device_id', 'created_at', 'updated_at', 'last_sync', 
        'last_sync_hash', 'status_display_detailed', 'health_summary'
    )
    
    fieldsets = (
        ('Device Information', {
            'fields': ('device_id', 'name', 'group')
        }),
        ('Status & Sync', {
            'fields': (
                'status', 'last_sync', 'last_sync_hash', 
                'sync_fail_count', 'status_display_detailed'
            )
        }),
        ('Device Details', {
            'fields': ('app_version', 'firmware_version')
        }),
        ('Custom Configuration', {
            'fields': ('custom_resolution', 'custom_orientation'),
            'classes': ('collapse',)
        }),
        ('Location & Time', {
            'fields': ('location', 'timezone'),
            'classes': ('collapse',)
        }),
        ('Health Information', {
            'fields': ('health_summary',),
            'classes': ('collapse',)
        }),
        ('Administration', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [SyncLogInline]
    
    actions = ['reset_sync_failures', 'force_offline', 'clear_sync_hash']
    
    def status_display(self, obj):
        """Status display for list view"""
        colors = {
            'online': 'green',
            'offline': 'gray',
            'error': 'red',
            'syncing': 'orange'
        }
        
        color = colors.get(obj.status, 'black')
        icon = {
            'online': '🟢',
            'offline': '⚫',
            'error': '🔴',
            'syncing': '🟡'
        }.get(obj.status, '❓')
        
        return format_html(
            '{} <span style="color: {};">{}</span>',
            icon, color, obj.get_status_display()
        )
    
    status_display.short_description = 'Status'
    
    def status_display_detailed(self, obj):
        """Detailed status for detail view"""
        minutes_ago = obj.last_seen_minutes_ago
        
        if obj.is_online:
            if minutes_ago is not None and minutes_ago < 10:
                return format_html('🟢 <strong>Online</strong> (last seen {} min ago)', minutes_ago)
            else:
                return format_html('🟢 <strong>Online</strong>')
        elif obj.is_recently_online:
            return format_html('🟡 <strong>Recently Online</strong> (last seen {} min ago)', minutes_ago or 'unknown')
        else:
            return format_html('🔴 <strong>Offline</strong> (last seen {} min ago)', minutes_ago or 'never')
    
    status_display_detailed.short_description = 'Detailed Status'
    
    def last_sync_display(self, obj):
        """Last sync display for list view"""
        if not obj.last_sync:
            return format_html('<span style="color: red;">Never</span>')
        
        minutes_ago = obj.last_seen_minutes_ago
        
        if minutes_ago < 10:
            return format_html('<span style="color: green;">{}m ago</span>', minutes_ago)
        elif minutes_ago < 60:
            return format_html('<span style="color: orange;">{}m ago</span>', minutes_ago)
        else:
            hours_ago = minutes_ago // 60
            return format_html('<span style="color: red;">{}h ago</span>', hours_ago)
    
    last_sync_display.short_description = 'Last Sync'
    
    def battery_display(self, obj):
        """Battery display for list view"""
        return obj.battery_status_display
    
    battery_display.short_description = 'Battery'
    
    def signal_display(self, obj):
        """Signal display for list view"""
        return obj.signal_status_display
    
    signal_display.short_description = 'Signal'
    
    def sync_failures(self, obj):
        """Sync failures display"""
        return obj.sync_status_display
    
    sync_failures.short_description = 'Sync Status'
    
    def health_summary(self, obj):
        """Health summary for detail view"""
        html = "<div style='font-family: monospace;'>"
        
        # ... código existente de health_summary ...
        
        # Agregar resumen de logs
        log_summary = obj.log_summary
        html += "<br><strong>Recent Logs (24h):</strong><br>"
        html += f"  Total: {log_summary['total']}<br>"
        
        if log_summary['errors'] > 0:
            html += f"  <span style='color: red;'>❌ Errors: {log_summary['errors']}</span><br>"
        
        if log_summary['warnings'] > 0:
            html += f"  <span style='color: orange;'>⚠️ Warnings: {log_summary['warnings']}</span><br>"
        
        if log_summary['total'] == 0:
            html += f"  <span style='color: gray;'>No recent logs</span><br>"
        elif log_summary['errors'] == 0 and log_summary['warnings'] == 0:
            html += f"  <span style='color: green;'>✅ No issues</span><br>"
        
        # Link to full logs
        html += f"<br><a href='/admin/players/devicelog/?player__id__exact={obj.id}' target='_blank'>📋 View Full Logs</a>"
        
        html += "</div>"
        return format_html(html)
    
    health_summary.short_description = 'Health & Logs Summary'
    
    # Admin Actions
    def reset_sync_failures(self, request, queryset):
        """Reset sync failure counter for selected players"""
        count = 0
        for player in queryset:
            player.reset_sync_failures()
            count += 1
        
        self.message_user(request, f'Reset sync failures for {count} players.')
    
    reset_sync_failures.short_description = 'Reset sync failures'
    
    def force_offline(self, request, queryset):
        """Force selected players offline"""
        count = queryset.update(status='offline')
        self.message_user(request, f'Set {count} players to offline.')
    
    force_offline.short_description = 'Force offline'
    
    def clear_sync_hash(self, request, queryset):
        """Clear sync hash to force full sync"""
        count = queryset.update(last_sync_hash='')
        self.message_user(request, f'Cleared sync hash for {count} players (will force full sync).')
    
    clear_sync_hash.short_description = 'Clear sync hash (force full sync)'


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp', 'player', 'status', 'assets_synced', 
        'duration_display', 'bytes_transferred_display'
    )
    list_filter = ('status', 'timestamp', 'player__group')
    search_fields = ('player__name', 'player__device_id', 'sync_id', 'error_message')
    readonly_fields = (
        'timestamp', 'duration_display', 'bytes_transferred_display', 'device_info_display'
    )
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('player', 'sync_id', 'timestamp', 'status')
        }),
        ('Sync Details', {
            'fields': (
                'assets_synced', 'duration_display', 'bytes_transferred_display', 
                'sync_hash'
            )
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Device Information', {
            'fields': ('device_info_display',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Los logs se crean automáticamente
    
    def has_change_permission(self, request, obj=None):
        return False  # Los logs no se pueden modificar
    
    def device_info_display(self, obj):
        """Display device info as formatted JSON"""
        if not obj.device_info:
            return "No device info"
        
        import json
        try:
            formatted = json.dumps(obj.device_info, indent=2)
            return format_html('<pre>{}</pre>', formatted)
        except:
            return str(obj.device_info)
    
    device_info_display.short_description = 'Device Information'





@admin.register(DeviceLog)
class DeviceLogAdmin(admin.ModelAdmin):
    list_display = (
        'device_timestamp', 'player', 'level_display', 'category_display', 
        'tag', 'short_message', 'has_exception_display'
    )
    list_filter = (
        'level', 'category', 'player__group', 'device_timestamp', 
        'player', 'tag', 'thread_name'
    )
    search_fields = (
        'player__name', 'player__device_id', 'tag', 'message', 
        'exception_class', 'method_name'
    )
    readonly_fields = (
        'timestamp', 'device_timestamp', 'level_display_detailed', 
        'category_display_detailed', 'formatted_stack_trace', 'extra_data_display'
    )
    date_hierarchy = 'device_timestamp'
    
    fieldsets = (
        ('Device & Timing', {
            'fields': ('player', 'device_timestamp', 'timestamp')
        }),
        ('Log Information', {
            'fields': (
                'level_display_detailed', 'category_display_detailed', 
                'tag', 'message'
            )
        }),
        ('Code Location', {
            'fields': ('thread_name', 'method_name', 'line_number'),
            'classes': ('collapse',)
        }),
        ('Exception Details', {
            'fields': ('exception_class', 'formatted_stack_trace'),
            'classes': ('collapse',)
        }),
        ('Device Context', {
            'fields': ('app_version', 'battery_level', 'memory_available_mb'),
            'classes': ('collapse',)
        }),
        ('Extra Data', {
            'fields': ('extra_data_display',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['delete_selected_logs', 'export_logs_csv']
    
    def has_add_permission(self, request):
        return False  # Los logs se crean via API
    
    def has_change_permission(self, request, obj=None):
        return False  # Los logs no se modifican
    
    def level_display(self, obj):
        """Level display for list view"""
        return format_html(
            '{} <span style="color: {}; font-weight: bold;">{}</span>',
            obj.level_icon, obj.level_color, obj.level
        )
    level_display.short_description = 'Level'
    
    def level_display_detailed(self, obj):
        """Detailed level display"""
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 14px;">{} {}</span>',
            obj.level_color, obj.level_icon, obj.level
        )
    level_display_detailed.short_description = 'Log Level'
    
    def category_display(self, obj):
        """Category display for list view"""
        return format_html(
            '{} {}',
            obj.category_icon, obj.category
        )
    category_display.short_description = 'Category'
    
    def category_display_detailed(self, obj):
        """Detailed category display"""
        return format_html(
            '<span style="font-size: 14px;">{} {}</span>',
            obj.category_icon, obj.category
        )
    category_display_detailed.short_description = 'Category'
    
    def has_exception_display(self, obj):
        """Exception indicator"""
        if obj.has_exception:
            return format_html('🚨 <span style="color: red;">Yes</span>')
        return '—'
    has_exception_display.short_description = 'Exception?'
    
    def formatted_stack_trace(self, obj):
        """Formatted stack trace display"""
        if not obj.stack_trace:
            return "No stack trace"
        
        return format_html(
            '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 12px; max-height: 300px; overflow-y: auto;">{}</pre>',
            obj.stack_trace
        )
    formatted_stack_trace.short_description = 'Stack Trace'
    
    def extra_data_display(self, obj):
        """Display extra data as formatted JSON"""
        if not obj.extra_data:
            return "No extra data"
        
        import json
        try:
            formatted = json.dumps(obj.extra_data, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 12px; max-height: 200px; overflow-y: auto;">{}</pre>',
                formatted
            )
        except:
            return str(obj.extra_data)
    extra_data_display.short_description = 'Extra Data'
    
    def delete_selected_logs(self, request, queryset):
        """Delete selected logs"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'Deleted {count} log entries.')
    delete_selected_logs.short_description = 'Delete selected logs'
    
    def export_logs_csv(self, request, queryset):
        """Export logs to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="device_logs.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Timestamp', 'Player', 'Level', 'Category', 'Tag', 
            'Message', 'Exception', 'Method', 'Line'
        ])
        
        for log in queryset:
            writer.writerow([
                log.device_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.player.name,
                log.level,
                log.category,
                log.tag,
                log.message,
                log.exception_class,
                log.method_name,
                log.line_number,
            ])
        
        return response
    export_logs_csv.short_description = 'Export to CSV'