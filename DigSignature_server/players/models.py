from django.db import models
from django.core.validators import RegexValidator

class Group(models.Model):
    """Grupos de reproductores"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Configuraciones por defecto del grupo
    default_playlist = models.ForeignKey(
        'playlists.Playlist', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='default_for_groups'
    )
    sync_interval = models.PositiveIntegerField(default=300)  # segundos
    resolution = models.CharField(
        max_length=20, 
        choices=[
            ('1920x1080', '1920x1080 (Full HD)'),
            ('1280x720', '1280x720 (HD)'),
            ('1024x768', '1024x768 (XGA)'),
            ('800x600', '800x600 (SVGA)'),
        ],
        default='1920x1080'
    )
    orientation = models.CharField(
        max_length=10, 
        choices=[
            ('landscape', 'Landscape'), 
            ('portrait', 'Portrait')
        ], 
        default='landscape'
    )
    audio_enabled = models.BooleanField(default=True)
    
    # Configuraciones avanzadas
    tv_control = models.BooleanField(default=False, help_text="Enable CEC TV control")
    screenshot_interval = models.PositiveIntegerField(
        default=3600, 
        help_text="Screenshot interval in seconds"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Group"
        verbose_name_plural = "Groups"
    
    def __str__(self):
        return self.name
    
    @property
    def player_count(self):
        return self.players.count()

class Player(models.Model):
    """Reproductores/Dispositivos"""
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('error', 'Error'),
        ('syncing', 'Syncing'),
    ]
    
    # Validador para Device ID (16 dígitos hexadecimales)
    device_id_validator = RegexValidator(
        regex=r'^[0-9A-Fa-f]{16}$',
        message='Device ID must be exactly 16 hexadecimal characters'
    )
    
    device_id = models.CharField(
        max_length=16, 
        unique=True,
        validators=[device_id_validator],
        help_text="16-digit hexadecimal device identifier"
    )
    name = models.CharField(max_length=100)
    mac_address = models.CharField(
        max_length=17, 
        blank=True,
        validators=[RegexValidator(
            regex=r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
            message='Invalid MAC address format'
        )]
    )
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='players')
    
    # Estado y conectividad
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='offline')
    last_seen = models.DateTimeField(null=True, blank=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Información del hardware/software
    player_version = models.CharField(max_length=20, blank=True)
    hardware_info = models.JSONField(default=dict, blank=True)  # JSON para info técnica
    
    # Configuraciones específicas (override del grupo si es necesario)
    custom_resolution = models.CharField(max_length=20, blank=True)
    custom_orientation = models.CharField(max_length=10, blank=True)
    
    # Geolocalización y timezone
    location = models.CharField(max_length=200, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Configuraciones adicionales
    notes = models.TextField(blank=True, help_text="Administrator notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Player"
        verbose_name_plural = "Players"
    
    def __str__(self):
        return f"{self.name} ({self.device_id})"
    
    @property
    def is_online(self):
        return self.status == 'online'
    
    @property
    def effective_resolution(self):
        return self.custom_resolution or self.group.resolution
    
    @property
    def effective_orientation(self):
        return self.custom_orientation or self.group.orientation