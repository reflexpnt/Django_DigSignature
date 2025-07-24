from django.contrib import admin
from .models import Label, Layout, Asset

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'description')
    search_fields = ('name',)
    ordering = ['name']

@admin.register(Layout)
class LayoutAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_custom', 'zone_count', 'preview_image_display')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    def preview_image_display(self, obj):
        if obj.preview_image:
            return f'<img src="{obj.preview_image.url}" style="height: 50px;" />'
        return '-'
    preview_image_display.allow_tags = True
    preview_image_display.short_description = 'Preview'

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'asset_type', 'status', 
        'file_size_human', 'duration_human', 
        'resolution', 'version', 'created_at'
    )
    list_filter = ('asset_type', 'status', 'labels')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'file_size_human', 'duration_human')
    filter_horizontal = ('labels',)
