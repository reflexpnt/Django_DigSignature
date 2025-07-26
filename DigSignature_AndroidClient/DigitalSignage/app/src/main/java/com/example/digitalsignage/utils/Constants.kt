// utils/Constants.kt

package com.digitalsignage.utils

object Constants {

    // Server Configuration
    const val SERVER_URL = "http://192.168.1.131:8000"
    const val SYNC_INTERVAL_DEBUG = 10_000L // 10 segundos
    const val SYNC_INTERVAL_NORMAL = 300_000L // 5 minutos

    // API Endpoints
    const val API_REGISTER = "/players/api/register/"
    const val API_CHECK_SERVER = "/scheduling/api/v1/device/check_server/"
    const val API_LOG_SINGLE = "/players/api/logs/single/"
    const val API_LOG_BATCH = "/players/api/logs/batch/"
    const val API_DOWNLOAD_ASSET = "/content/api/assets/%s/download/"

    // Device Configuration
    const val DEVICE_ID_LENGTH = 16
    const val DEFAULT_DEVICE_NAME = "DigitalSignage Device"

    // Kiosk Mode
    const val KIOSK_EXIT_TAPS = 5
    const val KIOSK_TAP_TIMEOUT = 2000L // 2 segundos
    const val KIOSK_TAP_CORNER_PERCENTAGE = 0.2f // 20% de la esquina

    // Cache Configuration
    const val CACHE_DIR_ASSETS = "assets"
    const val CACHE_DIR_VIDEOS = "videos"
    const val CACHE_DIR_IMAGES = "images"
    const val CACHE_DIR_HTML = "html"
    const val CACHE_MAX_SIZE_MB = 1024 // 1GB

    // Fallback Content
    const val FALLBACK_VIDEO = "default_video.mp4"
    const val FALLBACK_IMAGE = "default_image.jpg"
    const val FALLBACK_HTML = "error_content.html"

    // Content Types
    const val CONTENT_TYPE_VIDEO = "video"
    const val CONTENT_TYPE_IMAGE = "image"
    const val CONTENT_TYPE_HTML = "html"
    const val CONTENT_TYPE_URL = "url"

    // Layout Types
    const val LAYOUT_FULLSCREEN = "pantalla_completa"
    const val LAYOUT_GRID_2X2 = "grid_2x2"
    const val LAYOUT_SIDEBAR = "sidebar"
    const val LAYOUT_HEADER_FOOTER = "header_footer"

    // Log Configuration
    const val LOG_BATCH_SIZE = 50
    const val LOG_SEND_INTERVAL = 30_000L // 30 segundos
    const val LOG_MAX_LINES = 100

    // Download Configuration
    const val DOWNLOAD_TIMEOUT = 30_000L // 30 segundos
    const val DOWNLOAD_CHUNK_SIZE = 8192 // 8KB
    const val MAX_CONCURRENT_DOWNLOADS = 3

    // Orientation
    const val ORIENTATION_LANDSCAPE = "landscape"
    const val ORIENTATION_PORTRAIT = "portrait"

    // SharedPreferences Keys
    const val PREFS_NAME = "digital_signage_prefs"
    const val PREF_DEVICE_ID = "device_id"
    const val PREF_DEVICE_NAME = "device_name"
    const val PREF_LAST_SYNC = "last_sync"
    const val PREF_LAST_SYNC_HASH = "last_sync_hash"
    const val PREF_IS_REGISTERED = "is_registered"
    const val PREF_ORIENTATION = "orientation"
    const val PREF_IS_MUTED = "is_muted"
    const val PREF_SYNC_INTERVAL = "sync_interval"
    const val PREF_CURRENT_PLAYLIST = "current_playlist"
}