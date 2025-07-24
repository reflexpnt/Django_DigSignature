from django.db import models
import os

class SystemSettings(models.Model):
    """Configuraciones globales del sistema (Singleton)"""
    installation_name = models.CharField(max_length=200, default='PiSignage Installation')
    
    # Configuraciones de upload
    max_file_size_mb = models.PositiveIntegerField(default=500)
    allowed_file_types = models.CharField(
        max_length=500, 
        default='mp4,avi,mov,jpg,png,pdf,html,zip,mp3'
    )
    
    # Configuraciones de conversión
    auto_convert_videos = models.BooleanField(default=True)
    video_quality = models.CharField(
        max_length=10, 
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('ultra', 'Ultra')
        ],
        default='high'
    )
    generate_thumbnails = models.BooleanField(default=True)
    
    # Configuraciones de sync
    default_sync_interval = models.PositiveIntegerField(default=300)  # segundos
    
    # Configuraciones de servidor
    server_name = models.CharField(max_length=200, blank=True)
    server_port = models.PositiveIntegerField(default=3000)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"
    
    def save(self, *args, **kwargs):
        # Asegurar que solo existe una instancia (Singleton)
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return f"Settings: {self.installation_name}"

class ActivityLog(models.Model):
    """Log de actividades del sistema"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('deploy', 'Deploy'),
        ('sync', 'Sync'),
        ('upload', 'Upload'),
        ('register', 'Register'),
    ]
    
    # ¿Quién? (sin sistema de usuarios complejo por ahora)
    user = models.CharField(max_length=100, default='system')
    
    # ¿Qué?
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.CharField(max_length=50)
    object_repr = models.CharField(max_length=200)
    
    # ¿Cuándo?
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # ¿Detalles?
    details = models.JSONField(default=dict, blank=True)
    
    # IP y User Agent
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"
    
    def __str__(self):
        return f"{self.action.title()} {self.model_name} - {self.object_repr}"