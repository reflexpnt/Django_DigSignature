from django.db import models
from django.core.validators import MinValueValidator

class Schedule(models.Model):
    """Programación de playlists"""
    REPEAT_CHOICES = [
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    name = models.CharField(max_length=200)
    playlist = models.ForeignKey('playlists.Playlist', on_delete=models.CASCADE)
    group = models.ForeignKey('players.Group', on_delete=models.CASCADE)
    
    # Programación
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    repeat_type = models.CharField(max_length=10, choices=REPEAT_CHOICES, default='once')
    weekdays = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Comma-separated weekdays (1=Monday, 7=Sunday). E.g: 1,2,3,4,5"
    )
    
    # Configuraciones
    priority = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Higher numbers = higher priority"
    )
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', 'start_time']
        verbose_name = "Schedule"
        verbose_name_plural = "Schedules"
    
    def __str__(self):
        return f"{self.name} - {self.playlist.name}"

class Deployment(models.Model):
    """Despliegues de contenido a grupos"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('deploying', 'Deploying'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    group = models.ForeignKey('players.Group', on_delete=models.CASCADE)
    playlist = models.ForeignKey(
        'playlists.Playlist', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    
    # Para tracking del progreso
    total_players = models.PositiveIntegerField(default=0)
    completed_players = models.PositiveIntegerField(default=0)
    failed_players = models.PositiveIntegerField(default=0)
    
    # Configuraciones del despliegue
    force_sync = models.BooleanField(default=False)
    deploy_immediately = models.BooleanField(default=True)
    scheduled_deploy_time = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Deployment"
        verbose_name_plural = "Deployments"
    
    def __str__(self):
        return f"Deploy {self.playlist.name if self.playlist else 'Config'} to {self.group.name}"
    
    @property
    def progress_percentage(self):
        if self.total_players == 0:
            return 0
        return (self.completed_players / self.total_players) * 100

class DeploymentLog(models.Model):
    """Log detallado de despliegues"""
    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='logs')
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE)
    
    status = models.CharField(max_length=12, choices=Deployment.STATUS_CHOICES)
    message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = "Deployment Log"
        verbose_name_plural = "Deployment Logs"
    
    def __str__(self):
        return f"{self.deployment.name} - {self.player.name} ({self.status})"