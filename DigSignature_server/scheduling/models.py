# scheduling/models.py - Sistema de programación y despliegue basado en el original
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import hashlib
import json

class Deployment(models.Model):
    """Despliegues de contenido a grupos - funcionalidad central del original"""
    DEPLOYMENT_STATUS = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'), 
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200, help_text="Deployment name/description")
    group = models.ForeignKey('players.Group', on_delete=models.CASCADE, related_name='deployments')
    
    # Playlists a desplegar
    playlists = models.ManyToManyField('playlists.Playlist', related_name='deployments')
    
    # Estado del despliegue
    status = models.CharField(max_length=20, choices=DEPLOYMENT_STATUS, default='pending')
    
    # Programación
    scheduled_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When to deploy (null = deploy immediately)"
    )
    deployed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Configuraciones del despliegue
    force_sync = models.BooleanField(
        default=False, 
        help_text="Force full sync even if no changes detected"
    )
    restart_players = models.BooleanField(
        default=False,
        help_text="Restart players after deployment"
    )
    
    # Resultados
    success_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    # Tracking
    created_by = models.CharField(max_length=100, default='system')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Deployment"
        verbose_name_plural = "Deployments"
    
    def __str__(self):
        return f"{self.name} -> {self.group.name} ({self.status})"
    
    def can_execute(self):
        """Verificar si el deployment puede ejecutarse"""
        if self.status not in ['pending']:
            return False
        
        if self.scheduled_at and timezone.now() < self.scheduled_at:
            return False
        
        return True
    
    def start_deployment(self):
        """Iniciar el proceso de despliegue"""
        if not self.can_execute():
            raise ValidationError("Deployment cannot be executed at this time")
        
        self.status = 'in_progress'
        self.deployed_at = timezone.now()
        self.save()
    
    def complete_deployment(self, success_count=0, failure_count=0, error_message=''):
        """Marcar el deployment como completado"""
        self.status = 'completed' if failure_count == 0 else 'failed'
        self.success_count = success_count
        self.failure_count = failure_count
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()


class DeploymentPlayer(models.Model):
    """Tracking del despliegue por player individual"""
    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='player_results')
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE)
    
    # Estado específico del player
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('syncing', 'Syncing'),
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('timeout', 'Timeout'),
        ],
        default='pending'
    )
    
    # Detalles de la sincronización
    sync_started_at = models.DateTimeField(null=True, blank=True)
    sync_completed_at = models.DateTimeField(null=True, blank=True)
    assets_synced = models.PositiveIntegerField(default=0)
    bytes_transferred = models.PositiveBigIntegerField(default=0)
    
    # Hash de sincronización
    sync_hash_sent = models.CharField(max_length=64, blank=True)
    sync_hash_confirmed = models.CharField(max_length=64, blank=True)
    
    error_message = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['deployment', 'player']
        ordering = ['player__name']
    
    def __str__(self):
        return f"{self.deployment.name} -> {self.player.name} ({self.status})"


