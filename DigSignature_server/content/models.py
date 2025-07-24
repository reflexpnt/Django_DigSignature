# content/models.py - Basado en el análisis del proyecto Node.js original
from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import os
import hashlib

class Label(models.Model):
    """Etiquetas para organizar assets - equivalente al sistema de labels del original"""
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
    """Layouts predefinidos - basado en los 8 layouts del original"""
    PREDEFINED_LAYOUTS = [
        ('1', 'Layout 1 - Full Screen'),
        ('2a', 'Layout 2a - Main + Side'),
        ('2b', 'Layout 2b - Main + Bottom'),
        ('3a', 'Layout 3a - Main + 2 Sides'),
        ('3b', 'Layout 3b - Main + Side + Bottom'),
        ('4', 'Layout 4 - 4 Quadrants'),
        ('4b', 'Layout 4b - Main + 3 Zones'),
        ('2ab', 'Layout 2ab - Main + Side + Bottom'),
        ('custom', 'Custom Layout'),
    ]
    
    code = models.CharField(max_length=10, choices=PREDEFINED_LAYOUTS, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Configuración de zonas en JSON - basado en el original
    zones_config = models.JSONField(
        default=dict,
        help_text="JSON configuration defining layout zones and their properties"
    )
    
    # Para layouts custom
    is_custom = models.BooleanField(default=False)
    custom_html = models.TextField(
        blank=True,
        help_text="Custom HTML template for layout (for custom layouts only)"
    )
    
    # Preview del layout
    preview_image = models.ImageField(
        upload_to='layouts/previews/',
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
        verbose_name = "Layout"
        verbose_name_plural = "Layouts"
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def zone_count(self):
        """Número de zonas en el layout"""
        return len(self.zones_config.keys()) if self.zones_config else 1
    
    @classmethod
    def get_default_layouts(cls):
        """Crear layouts por defecto basados en el original"""
        default_configs = {
            '1': {
                'main': {'x': 0, 'y': 0, 'width': 100, 'height': 100}
            },
            '2a': {
                'main': {'x': 0, 'y': 0, 'width': 75, 'height': 100},
                'side': {'x': 75, 'y': 0, 'width': 25, 'height': 100}
            },
            '2b': {
                'main': {'x': 0, 'y': 0, 'width': 100, 'height': 75},
                'bottom': {'x': 0, 'y': 75, 'width': 100, 'height': 25}
            },
            '3a': {
                'main': {'x': 25, 'y': 0, 'width': 50, 'height': 100},
                'side1': {'x': 0, 'y': 0, 'width': 25, 'height': 100},
                'side2': {'x': 75, 'y': 0, 'width': 25, 'height': 100}
            },
            '3b': {
                'main': {'x': 0, 'y': 0, 'width': 75, 'height': 75},
                'side': {'x': 75, 'y': 0, 'width': 25, 'height': 75},
                'bottom': {'x': 0, 'y': 75, 'width': 100, 'height': 25}
            },
            '4': {
                'zone1': {'x': 0, 'y': 0, 'width': 50, 'height': 50},
                'zone2': {'x': 50, 'y': 0, 'width': 50, 'height': 50},
                'zone3': {'x': 0, 'y': 50, 'width': 50, 'height': 50},
                'zone4': {'x': 50, 'y': 50, 'width': 50, 'height': 50}
            },
            '4b': {
                'main': {'x': 0, 'y': 0, 'width': 67, 'height': 67},
                'zone2': {'x': 67, 'y': 0, 'width': 33, 'height': 33},
                'zone3': {'x': 67, 'y': 33, 'width': 33, 'height': 34},
                'zone4': {'x': 0, 'y': 67, 'width': 67, 'height': 33}
            },
            '2ab': {
                'main': {'x': 0, 'y': 0, 'width': 75, 'height': 75},
                'side': {'x': 75, 'y': 0, 'width': 25, 'height': 75},
                'bottom': {'x': 0, 'y': 75, 'width': 100, 'height': 25}
            }
        }
        
        for code, config in default_configs.items():
            layout_name = dict(cls.PREDEFINED_LAYOUTS)[code]
            cls.objects.get_or_create(
                code=code,
                defaults={
                    'name': layout_name,
                    'zones_config': config,
                    'is_custom': False
                }
            )

def asset_upload_path(instance, filename):
    """Generar path dinámico para uploads - similar al original"""
    from datetime import datetime
    now = datetime.now()
    return f'assets/{now.year}/{now.month:02d}/{filename}'

class Asset(models.Model):
    """Assets/Contenido multimedia - basado en el esquema original"""
    ASSET_TYPES = [
        ('video', 'Video'),
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('pdf', 'PDF'),
        ('html', 'HTML'),
        ('zip', 'ZIP Package'),
        ('link', 'Web Link'),
        ('rss', 'RSS Feed'),
        ('calendar', 'Google Calendar'),
    ]
    
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('error', 'Error'),
    ]
    
    # Información básica
    name = models.CharField(max_length=200)
    original_name = models.CharField(max_length=200, blank=True)
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='ready')
    
    # Archivos
    file = models.FileField(
        upload_to=asset_upload_path,
        null=True,
        blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['mp4', 'avi', 'mov', 'mkv', 'jpg', 'jpeg', 'png', 'gif', 
                              'pdf', 'html', 'zip', 'mp3', 'wav', 'aac']
        )]
    )
    thumbnail = models.ImageField(
        upload_to='thumbnails/%Y/%m/',
        null=True,
        blank=True
    )
    
    # Para URLs/links
    url = models.URLField(blank=True)
    
    # Metadatos - basado en los campos del original
    file_size = models.PositiveBigIntegerField(null=True, blank=True)  # bytes
    duration = models.PositiveIntegerField(null=True, blank=True)  # segundos
    resolution = models.CharField(max_length=20, blank=True)  # ej: 1920x1080
    
    # Metadata adicional en JSON - como en el original
    metadata = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Additional metadata like codec, bitrate, fps, etc."
    )
    
    # Checksum para sincronización - crítico para el port
    checksum = models.CharField(max_length=64, blank=True, help_text="SHA256 checksum of file")
    
    # Información adicional
    description = models.TextField(blank=True)
    
    # Organización - sistema de labels como en el original
    labels = models.ManyToManyField(Label, blank=True)
    
    # Control de versiones
    version = models.PositiveIntegerField(default=1)
    
    # Fechas de validez - funcionalidad del original
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Calcular checksum automáticamente - crítico para sync
        if self.file and not self.checksum:
            self.checksum = self.calculate_checksum()
        
        # Guardar nombre original
        if self.file and not self.original_name:
            self.original_name = os.path.basename(self.file.name)
        
        super().save(*args, **kwargs)
    
    def calculate_checksum(self):
        """Calcular SHA256 checksum del archivo"""
        if not self.file:
            return ''
        
        hash_sha256 = hashlib.sha256()
        
        try:
            self.file.seek(0)
            for chunk in iter(lambda: self.file.read(4096), b""):
                hash_sha256.update(chunk)
            self.file.seek(0)
            return hash_sha256.hexdigest()
        except:
            return ''
    
    @property
    def file_size_human(self):
        """Tamaño de archivo en formato legible"""
        if not self.file_size:
            return "Unknown"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
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
    
    @property
    def download_url(self):
        """URL para descargar el asset - usado en sync"""
        return f"/content/assets/{self.id}/download/"
    
    @property
    def thumbnail_url(self):
        """URL del thumbnail"""
        if self.thumbnail:
            return self.thumbnail.url
        return None
    
    def is_video(self):
        return self.asset_type == 'video'
    
    def is_image(self):
        return self.asset_type == 'image'
    
    def is_audio(self):
        return self.asset_type == 'audio'
    
    def needs_conversion(self):
        """Determinar si el asset necesita conversión"""
        if self.asset_type == 'video' and self.file:
            ext = os.path.splitext(self.file.name)[1].lower()
            return ext != '.mp4'
        return False
    
    def create_thumbnail(self):
        """Crear thumbnail del asset - implementar con PIL/ImageMagick"""
        # TODO: Implementar generación de thumbnails
        pass
    
    def convert_to_mp4(self):
        """Convertir video a MP4 - implementar con FFmpeg"""
        # TODO: Implementar conversión de video
        pass
    
    def extract_metadata(self):
        """Extraer metadata del archivo - implementar con FFprobe"""
        # TODO: Implementar extracción de metadata
        pass


# Modelo para tracking de conversiones
class AssetConversion(models.Model):
    """Tracking de conversiones de assets"""
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='conversions')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    conversion_type = models.CharField(
        max_length=20,
        choices=[
            ('video_mp4', 'Video to MP4'),
            ('thumbnail', 'Thumbnail Generation'),
            ('metadata', 'Metadata Extraction'),
        ]
    )
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.asset.name} - {self.conversion_type} ({self.status})"