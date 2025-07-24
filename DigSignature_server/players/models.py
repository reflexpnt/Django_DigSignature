from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta

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
    
    # Geolocalización por defecto
    default_timezone = models.CharField(max_length=50, default='UTC')
    
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
    
    @property
    def online_player_count(self):
        return self.players.filter(status='online').count()

class Player(models.Model):
    """Reproductores/Dispositivos"""
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('error', 'Error'),
        ('syncing', 'Syncing'),
    ]
    
    CONNECTION_TYPES = [
        ('wifi', 'WiFi'),
        ('mobile', 'Mobile Data'),
        ('ethernet', 'Ethernet'),
        ('unknown', 'Unknown'),
    ]
    
    # Validador para Device ID (16 dígitos hexadecimales)
    device_id_validator = RegexValidator(
        regex=r'^[0-9A-Fa-f]{16}$',
        message='Device ID must be exactly 16 hexadecimal characters'
    )
    
    # === CAMPOS CORE ===
    device_id = models.CharField(
        max_length=16, 
        unique=True,
        validators=[device_id_validator],
        help_text="16-digit hexadecimal device identifier"
    )
    name = models.CharField(max_length=100)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='players')
    
    # === ESTADO Y CONECTIVIDAD ===
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='offline')
    last_sync = models.DateTimeField(null=True, blank=True)
    last_sync_hash = models.CharField(max_length=64, blank=True, help_text="SHA256 hash for sync detection")
    sync_fail_count = models.PositiveIntegerField(default=0, help_text="Consecutive sync failures")
    
    # === INFORMACIÓN DEL DEVICE ===
    app_version = models.CharField(max_length=20, blank=True, help_text="App version (e.g., 1.2.3)")
    firmware_version = models.CharField(max_length=20, blank=True, help_text="Android version (e.g., 12)")
    
    # === ESTADO DE SALUD ===
    battery_level = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Battery percentage (0-100)"
    )
    storage_free_mb = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Free storage in MB"
    )
    temperature_celsius = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Device temperature in Celsius"
    )
    
    # === INFORMACIÓN DE RED ===
    connection_type = models.CharField(
        max_length=20, 
        choices=CONNECTION_TYPES,
        blank=True,
        default='unknown'
    )
    signal_strength = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Signal strength in dBm (WiFi: -30 to -90, Mobile: -50 to -120)"
    )
    
    # === CONFIGURACIONES PERSONALIZADAS ===
    custom_resolution = models.CharField(
        max_length=20, 
        blank=True,
        choices=[
            ('1920x1080', '1920x1080 (Full HD)'),
            ('1280x720', '1280x720 (HD)'),
            ('1024x768', '1024x768 (XGA)'),
            ('800x600', '800x600 (SVGA)'),
        ],
        help_text="Override group resolution if needed"
    )
    custom_orientation = models.CharField(
        max_length=10, 
        choices=[
            ('landscape', 'Landscape'), 
            ('portrait', 'Portrait')
        ], 
        blank=True,
        help_text="Override group orientation if needed"
    )
    
    # === GEOLOCALIZACIÓN Y TIMEZONE ===
    timezone = models.CharField(
        max_length=50, 
        default='UTC',
        help_text="Device timezone (e.g., Europe/Madrid, America/New_York)"
    )
    location = models.CharField(max_length=200, blank=True, help_text="Physical location description")
    
    # === ADMINISTRACIÓN ===
    notes = models.TextField(blank=True, help_text="Administrator notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Player"
        verbose_name_plural = "Players"
    
    def __str__(self):
        return f"{self.name} ({self.device_id})"
    
    # === PROPERTIES ===
    @property
    def is_online(self):
        """Check if player is currently online"""
        return self.status == 'online'
    
    @property
    def effective_resolution(self):
        """Get effective resolution (custom or group default)"""
        return self.custom_resolution or self.group.resolution
    
    @property
    def effective_orientation(self):
        """Get effective orientation (custom or group default)"""
        return self.custom_orientation or self.group.orientation
    
    @property
    def effective_timezone(self):
        """Get effective timezone (player or group default)"""
        return self.timezone if self.timezone != 'UTC' else self.group.default_timezone
    
    @property
    def last_seen_minutes_ago(self):
        """Minutes since last sync"""
        if not self.last_sync:
            return None
        return int((timezone.now() - self.last_sync).total_seconds() / 60)
    
    @property
    def is_recently_online(self):
        """Consider online if last sync was within 2x sync interval"""
        if not self.last_sync:
            return False
        
        max_offline_time = self.group.sync_interval * 2
        time_since_sync = (timezone.now() - self.last_sync).total_seconds()
        return time_since_sync <= max_offline_time
    
    @property
    def sync_status_display(self):
        """Human readable sync status"""
        if self.sync_fail_count == 0:
            return "✅ Healthy"
        elif self.sync_fail_count < 3:
            return f"⚠️ {self.sync_fail_count} failures"
        else:
            return f"❌ {self.sync_fail_count} failures"
    
    @property
    def battery_status_display(self):
        """Human readable battery status"""
        if self.battery_level is None:
            return "Unknown"
        elif self.battery_level > 50:
            return f"🔋 {self.battery_level}%"
        elif self.battery_level > 20:
            return f"🪫 {self.battery_level}%"
        else:
            return f"⚠️ {self.battery_level}%"
    
    @property
    def signal_status_display(self):
        """Human readable signal status"""
        if self.signal_strength is None:
            return "Unknown"
        
        if self.connection_type == 'wifi':
            if self.signal_strength > -50:
                return f"📶 Excellent ({self.signal_strength}dBm)"
            elif self.signal_strength > -70:
                return f"📶 Good ({self.signal_strength}dBm)"
            elif self.signal_strength > -80:
                return f"📶 Fair ({self.signal_strength}dBm)"
            else:
                return f"📶 Poor ({self.signal_strength}dBm)"
        
        return f"📱 {self.signal_strength}dBm"
    
    @property
    def temperature_status_display(self):
        """Human readable temperature status"""
        if self.temperature_celsius is None:
            return "Unknown"
        elif self.temperature_celsius < 60:
            return f"🌡️ Normal ({self.temperature_celsius}°C)"
        elif self.temperature_celsius < 80:
            return f"🌡️ Warm ({self.temperature_celsius}°C)"
        else:
            return f"🌡️ Hot ({self.temperature_celsius}°C)"
    
    # === METHODS ===
    def reset_sync_failures(self):
        """Reset sync failure counter"""
        self.sync_fail_count = 0
        self.save(update_fields=['sync_fail_count'])
    
    def increment_sync_failures(self):
        """Increment sync failure counter"""
        self.sync_fail_count += 1
        if self.sync_fail_count >= 5:
            self.status = 'error'
        self.save(update_fields=['sync_fail_count', 'status'])
    
    def update_health_data(self, health_data):
        """Update health data from device request"""
        self.battery_level = health_data.get('battery_level')
        self.storage_free_mb = health_data.get('storage_free_mb')
        self.temperature_celsius = health_data.get('temperature_celsius')
        self.connection_type = health_data.get('connection_type', 'unknown')
        self.signal_strength = health_data.get('signal_strength')
        
        # Update status to online if device is reporting
        self.status = 'online'
        
        self.save(update_fields=[
            'battery_level', 'storage_free_mb', 'temperature_celsius',
            'connection_type', 'signal_strength', 'status'
        ])

    def get_recent_logs(self, hours=24, level=None):
        """Get recent logs for this player"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        queryset = self.device_logs.filter(device_timestamp__gte=cutoff_time)
        
        if level:
            queryset = queryset.filter(level=level)
        
        return queryset.order_by('-device_timestamp')
    
    @property
    def has_recent_errors(self):
        """Check if player has recent errors"""
        return self.get_recent_logs(hours=1, level='ERROR').exists() or \
               self.get_recent_logs(hours=1, level='FATAL').exists()
    
    @property
    def log_summary(self):
        """Summary of recent logs"""
        recent_logs = self.get_recent_logs(hours=24)
        
        summary = {
            'total': recent_logs.count(),
            'errors': recent_logs.filter(level__in=['ERROR', 'FATAL']).count(),
            'warnings': recent_logs.filter(level='WARN').count(),
        }
        
        return summary
    
    
class SyncLog(models.Model):
    """Log de sincronizaciones para auditoría"""
    SYNC_STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
        ('timeout', 'Timeout'),
    ]
    
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='sync_logs')
    sync_id = models.CharField(max_length=50, help_text="Unique sync identifier")
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=SYNC_STATUS_CHOICES)
    
    # Datos de la sincronización
    assets_synced = models.PositiveIntegerField(default=0)
    bytes_transferred = models.PositiveBigIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Información adicional
    sync_hash = models.CharField(max_length=64, blank=True)
    error_message = models.TextField(blank=True)
    device_info = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Sync Log"
        verbose_name_plural = "Sync Logs"
    
    def __str__(self):
        return f"{self.player.name} - {self.status} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration_display(self):
        """Human readable duration"""
        if not self.duration_seconds:
            return "Unknown"
        
        if self.duration_seconds < 60:
            return f"{self.duration_seconds}s"
        else:
            minutes = self.duration_seconds // 60
            seconds = self.duration_seconds % 60
            return f"{minutes}m {seconds}s"
    
    @property
    def bytes_transferred_display(self):
        """Human readable bytes transferred"""
        if self.bytes_transferred == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.bytes_transferred < 1024.0:
                return f"{self.bytes_transferred:.1f} {unit}"
            self.bytes_transferred /= 1024.0
        
        return f"{self.bytes_transferred:.1f} TB"
    

class DeviceLog(models.Model):
    """Logs centralizados enviados desde dispositivos Android"""
    
    LOG_LEVELS = [
        ('VERBOSE', 'Verbose'),
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARN', 'Warning'),
        ('ERROR', 'Error'),
        ('FATAL', 'Fatal'),
    ]
    
    CATEGORIES = [
        ('SYSTEM', 'System'),
        ('SYNC', 'Synchronization'),
        ('PLAYBACK', 'Playback'),
        ('NETWORK', 'Network'),
        ('STORAGE', 'Storage'),
        ('UI', 'User Interface'),
        ('HARDWARE', 'Hardware'),
        ('APP', 'Application'),
    ]
    
    # Relación con el player
    player = models.ForeignKey(
        Player, 
        on_delete=models.CASCADE, 
        related_name='device_logs'
    )
    
    # Información del log
    timestamp = models.DateTimeField(auto_now_add=True)
    device_timestamp = models.DateTimeField(
        help_text="Timestamp from the device (may differ from server time)"
    )
    
    level = models.CharField(max_length=10, choices=LOG_LEVELS, default='INFO')
    category = models.CharField(max_length=15, choices=CATEGORIES, default='APP')
    
    # Contenido del log
    tag = models.CharField(
        max_length=50, 
        help_text="Log tag (like Android Log.tag)"
    )
    message = models.TextField(help_text="Log message content")
    
    # Información adicional
    thread_name = models.CharField(max_length=50, blank=True)
    method_name = models.CharField(max_length=100, blank=True)
    line_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Para exceptions/stack traces
    exception_class = models.CharField(max_length=100, blank=True)
    stack_trace = models.TextField(blank=True)
    
    # Metadata adicional del device en ese momento
    app_version = models.CharField(max_length=20, blank=True)
    battery_level = models.PositiveIntegerField(null=True, blank=True)
    memory_available_mb = models.PositiveIntegerField(null=True, blank=True)
    
    # JSON para datos adicionales flexibles
    extra_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-device_timestamp', '-timestamp']
        verbose_name = "Device Log"
        verbose_name_plural = "Device Logs"
        indexes = [
            models.Index(fields=['player', '-device_timestamp']),
            models.Index(fields=['level', '-device_timestamp']),
            models.Index(fields=['category', '-device_timestamp']),
            models.Index(fields=['tag', '-device_timestamp']),
        ]
    
    def __str__(self):
        return f"{self.player.name} [{self.level}] {self.tag}: {self.message[:50]}..."
    
    @property
    def level_icon(self):
        """Icon for log level"""
        icons = {
            'VERBOSE': '🔍',
            'DEBUG': '🐛',
            'INFO': 'ℹ️',
            'WARN': '⚠️',
            'ERROR': '❌',
            'FATAL': '💀',
        }
        return icons.get(self.level, '📝')
    
    @property
    def level_color(self):
        """CSS color for log level"""
        colors = {
            'VERBOSE': '#6c757d',  # Gray
            'DEBUG': '#17a2b8',    # Cyan
            'INFO': '#28a745',     # Green
            'WARN': '#ffc107',     # Yellow
            'ERROR': '#dc3545',    # Red
            'FATAL': '#6f42c1',    # Purple
        }
        return colors.get(self.level, '#000000')
    
    @property
    def category_icon(self):
        """Icon for category"""
        icons = {
            'SYSTEM': '⚙️',
            'SYNC': '🔄',
            'PLAYBACK': '▶️',
            'NETWORK': '🌐',
            'STORAGE': '💾',
            'UI': '🖥️',
            'HARDWARE': '🔧',
            'APP': '📱',
        }
        return icons.get(self.category, '📋')
    
    @property
    def short_message(self):
        """Shortened message for list display"""
        if len(self.message) <= 100:
            return self.message
        return self.message[:97] + "..."
    
    @property
    def has_exception(self):
        """Check if log has exception info"""
        return bool(self.exception_class or self.stack_trace)
    
    @classmethod
    def cleanup_old_logs(cls, days_to_keep=30):
        """Clean up logs older than specified days"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        deleted_count = cls.objects.filter(timestamp__lt=cutoff_date).delete()[0]
        return deleted_count
    
    @classmethod
    def get_recent_errors(cls, player=None, hours=24):
        """Get recent error logs"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        queryset = cls.objects.filter(
            timestamp__gte=cutoff_time,
            level__in=['ERROR', 'FATAL']
        )
        
        if player:
            queryset = queryset.filter(player=player)
        
        return queryset.order_by('-timestamp')
    
