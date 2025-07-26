// utils/Constants.kt

package com.digitalsignage.utils


object Constants {

    // Configuración del servidor
    const val SERVER_URL = "http://192.168.1.131:8000"

    // Configuración de sincronización
    const val SYNC_INTERVAL_DEBUG = 15_000L        // 15 segundos para debug
    const val SYNC_INTERVAL_PRODUCTION = 300_000L  // 5 minutos en producción
    const val SYNC_TIMEOUT_MS = 30_000L            // 30 segundos timeout
    const val SYNC_RETRY_ATTEMPTS = 3              // Reintentos de sync
    const val SYNC_RETRY_DELAY_MS = 5_000L         // 5 segundos entre reintentos

    // Configuración de dispositivo
    const val DEVICE_ID_LENGTH = 16
    const val DEVICE_REGISTRATION_TIMEOUT_MS = 15_000L

    // Configuración de kiosk
    const val KIOSK_EXIT_TAPS = 5
    const val KIOSK_EXIT_TAP_TIMEOUT_MS = 2_000L

    // Configuración de cache y almacenamiento
    const val CACHE_MAX_SIZE_MB = 1024                    // 1GB máximo
    const val CACHE_CLEANUP_THRESHOLD_PERCENT = 90       // Limpiar cuando llegue al 90%
    const val CACHE_MIN_FREE_SPACE_MB = 100              // Mantener 100MB libres mínimo
    const val ASSET_DOWNLOAD_TIMEOUT_MS = 120_000L       // 2 minutos por asset
    const val ASSET_DOWNLOAD_RETRY_ATTEMPTS = 3          // Reintentos de descarga

    // Configuración de logging
    const val LOG_MAX_LINES = 500                        // Máximo logs en UI
    const val LOG_MAX_QUEUE_SIZE = 1000                  // Máximo logs en cola
    const val LOG_SEND_INTERVAL = 2_000L                 // 2 segundos para envío
    const val LOG_BATCH_SIZE = 10                        // Logs por batch
    const val LOG_RETRY_DELAY_MS = 5_000L                // Delay entre reintentos
    const val LOG_FAILURE_NOTIFICATION_INTERVAL = 300_000L // 5 minutos entre advertencias

    // Configuración de descarga
    const val DOWNLOAD_BUFFER_SIZE = 8192                // 8KB buffer para descarga
    const val DOWNLOAD_PROGRESS_UPDATE_INTERVAL = 8192   // Actualizar progreso cada 8KB
    const val MAX_CONCURRENT_DOWNLOADS = 3               // Máximo 3 descargas simultáneas

    // Configuración de verificación de integridad
    const val CHECKSUM_ALGORITHM = "SHA-256"
    const val VERIFY_CHECKSUMS = true                    // Verificar checksums por defecto

    // Configuración de UI
    const val UI_UPDATE_INTERVAL_MS = 1_000L             // Actualizar UI cada segundo
    const val STATUS_UPDATE_INTERVAL_MS = 5_000L         // Actualizar estado cada 5 segundos
    const val BATTERY_UPDATE_INTERVAL_MS = 30_000L       // Actualizar batería cada 30 segundos

    // Configuración de red
    const val NETWORK_CONNECT_TIMEOUT_MS = 30_000L       // 30 segundos conexión
    const val NETWORK_READ_TIMEOUT_MS = 60_000L          // 60 segundos lectura
    const val NETWORK_WRITE_TIMEOUT_MS = 60_000L         // 60 segundos escritura
    const val CONNECTIVITY_CHECK_INTERVAL_MS = 60_000L   // Verificar conectividad cada minuto

    // Configuración de archivos
    const val ASSET_TEMP_EXTENSION = ".tmp"
    const val ASSET_BACKUP_EXTENSION = ".bak"

    // Directorios de assets
    const val DIR_VIDEOS = "videos"
    const val DIR_IMAGES = "images"
    const val DIR_HTML = "html"
    const val DIR_AUDIO = "audio"
    const val DIR_ASSETS = "assets"
    const val DIR_LOGS = "logs"
    const val DIR_CACHE = "digitalsignage"

    // Formatos de archivo soportados
    val SUPPORTED_VIDEO_FORMATS = setOf("mp4", "avi", "mov", "mkv", "webm")
    val SUPPORTED_IMAGE_FORMATS = setOf("jpg", "jpeg", "png", "gif", "bmp", "webp")
    val SUPPORTED_HTML_FORMATS = setOf("html", "htm")
    val SUPPORTED_AUDIO_FORMATS = setOf("mp3", "wav", "aac", "ogg")

    // Configuración de reproducción
    const val DEFAULT_ASSET_DURATION_SECONDS = 30
    const val MIN_ASSET_DURATION_SECONDS = 1
    const val MAX_ASSET_DURATION_SECONDS = 3600         // 1 hora máximo

    // Configuración de emergencia
    const val EMERGENCY_MESSAGE_CHECK_INTERVAL_MS = 10_000L  // Verificar cada 10 segundos
    const val EMERGENCY_MESSAGE_TIMEOUT_MS = 5_000L     // 5 segundos timeout

