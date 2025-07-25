# playlists/models.py - Basado en el análisis del proyecto Node.js original
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import hashlib
import json

class Playlist(models.Model):
    """Listas de reproducción - basado en el esquema original"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    layout = models.ForeignKey('content.Layout', on_delete=models.CASCADE)
    
    # Configuraciones de playlist - basado en el original
    is_advertisement = models.BooleanField(default=False, help_text="Advertisement playlist with interval timer")
    ad_interval = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Advertisement interval in seconds (for ad playlists)"
    )
    
    # Ticker configuration - funcionalidad clave del original
    ticker_enabled = models.BooleanField(default=False)
    ticker_text = models.TextField(blank=True, help_text="Static ticker text or RSS feed URL")
    ticker_speed = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Ticker scroll speed (1=slow, 10=fast)"
    )
    ticker_position = models.CharField(
        max_length=10,
        choices=[
            ('bottom', 'Bottom'),
            ('top', 'Top'),
        ],
        default='bottom'
    )
    
    # Configuraciones avanzadas - del original
    shuffle_enabled = models.BooleanField(default=False, help_text="Shuffle assets before playback")
    repeat_enabled = models.BooleanField(default=True, help_text="Repeat playlist when finished")
    
    # Para playlist merging - funcionalidad del original
    merge_alternate_assets = models.BooleanField(
        default=False, 
        help_text="Merge alternate assets from different playlists"
    )
    
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
        return sum(item.effective_duration for item in self.items.all())
    
    @property
    def item_count(self):
        """Número de items en la playlist"""
        return self.items.count()
    
    @property
    def asset_count_by_zone(self):
        """Conteo de assets por zona"""
        zones = {}
        for item in self.items.all():
            zone = item.zone
            if zone not in zones:
                zones[zone] = 0
            zones[zone] += 1
        return zones
    
    def get_sync_hash(self):
        """Calcular hash para detectar cambios - crítico para sync sin WebSocket"""
        data = {
            'id': self.id,
            'name': self.name,
            'layout': self.layout.code,
            'updated_at': self.updated_at.isoformat(),
            'ticker_enabled': self.ticker_enabled,
            'ticker_text': self.ticker_text,
            'items': []
        }
        
        for item in self.items.all().order_by('order'):
            data['items'].append({
                'asset_id': item.asset.id,
                'asset_checksum': item.asset.checksum,
                'duration': item.duration,
                'zone': item.zone,
                'order': item.order,
                'transition': item.transition_effect
            })
        
        json_string = json.dumps(data, sort_keys=True)
        full_hash = hashlib.sha256(json_string.encode()).hexdigest()
        return full_hash[:8]  # Primeros 8 caracteres
        #return hashlib.sha256(json_string.encode()).hexdigest()
    
    def to_sync_data(self):
        """Convertir playlist a formato de sincronización - como en el original"""
        return {
            'id': str(self.id),
            'name': self.name,
            'layout': self.layout.code,
            'active': True,  # TODO: Implementar lógica de activación
            'ticker': {
                'enabled': self.ticker_enabled,
                'text': self.ticker_text,
                'speed': self.ticker_speed,
                'position': self.ticker_position
            },
            'shuffle': self.shuffle_enabled,
            'repeat': self.repeat_enabled,
            'items': [item.to_sync_data() for item in self.items.all().order_by('order')]
        }

class PlaylistItem(models.Model):
    """Items/elementos de una playlist - basado en el esquema original"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='items')
    asset = models.ForeignKey('content.Asset', on_delete=models.CASCADE)
    
    # Configuración por item - campos del original
    duration = models.PositiveIntegerField(
        default=10,
        help_text="Duration in seconds (for non-video assets)"
    )
    
    # Zone mapping - crítico para layouts multi-zona
    zone = models.CharField(
        max_length=20, 
        default='main',
        help_text="Layout zone: main, side, bottom, zone1, zone2, zone3, zone4"
    )
    
    order = models.PositiveIntegerField(default=0, help_text="Display order within zone")
    
    # Para layouts complejos - funcionalidad del original
    fullscreen = models.BooleanField(default=False, help_text="Display asset in fullscreen mode")
    
    # Configuraciones avanzadas - del original
    transition_effect = models.CharField(
        max_length=20,
        choices=[
            ('none', 'None'),
            ('fade', 'Fade'),
            ('slide', 'Slide'),
            ('zoom', 'Zoom'),
            ('dissolve', 'Dissolve'),
        ],
        default='none'
    )
    
    # Asset-specific ticker - funcionalidad del original
    asset_ticker = models.TextField(
        blank=True, 
        help_text="Asset-specific ticker message (overrides playlist ticker)"
    )
    
    # Fechas de validez específicas - del original
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['zone', 'order']
        unique_together = ['playlist', 'asset', 'zone', 'order']
        verbose_name = "Playlist Item"
        verbose_name_plural = "Playlist Items"
    
    def __str__(self):
        return f"{self.playlist.name} - {self.asset.name} ({self.zone})"
    
    @property
    def effective_duration(self):
        """Duración efectiva del item (video usa su duración, otros usan la configurada)"""
        if self.asset.is_video() and self.asset.duration:
            return self.asset.duration
        return self.duration
    
    @property
    def is_currently_valid(self):
        """Verificar si el item es válido en este momento"""
        now = timezone.now()
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        return True
    
    def to_sync_data(self):
        """Convertir item a formato de sincronización - como en el original"""
        return {
            'id': self.id,
            'asset_id': str(self.asset.id),
            'duration': self.effective_duration,
            'zone': self.zone,
            'order': self.order,
            'transition': self.transition_effect,
            'fullscreen': self.fullscreen,
            'asset_ticker': self.asset_ticker,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
        }


