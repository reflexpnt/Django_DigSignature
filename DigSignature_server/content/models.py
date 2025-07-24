from django.db import models
from django.core.validators import FileExtensionValidator
import os

class Label(models.Model):
    """Etiquetas para organizar assets"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(
        max_length=7, 
        default='#007bff',
        help_text="Hex color code (e.g., #007bff)"
    )
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Label"
        verbose_name_plural = "Labels"
    
    def __str__(self):
        return self.name

class Layout(models.Model):
    """Layouts/Plantillas para playlists"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Configuración del layout (JSON)
    zones_config = models.JSONField(
        default=dict,
        help_text="JSON configuration for layout zones"
    )
    is_custom = models.BooleanField(default=False)
    
    # Preview del layout
    preview_image = models.ImageField(
        upload_to='layouts/previews/',
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Layout"
        verbose_name_plural = "Layouts"
    
    def __str__(self):
        return self.name
    
    @property
    def zone_count(self):
        return len(self.zones_config.keys()) if self.zones_config else 1

def asset_upload_path(instance, filename):
    """Generar path dinámico para uploads"""
    # Organizar por año/mes
    from datetime import datetime
    now = datetime.now()
    return f'assets/{now.year}/{now.month:02d}/{filename}'

class Asset(models.Model):
    """Assets/Contenido multimedia"""
    ASSET_TYPES = [
        ('video', 'Video'),
        ('image', 'Image'),
        ('pdf', 'PDF'),
        ('html', 'HTML'),
        ('url', 'URL/Link'),
        ('audio', 'Audio'),
    ]
    
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('error', 'Error'),
    ]
    
    name = models.CharField(max_length=200)
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='ready')
    
    # Archivos
    file = models.FileField(
        upload_to=asset_upload_path,
        null=True,
        blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['mp4', 'avi', 'mov', 'jpg', 'jpeg', 'png', 'pdf', 'html', 'zip', 'mp3', 'wav']
        )]
    )
    thumbnail = models.ImageField(
        upload_to='thumbnails/%Y/%m/',
        null=True,
        blank=True
    )
    
    # Para URLs/links
    url = models.URLField(blank=True)
    
    # Metadatos
    file_size = models.PositiveBigIntegerField(null=True, blank=True)  # bytes
    duration = models.PositiveIntegerField(null=True, blank=True)  # segundos
    resolution = models.CharField(max_length=20, blank=True)  # ej: 1920x1080
    
    # Información adicional
    description = models.TextField(blank=True)
    
    # Organización
    labels = models.ManyToManyField(Label, blank=True)
    
    # Control de versiones
    version = models.PositiveIntegerField(default=1)
    
    # Fechas de validez
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
    
    def __str__(self):
        return self.name
    
    @property
    def file_size_human(self):
        """Tamaño de archivo en formato legible"""
        if not self.file_size:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    @property
    def duration_human(self):
        """Duración en formato legible"""
        if not self.duration:
            return None
        
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"