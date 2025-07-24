from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Playlist(models.Model):
    """Listas de reproducción"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    layout = models.ForeignKey('content.Layout', on_delete=models.CASCADE)
    
    # Configuraciones de playlist
    is_advertisement = models.BooleanField(default=False)
    ad_interval = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Advertisement interval in seconds"
    )
    
    # Ticker
    ticker_enabled = models.BooleanField(default=False)
    ticker_text = models.TextField(blank=True)
    ticker_speed = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    
    # Configuraciones avanzadas
    shuffle_enabled = models.BooleanField(default=False)
    repeat_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Playlist"
        verbose_name_plural = "Playlists"
    
    def __str__(self):
        return self.name
    
    @property
    def total_duration(self):
        """Duración total de la playlist en segundos"""
        return sum(item.duration for item in self.items.all())
    
    @property
    def item_count(self):
        return self.items.count()

class PlaylistItem(models.Model):
    """Items/elementos de una playlist"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='items')
    asset = models.ForeignKey('content.Asset', on_delete=models.CASCADE)
    
    # Configuración por item
    duration = models.PositiveIntegerField(
        default=10,
        help_text="Duration in seconds"
    )
    zone = models.CharField(
        max_length=20, 
        default='main',
        help_text="Layout zone (main, side, bottom, etc.)"
    )
    order = models.PositiveIntegerField(default=0)
    
    # Para layouts complejos
    fullscreen = models.BooleanField(default=False)
    
    # Configuraciones avanzadas
    transition_effect = models.CharField(
        max_length=20,
        choices=[
            ('none', 'None'),
            ('fade', 'Fade'),
            ('slide', 'Slide'),
            ('zoom', 'Zoom'),
        ],
        default='none'
    )
    
    # Fechas de validez específicas
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ['playlist', 'asset', 'zone']
        verbose_name = "Playlist Item"
        verbose_name_plural = "Playlist Items"
    
    def __str__(self):
        return f"{self.playlist.name} - {self.asset.name} ({self.zone})"