class PlaylistSchedule(models.Model):
    """Programación de playlists - funcionalidad del original"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='schedules')
    group = models.ForeignKey('players.Group', on_delete=models.CASCADE, related_name='playlist_schedules')
    
    # Configuración de horario
    start_time = models.TimeField(help_text="Daily start time (e.g., 08:00)")
    end_time = models.TimeField(help_text="Daily end time (e.g., 18:00)")
    
    # Días de la semana - 1=Monday, 7=Sunday
    days_of_week = models.JSONField(
        default=list,
        help_text="List of weekdays [1,2,3,4,5] for Mon-Fri"
    )
    
    # Fechas específicas
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Prioridad para resolución de conflictos
    priority = models.PositiveIntegerField(
        default=1,
        help_text="Higher number = higher priority"
    )
    
    # Estado
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', 'start_time']
        verbose_name = "Playlist Schedule"
        verbose_name_plural = "Playlist Schedules"
    
    def __str__(self):
        return f"{self.playlist.name} -> {self.group.name} ({self.start_time}-{self.end_time})"
    
    def is_active_now(self):
        """Verificar si el schedule está activo ahora"""
        if not self.is_active:
            return False
        
        # VALIDACIÓN para valores nulos.
        if not self.start_time or not self.end_time:
            return False
        now = timezone.now()
        
        # Verificar fecha
        if self.start_date and now.date() < self.start_date:
            return False
        
        if self.end_date and now.date() > self.end_date:
            return False
        
        # Verificar día de la semana (1=Monday)
        if self.days_of_week and now.isoweekday() not in self.days_of_week:
            return False
        
        # Verificar hora
        current_time = now.time()
        if self.start_time <= self.end_time:
            # Mismo día
            return self.start_time <= current_time <= self.end_time
        else:
            # Cruza medianoche
            return current_time >= self.start_time or current_time <= self.end_time
    
    @classmethod
    def get_active_playlist_for_group(cls, group):
        """Obtener la playlist activa de mayor prioridad para un grupo"""
        active_schedules = cls.objects.filter(
            group=group,
            is_active=True
        ).order_by('-priority', '-id')
        
        for schedule in active_schedules:
            if schedule.is_active_now():
                return schedule.playlist
        
        # Fallback a playlist por defecto del grupo
        return group.default_playlist


# Modelo para estadísticas de reproducción
class PlaylistStats(models.Model):
    """Estadísticas de reproducción de playlists"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='stats')
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE)
    
    # Datos de reproducción
    played_at = models.DateTimeField(auto_now_add=True)
    duration_played = models.PositiveIntegerField(help_text="Seconds played")
    completed = models.BooleanField(default=False)
    
    # Contexto adicional
    items_played = models.PositiveIntegerField(default=0)
    errors_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-played_at']
        verbose_name = "Playlist Stats"
        verbose_name_plural = "Playlist Stats"
    
    def __str__(self):
        return f"{self.playlist.name} on {self.player.name} at {self.played_at}"