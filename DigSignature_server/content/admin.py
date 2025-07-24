# content/admin.py - Admin interface basada en la funcionalidad del original
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http import HttpResponse
from .models import Label, Layout, Asset, AssetConversion

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_display', 'description', 'asset_count')
    search_fields = ('name', 'description')
    ordering = ['name']
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; border-radius: 3px; color: white;">{}</span>',
            obj.color, obj.name
        )
    color_display.short_description = 'Color'
    
    def asset_count(self, obj):
        count = obj.asset_set.count()
        if count > 0:
            url = reverse('admin:content_asset_changelist') + f'?labels__id__exact={obj.id}'
            return format_html('<a href="{}">{} assets</a>', url, count)
        return '0 assets'
    asset_count.short_description = 'Assets'

@admin.register(Layout)
class LayoutAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'zone_count', 'is_custom', 'preview_display', 'playlist_count')
    list_filter = ('is_custom',)
    search_fields = ('name', 'code')
    readonly_fields = ('created_at', 'updated_at', 'zones_preview')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description')
        }),
        ('Configuration', {
            'fields': ('zones_config', 'zones_preview', 'is_custom')
        }),
        ('Custom Layout', {
            'fields': ('custom_html',),
            'classes': ('collapse',),
            'description': 'Only for custom layouts'
        }),
        ('Preview', {
            'fields': ('preview_image',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def preview_display(self, obj):
        if obj.preview_image:
            return format_html(
                '<img src="{}" style="height: 50px; border: 1px solid #ddd;" />',
                obj.preview_image.url
            )
        return '—'
    preview_display.short_description = 'Preview'
    
    def zones_preview(self, obj):
        if not obj.zones_config:
            return 'No zones configured'
        
        html = '<div style="font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 4px;">'
        for zone, config in obj.zones_config.items():
            html += f'<strong>{zone}:</strong> {config.get("width", 0)}% × {config.get("height", 0)}%<br>'
        html += '</div>'
        
        return format_html(html)
    zones_preview.short_description = 'Zones Configuration'
    
    def playlist_count(self, obj):
        count = obj.playlist_set.count()
        if count > 0:
            url = reverse('admin:playlists_playlist_changelist') + f'?layout__id__exact={obj.id}'
            return format_html('<a href="{}">{} playlists</a>', url, count)
        return '0 playlists'
    playlist_count.short_description = 'Playlists'
    
    actions = ['create_default_layouts']
    
    def create_default_layouts(self, request, queryset):
        """Crear layouts por defecto basados en el original"""
        Layout.get_default_layouts()
        self.message_user(request, 'Default layouts created successfully.')
    create_default_layouts.short_description = 'Create default layouts'

class AssetConversionInline(admin.TabularInline):
    model = AssetConversion
    extra = 0
    readonly_fields = ('status', 'conversion_type', 'started_at', 'completed_at', 'error_message')
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'asset_type', 'status_display', 'file_size_display', 
        'duration_display', 'resolution', 'thumbnail_display', 'labels_display', 'created_at'
    )
    list_filter = ('asset_type', 'status', 'labels', 'created_at')
    search_fields = ('name', 'original_name', 'description')
    readonly_fields = (
        'original_name', 'file_size', 'checksum', 'created_at', 'updated_at', 
        'file_info_display', 'metadata_display'
    )
    filter_horizontal = ('labels',)
    inlines = [AssetConversionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'original_name', 'asset_type', 'status', 'description')
        }),
        ('File Information', {
            'fields': ('file', 'url', 'thumbnail', 'file_info_display')
        }),
        ('Metadata', {
            'fields': ('file_size', 'duration', 'resolution', 'checksum', 'metadata_display'),
            'classes': ('collapse',)
        }),
        ('Organization', {
            'fields': ('labels', 'version')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['regenerate_thumbnails', 'recalculate_checksums', 'convert_videos']
    
    def status_display(self, obj):
        colors = {
            'uploading': '#ffc107',
            'processing': '#17a2b8', 
            'ready': '#28a745',
            'error': '#dc3545'
        }
        
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def file_size_display(self, obj):
        return obj.file_size_human
    file_size_display.short_description = 'Size'
    
    def duration_display(self, obj):
        return obj.duration_human or '—'
    duration_display.short_description = 'Duration'
    
    def thumbnail_display(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="height: 40px; border: 1px solid #ddd;" />',
                obj.thumbnail.url
            )
        elif obj.is_image() and obj.file:
            return format_html(
                '<img src="{}" style="height: 40px; border: 1px solid #ddd;" />',
                obj.file.url
            )
        return '—'
    thumbnail_display.short_description = 'Thumbnail'
    
    def labels_display(self, obj):
        labels = obj.labels.all()[:3]  # Mostrar máximo 3 labels
        if not labels:
            return '—'
        
        html = ''
        for label in labels:
            html += format_html(
                '<span style="background-color: {}; color: white; padding: 1px 6px; border-radius: 3px; font-size: 11px; margin-right: 2px;">{}</span>',
                label.color, label.name
            )
        
        remaining = obj.labels.count() - len(labels)
        if remaining > 0:
            html += f' +{remaining} more'
        
        return format_html(html)
    labels_display.short_description = 'Labels'
    
    def file_info_display(self, obj):
        if not obj.file:
            return 'No file'
        
        html = f'<div style="font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 4px;">'
        html += f'<strong>File:</strong> {obj.file.name}<br>'
        html += f'<strong>Size:</strong> {obj.file_size_human}<br>'
        html += f'<strong>URL:</strong> <a href="{obj.file.url}" target="_blank">View/Download</a><br>'
        
        if obj.checksum:
            html += f'<strong>Checksum:</strong> {obj.checksum[:16]}...<br>'
        
        if obj.needs_conversion():
            html += '<strong style="color: #ffc107;">⚠️ Needs conversion to MP4</strong><br>'
        
        html += '</div>'
        return format_html(html)
    file_info_display.short_description = 'File Information'
    
    def metadata_display(self, obj):
        if not obj.metadata:
            return 'No metadata'
        
        html = '<div style="font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 4px;">'
        for key, value in obj.metadata.items():
            html += f'<strong>{key}:</strong> {value}<br>'
        html += '</div>'
        
        return format_html(html)
    metadata_display.short_description = 'Metadata'
    
    def regenerate_thumbnails(self, request, queryset):
        """Regenerar thumbnails para assets seleccionados"""
        count = 0
        for asset in queryset:
            if asset.is_video() or asset.is_image():
                # TODO: Implementar generación de thumbnails
                count += 1
        
        self.message_user(request, f'Queued {count} assets for thumbnail regeneration.')
    regenerate_thumbnails.short_description = 'Regenerate thumbnails'
    
    def recalculate_checksums(self, request, queryset):
        """Recalcular checksums"""
        count = 0
        for asset in queryset.filter(file__isnull=False):
            asset.checksum = asset.calculate_checksum()
            asset.save(update_fields=['checksum'])
            count += 1
        
        self.message_user(request, f'Recalculated checksums for {count} assets.')
    recalculate_checksums.short_description = 'Recalculate checksums'
    
    def convert_videos(self, request, queryset):
        """Convertir videos a MP4"""
        count = 0
        for asset in queryset.filter(asset_type='video'):
            if asset.needs_conversion():
                # TODO: Queue for conversion
                AssetConversion.objects.create(
                    asset=asset,
                    conversion_type='video_mp4',
                    status='pending'
                )
                count += 1
        
        self.message_user(request, f'Queued {count} videos for MP4 conversion.')
    convert_videos.short_description = 'Convert videos to MP4'

@admin.register(AssetConversion)
class AssetConversionAdmin(admin.ModelAdmin):
    list_display = ('asset', 'conversion_type', 'status', 'started_at', 'duration_display')
    list_filter = ('conversion_type', 'status', 'started_at')
    search_fields = ('asset__name',)
    readonly_fields = ('started_at', 'completed_at', 'duration_display')
    
    fieldsets = (
        ('Conversion Info', {
            'fields': ('asset', 'conversion_type', 'status')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_display')
        }),
        ('Error Details', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def duration_display(self, obj):
        if obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return f"{duration.total_seconds():.1f}s"
        elif obj.started_at:
            from django.utils import timezone
            duration = timezone.now() - obj.started_at
            return f"{duration.total_seconds():.1f}s (ongoing)"
        return '—'
    duration_display.short_description = 'Duration'
    
    def has_add_permission(self, request):
        return False  # Conversions are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Conversions shouldn't be modified manually