class EmergencyMessage(models.Model):
    """Mensajes de emergencia - funcionalidad del original"""
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    
    # Targeting
    groups = models.ManyToManyField('players.Group', blank=True, related_name='emergency_messages')
    players = models.ManyToManyField('players.Player', blank=True, related_name='emergency_messages')
    
    # Configuración de display
    display_duration = models.PositiveIntegerField(
        default=30, 
        help_text="Duration to display message in seconds"
    )
    background_color = models.CharField(max_length=7, default='#ff0000')
    text_color = models.CharField(max_length=7, default='#ffffff')
    font_size = models.PositiveIntegerField(default=48)
    
    # Control de tiempo
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Estado
    is_active = models.BooleanField(default=True)
    acknowledged_by = models.ManyToManyField(
        'players.Player', 
        through='EmergencyAcknowledgement',
        related_name='acknowledged_emergencies'
    )
    
    created_by = models.CharField(max_length=100, default='admin')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
        verbose_name = "Emergency Message"
        verbose_name_plural = "Emergency Messages"
    
    def __str__(self):
        return f"[{self.priority.upper()}] {self.title}"
    
    def is_currently_active(self):
        """Verificar si el mensaje está activo ahora"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        
        if now < self.start_time:
            return False
        
        if self.end_time and now > self.end_time:
            return False
        
        return True
    
    def get_target_players(self):
        """Obtener todos los players que deben recibir este mensaje"""
        target_players = set()
        
        # Players directos
        for player in self.players.all():
            target_players.add(player)
        
        # Players de grupos
        for group in self.groups.all():
            for player in group.players.all():
                target_players.add(player)
        
        return list(target_players)
    
    def to_sync_data(self):
        """Convertir a formato de sincronización"""
        return {
            'id': str(self.id),
            'title': self.title,
            'message': self.message,
            'priority': self.priority,
            'display_duration': self.display_duration,
            'background_color': self.background_color,
            'text_color': self.text_color,
            'font_size': self.font_size,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
        }


class EmergencyAcknowledgement(models.Model):
    """Tracking de acknowledgments de mensajes de emergencia"""
    emergency_message = models.ForeignKey(EmergencyMessage, on_delete=models.CASCADE)
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE)
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['emergency_message', 'player']


class SystemCommand(models.Model):
    """Comandos del sistema - funcionalidad de control remoto del original"""
    COMMAND_TYPES = [
        ('reboot', 'Reboot Player'),
        ('restart_app', 'Restart Application'),
        ('update_software', 'Update Software'),
        ('clear_cache', 'Clear Cache'),
        ('screenshot', 'Take Screenshot'),
        ('shell_command', 'Custom Shell Command'),
        ('tv_on', 'Turn TV On'),
        ('tv_off', 'Turn TV Off'),
        ('set_volume', 'Set Volume'),
    ]
    
    COMMAND_STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('executed', 'Executed'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ]
    
    command_type = models.CharField(max_length=20, choices=COMMAND_TYPES)
    
    # Targeting
    players = models.ManyToManyField('players.Player', related_name='system_commands')
    
    # Parámetros del comando
    parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Command parameters (e.g., shell command, volume level)"
    )
    
    # Estado y tracking
    status = models.CharField(max_length=10, choices=COMMAND_STATUS, default='pending')
    scheduled_at = models.DateTimeField(default=timezone.now)
    executed_at = models.DateTimeField(null=True, blank=True)
    
    # Resultados
    success_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    results = models.JSONField(default=dict, blank=True)
    
    created_by = models.CharField(max_length=100, default='admin')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "System Command"
        verbose_name_plural = "System Commands"
    
    def __str__(self):
        return f"{self.get_command_type_display()} - {self.status}"
    
    def can_execute(self):
        """Verificar si el comando puede ejecutarse"""
        return self.status == 'pending' and timezone.now() >= self.scheduled_at
    
    def to_sync_data(self):
        """Convertir comando a formato de sincronización"""
        return {
            'id': str(self.id),
            'command_type': self.command_type,
            'parameters': self.parameters,
            'scheduled_at': self.scheduled_at.isoformat(),
        }


class SyncRequest(models.Model):
    """Requests de sincronización desde players - para tracking"""
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE, related_name='sync_requests')
    
    # Request data
    request_timestamp = models.DateTimeField(auto_now_add=True)
    client_sync_hash = models.CharField(max_length=64, blank=True)
    app_version = models.CharField(max_length=20, blank=True)
    firmware_version = models.CharField(max_length=20, blank=True)
    
    # Response data
    needs_sync = models.BooleanField(default=False)
    server_sync_hash = models.CharField(max_length=64, blank=True)
    response_timestamp = models.DateTimeField(null=True, blank=True)
    
    # Health data from request
    battery_level = models.PositiveIntegerField(null=True, blank=True)
    storage_free_mb = models.PositiveIntegerField(null=True, blank=True)
    connection_type = models.CharField(max_length=20, blank=True)
    
    class Meta:
        ordering = ['-request_timestamp']
        verbose_name = "Sync Request"
        verbose_name_plural = "Sync Requests"
    
    def __str__(self):
        return f"{self.player.name} - {self.request_timestamp} ({'sync' if self.needs_sync else 'no sync'})"


# Management Commands y Scheduled Tasks
class ScheduledTask(models.Model):
    """Tareas programadas del sistema"""
    TASK_TYPES = [
        ('cleanup_logs', 'Cleanup Old Logs'),
        ('update_check', 'Check for Updates'),
        ('backup_data', 'Backup Data'),
        ('generate_reports', 'Generate Reports'),
        ('sync_all_players', 'Sync All Players'),
    ]
    
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    name = models.CharField(max_length=200)
    
    # Cron-like scheduling
    schedule_pattern = models.CharField(
        max_length=100,
        help_text="Cron pattern: * * * * * (minute hour day month weekday)"
    )
    
    # Estado
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    # Configuración
    parameters = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Scheduled Task"
        verbose_name_plural = "Scheduled Tasks"
    
    def __str__(self):
        return f"{self.name} ({self.schedule_pattern})"