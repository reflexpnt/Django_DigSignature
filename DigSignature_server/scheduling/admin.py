from django.contrib import admin
from .models import Schedule, Deployment, DeploymentLog

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'playlist', 'group', 'start_date', 'start_time', 
        'end_time', 'repeat_type', 'priority', 'is_active'
    )
    list_filter = ('repeat_type', 'is_active', 'group')
    search_fields = ('name', 'playlist__name', 'group__name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'group', 'playlist', 'status', 
        'progress_percentage', 'deploy_immediately', 
        'scheduled_deploy_time', 'created_at'
    )
    list_filter = ('status', 'deploy_immediately', 'group')
    search_fields = ('name', 'playlist__name', 'group__name')
    readonly_fields = (
        'created_at', 'started_at', 'completed_at', 
        'progress_percentage', 'total_players', 
        'completed_players', 'failed_players'
    )

@admin.register(DeploymentLog)
class DeploymentLogAdmin(admin.ModelAdmin):
    list_display = (
        'deployment', 'player', 'status', 
        'started_at', 'completed_at'
    )
    list_filter = ('status', 'deployment')
    search_fields = ('deployment__name', 'player__name')
    readonly_fields = ('started_at',)