    // Configuración de salud del dispositivo
    const val HEALTH_UPDATE_INTERVAL_MS = 30_000L       // Actualizar salud cada 30 segundos
    const val BATTERY_LOW_THRESHOLD = 20                // Advertencia de batería baja en 20%
    const val BATTERY_CRITICAL_THRESHOLD = 10           // Batería crítica en 10%
    const val TEMPERATURE_WARNING_CELSIUS = 70          // Advertencia de temperatura en 70°C
    const val TEMPERATURE_CRITICAL_CELSIUS = 80         // Temperatura crítica en 80°C
    const val STORAGE_LOW_THRESHOLD_MB = 500            // Advertencia de almacenamiento en 500MB
    const val STORAGE_CRITICAL_THRESHOLD_MB = 100       // Almacenamiento crítico en 100MB

    // Configuración de debug
    const val DEBUG_MODE = true                         // Modo debug activado
    const val VERBOSE_LOGGING = true                    // Logging verboso
    const val SHOW_PERFORMANCE_LOGS = false             // Logs de rendimiento
    const val SIMULATE_NETWORK_DELAYS = false           // Simular delays de red

    // Versión de la aplicación
    const val APP_VERSION = "1.0.0"
    const val APP_BUILD = "debug"

    // Configuración de preferencias
    const val PREFS_NAME = "DigitalSignagePrefs"
    const val PREFS_DEVICE_ID = "device_id"
    const val PREFS_LAST_SYNC_HASH = "last_sync_hash"
    const val PREFS_LAST_SYNC_TIME = "last_sync_time"
    const val PREFS_SYNC_INTERVAL = "sync_interval"
    const val PREFS_KIOSK_MODE = "kiosk_mode"
    const val PREFS_AUDIO_MUTED = "audio_muted"
    const val PREFS_ORIENTATION = "orientation"
    const val PREFS_LAST_PLAYLIST_ID = "last_playlist_id"
    const val PREFS_SERVER_URL = "server_url"

    // Códigos de resultado
    const val RESULT_SUCCESS = 0
    const val RESULT_ERROR_NETWORK = 1
    const val RESULT_ERROR_STORAGE = 2
    const val RESULT_ERROR_PERMISSION = 3
    const val RESULT_ERROR_DEVICE_NOT_REGISTERED = 4
    const val RESULT_ERROR_SYNC_FAILED = 5
    const val RESULT_ERROR_DOWNLOAD_FAILED = 6
    const val RESULT_ERROR_CHECKSUM_MISMATCH = 7
    const val RESULT_ERROR_INSUFFICIENT_SPACE = 8
    const val RESULT_ERROR_TIMEOUT = 9
    const val RESULT_ERROR_UNKNOWN = 999

    // Mensajes de error comunes
    const val ERROR_NETWORK_UNAVAILABLE = "Network not available"
    const val ERROR_SERVER_UNREACHABLE = "Server unreachable"
    const val ERROR_DEVICE_NOT_REGISTERED = "Device not registered"
    const val ERROR_INSUFFICIENT_STORAGE = "Insufficient storage space"
    const val ERROR_CHECKSUM_MISMATCH = "File integrity check failed"
    const val ERROR_DOWNLOAD_FAILED = "Asset download failed"
    const val ERROR_SYNC_FAILED = "Synchronization failed"
    const val ERROR_PERMISSION_DENIED = "Permission denied"

    // Configuración de notificaciones (si se implementan)
    const val NOTIFICATION_CHANNEL_ID = "digitalsignage_channel"
    const val NOTIFICATION_CHANNEL_NAME = "Digital Signage"
    const val NOTIFICATION_ID_SYNC = 1001
    const val NOTIFICATION_ID_DOWNLOAD = 1002
    const val NOTIFICATION_ID_ERROR = 1003
    const val NOTIFICATION_ID_LOW_BATTERY = 1004
    const val NOTIFICATION_ID_LOW_STORAGE = 1005
}


object MissingConstants {

    // Orientaciones
    const val ORIENTATION_LANDSCAPE = "landscape"
    const val ORIENTATION_PORTRAIT = "portrait"

    // Preferencias
    const val PREF_DEVICE_ID = "device_id"
    const val PREF_DEVICE_NAME = "device_name"
    const val PREF_LAST_SYNC = "last_sync"
    const val PREF_LAST_SYNC_HASH = "last_sync_hash"
    const val PREF_IS_REGISTERED = "is_registered"
    const val PREF_ORIENTATION = "orientation"
    const val PREF_IS_MUTED = "is_muted"
    const val PREF_SYNC_INTERVAL = "sync_interval"
    const val PREF_CURRENT_PLAYLIST = "current_playlist"

    // Valores por defecto
    const val DEFAULT_DEVICE_NAME = "Android Device"

    // Directorios de cache
    const val CACHE_DIR_VIDEOS = "videos"
    const val CACHE_DIR_IMAGES = "images"
    const val CACHE_DIR_HTML = "html"
    const val CACHE_DIR_ASSETS = "assets"

    // Tipos de contenido
    const val CONTENT_TYPE_VIDEO = "video"
    const val CONTENT_TYPE_IMAGE = "image"
    const val CONTENT_TYPE_HTML = "html"

    // Archivos fallback
    const val FALLBACK_VIDEO = "default_video.mp4"
    const val FALLBACK_IMAGE = "default_image.jpg"
    const val FALLBACK_HTML = "default_content.html"

    // Kiosk
    const val KIOSK_TAP_CORNER_PERCENTAGE = 10
    const val KIOSK_TAP_TIMEOUT = 2000L

    // API
    const val API_REGISTER = "/players/api/register/"
}