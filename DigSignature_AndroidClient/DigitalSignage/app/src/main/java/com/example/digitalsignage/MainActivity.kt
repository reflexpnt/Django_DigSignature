// MainActivity.kt

package com.digitalsignage

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.os.Bundle
import android.view.MotionEvent
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.digitalsignage.managers.*
import com.digitalsignage.network.ApiClient
import com.digitalsignage.storage.FileManager
import com.digitalsignage.storage.PreferencesManager
import com.digitalsignage.utils.Constants
import com.digitalsignage.utils.DeviceUtils
import com.digitalsignage.utils.Logger
import kotlinx.coroutines.*

class MainActivity : AppCompatActivity() {

    // UI Components
    private lateinit var contentContainer: FrameLayout
    private lateinit var logTextView: TextView
    private lateinit var logScrollView: ScrollView
    private lateinit var controlPanel: LinearLayout

    // Botones de control
    private lateinit var btnToggleKiosk: Button
    private lateinit var btnToggleLog: Button
    private lateinit var btnSync: Button
    private lateinit var btnRotate: Button
    private lateinit var btnMute: Button
    private lateinit var btnCopyLog: Button
    private lateinit var btnClearCache: Button
    private lateinit var btnDebug: Button

    // Indicadores de estado
    private lateinit var deviceIdText: TextView
    private lateinit var syncStatusText: TextView
    private lateinit var batteryText: TextView
    private lateinit var kioskIndicator: TextView

    // Managers principales
    private lateinit var preferencesManager: PreferencesManager
    private lateinit var logger: Logger
    private lateinit var apiClient: ApiClient
    private lateinit var deviceManager: DeviceManager
    private lateinit var syncManager: SyncManager
    private lateinit var kioskManager: KioskManager
    private lateinit var fileManager: FileManager
    private lateinit var assetManager: AssetManager
    private lateinit var playlistManager: PlaylistManager

    // Estado de la aplicación
    private var isDebugMode = true // TODO: Configurar según build
    private var showLog = true
    private var initialSyncCompleted = false

    // Coroutines
    private var statusUpdateJob: Job? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        initializeBasicManagers()  // ← PRIMERO: Logger y básicos
        initializeUI()             // ← SEGUNDO: UI (necesita logger)
        initializeManagers()       // ← TERCERO: Resto de managers (necesita UI)
        setupEventListeners()
        startApplication()

        // Configurar visibilidad inicial DESPUÉS de que todo esté inicializado
        updateUIVisibility()
    }

    /**
     * Inicializa managers básicos que no dependen de UI
     */
    private fun initializeBasicManagers() {
        // Managers básicos
        preferencesManager = PreferencesManager(this)
        apiClient = ApiClient(this)
        logger = Logger(this, preferencesManager.deviceId)
        fileManager = FileManager(this, logger)

        logger.i(Logger.Category.APP, "DigitalSignage App Initialized")
        logger.i(Logger.Category.SYSTEM, "Device ID: ${preferencesManager.deviceId}")
    }

    /**
     * Inicializa managers que dependen de UI
     */
    private fun initializeManagers() {
        // Managers de funcionalidad (necesitan UI)
        deviceManager = DeviceManager(this, apiClient, preferencesManager, logger)
        syncManager = SyncManager(this, apiClient, preferencesManager, logger)
        kioskManager = KioskManager(this, preferencesManager, logger)
        assetManager = AssetManager(this, apiClient, fileManager, logger)
        playlistManager = PlaylistManager(this, contentContainer, logger, fileManager, assetManager)
    }

    /**
     * Inicializa componentes de UI
     */
    private fun initializeUI() {
        // Contenedores principales
        contentContainer = findViewById(R.id.content_container)
        logScrollView = findViewById(R.id.log_scroll_view)
        logTextView = findViewById(R.id.log_text_view)
        controlPanel = findViewById(R.id.control_panel)

        // Botones de control
        btnToggleKiosk = findViewById(R.id.btn_toggle_kiosk)
        btnToggleLog = findViewById(R.id.btn_toggle_log)
        btnSync = findViewById(R.id.btn_sync)
        btnRotate = findViewById(R.id.btn_rotate)
        btnMute = findViewById(R.id.btn_mute)
        btnCopyLog = findViewById(R.id.btn_copy_log)
        btnClearCache = findViewById(R.id.btn_clear_cache)
        btnDebug = findViewById(R.id.btn_debug)

        // Indicadores de estado
        deviceIdText = findViewById(R.id.device_id_text)
        syncStatusText = findViewById(R.id.sync_status_text)
        batteryText = findViewById(R.id.battery_text)
        kioskIndicator = findViewById(R.id.kiosk_indicator)

        // Configurar callback del logger para actualizar UI
        logger.onLogAdded = { logMessage ->
            runOnUiThread {
                updateLogDisplay()
            }
        }

        // Mostrar Device ID completo
        deviceIdText.text = "${preferencesManager.deviceId}"

        // NO llamar updateUIVisibility aquí - se hará después de inicializar managers
    }

    /**
     * Configura los event listeners
     */
    private fun setupEventListeners() {

        // Toggle Kiosk Mode
        btnToggleKiosk.setOnClickListener {
            kioskManager.toggleKioskMode()
            updateUIVisibility()
        }

        // Toggle Log Display
        btnToggleLog.setOnClickListener {
            showLog = !showLog
            updateLogVisibility()
        }

        // Manual Sync
        btnSync.setOnClickListener {
            lifecycleScope.launch {
                performManualSync()
            }
        }

        // Rotate Screen
        btnRotate.setOnClickListener {
            kioskManager.toggleOrientation()
            logger.i(Logger.Category.UI, "Orientation toggled to: ${preferencesManager.orientation}")
        }

        // Toggle Mute
        btnMute.setOnClickListener {
            toggleMute()
        }

        // Copy Logs to Clipboard
        btnCopyLog.setOnClickListener {
            copyLogsToClipboard()
        }

        // Clear Cache
        btnClearCache.setOnClickListener {
            clearCache()
        }

        // Debug Info
        btnDebug.setOnClickListener {
            showDebugInfo()
        }

        // Callbacks de managers
        setupManagerCallbacks()
    }

    /**
     * Configura callbacks de los managers
     */
    private fun setupManagerCallbacks() {

        // Callback de sincronización completada
        syncManager.onSyncCompleted = { syncData ->
            runOnUiThread {
                syncStatusText.text = "✅ Synced"
                syncStatusText.setTextColor(getColor(android.R.color.holo_green_light))

                // Actualizar playlist si cambió
                syncData.playlist?.let { playlist ->
                    playlistManager.updatePlaylist(playlist, syncData.assets)
                }

                if (!initialSyncCompleted) {
                    initialSyncCompleted = true
                    logger.i(Logger.Category.SYNC, "Initial sync completed successfully")
                }
            }
        }

        // Callback de error de sincronización
        syncManager.onSyncError = { errorMessage ->
            runOnUiThread {
                syncStatusText.text = "❌ Error"
                syncStatusText.setTextColor(getColor(android.R.color.holo_red_light))

                // Si no se ha completado la sync inicial, usar fallback
                if (!initialSyncCompleted) {
                    logger.w(Logger.Category.SYNC, "Initial sync failed, using fallback content")
                    playlistManager.playFallbackContent()
                }
            }
        }

        // Callback de salida del modo kiosk
        kioskManager.onKioskExitDetected = {
            logger.i(Logger.Category.UI, "Kiosk exit sequence detected")
            kioskManager.disableKioskMode()
            updateUIVisibility()
        }

        // Callback de progreso de descarga
        assetManager.onDownloadProgress = { assetId, progress ->
            // TODO: Mostrar progreso en UI si es necesario
            logger.d(Logger.Category.STORAGE, "Download progress $assetId: $progress%")
        }
    }

    /**
     * Inicia la aplicación
     */
    private fun startApplication() {
        logger.i(Logger.Category.APP, "Starting Digital Signage Application")

        // DEBUGGING: No iniciar en modo kiosk automáticamente
        // kioskManager.enableKioskMode()
        logger.w(Logger.Category.APP, "Kiosk mode disabled for debugging")

        // Iniciar actualizaciones de estado
        startStatusUpdates()

        // Iniciar con contenido fallback
        playlistManager.playFallbackContent()

        // Registrar dispositivo y comenzar sincronización
        lifecycleScope.launch {
            try {
                logger.i(Logger.Category.SYSTEM, "Starting device registration...")

                // Asegurar registro del dispositivo
                when (val result = deviceManager.ensureDeviceRegistered()) {
                    is DeviceManager.RegistrationResult.Success -> {
                        logger.i(Logger.Category.SYSTEM, "✅ Device registration completed successfully")
                        startSyncProcess()
                    }
                    is DeviceManager.RegistrationResult.AlreadyRegistered -> {
                        logger.i(Logger.Category.SYSTEM, "✅ Device already registered")
                        startSyncProcess()
                    }
                    is DeviceManager.RegistrationResult.Error -> {
                        logger.e(Logger.Category.SYSTEM, "❌ Device registration failed: ${result.message}")
                        // Continuar con contenido fallback
                    }
                }
            } catch (e: Exception) {
                logger.e(Logger.Category.APP, "Error during app startup", exception = e)
            }
        }

        // updateUIVisibility() se llama en onCreate() al final
    }

    /**
     * Inicia el proceso de sincronización
     */
    private fun startSyncProcess() {
        logger.i(Logger.Category.SYNC, "Starting sync process")

        // Realizar sync inicial
        lifecycleScope.launch {
            performManualSync()
        }

        // Iniciar sync periódico
        syncManager.startPeriodicSync()
    }

    /**
     * Realiza una sincronización manual
     */
    private suspend fun performManualSync() {
        runOnUiThread {
            syncStatusText.text = "⏳ Syncing..."
            syncStatusText.setTextColor(getColor(android.R.color.holo_orange_light))
        }

        logger.i(Logger.Category.SYNC, "Manual sync requested")

        try {
            val result = syncManager.performSync()

            when (result) {
                is SyncManager.SyncResult.Success -> {
                    logger.i(Logger.Category.SYNC, "Manual sync completed successfully")
                }
                is SyncManager.SyncResult.NoUpdates -> {
                    logger.i(Logger.Category.SYNC, "Manual sync: no updates needed")
                    runOnUiThread {
                        syncStatusText.text = "✅ Up to date"
                        syncStatusText.setTextColor(getColor(android.R.color.holo_green_light))
                    }
                }
                is SyncManager.SyncResult.Error -> {
                    logger.e(Logger.Category.SYNC, "Manual sync failed: ${result.message}")
                }
            }
        } catch (e: Exception) {
            logger.e(Logger.Category.SYNC, "Manual sync exception", exception = e)
        }
    }

    /**
     * Inicia actualizaciones periódicas de estado
     */
    private fun startStatusUpdates() {
        statusUpdateJob = lifecycleScope.launch {
            while (isActive) {
                try {
                    updateStatusIndicators()
                    delay(5000) // Actualizar cada 5 segundos
                } catch (e: Exception) {
                    logger.w(Logger.Category.UI, "Error updating status", exception = e)
                    delay(10000) // Esperar más tiempo si hay error
                }
            }
        }
    }

    /**
     * Actualiza los indicadores de estado
     */
    private fun updateStatusIndicators() {
        val healthData = DeviceUtils.getHealthData(this)

        runOnUiThread {
            // Actualizar batería
            val batteryIcon = when {
                healthData.batteryLevel > 75 -> "🔋"
                healthData.batteryLevel > 50 -> "🔋"
                healthData.batteryLevel > 25 -> "🪫"
                else -> "🪫"
            }
            batteryText.text = "$batteryIcon ${healthData.batteryLevel}%"

            // Cambiar color según nivel de batería
            val batteryColor = when {
                healthData.batteryLevel > 50 -> android.R.color.holo_green_light
                healthData.batteryLevel > 25 -> android.R.color.holo_orange_light
                else -> android.R.color.holo_red_light
            }
            batteryText.setTextColor(getColor(batteryColor))
        }
    }

    /**
     * Actualiza la visibilidad de elementos UI según el modo
     */
    private fun updateUIVisibility() {
        val isKiosk = kioskManager.isKioskModeEnabled()

        // Panel de controles: visible solo en modo debug y no-kiosk
        controlPanel.visibility = if (isDebugMode && !isKiosk) View.VISIBLE else View.GONE

        // Indicador de kiosk
        kioskIndicator.visibility = if (isKiosk) View.VISIBLE else View.GONE

        // Actualizar texto del botón kiosk
        btnToggleKiosk.text = if (isKiosk) "Exit Kiosk" else "Enter Kiosk"
        btnToggleKiosk.setBackgroundColor(
            getColor(if (isKiosk) android.R.color.holo_red_dark else android.R.color.holo_green_dark)
        )

        updateLogVisibility()
        updateMuteButton()
    }

    /**
     * Actualiza la visibilidad del log
     */
    private fun updateLogVisibility() {
        val shouldShowLog = showLog && (isDebugMode || !kioskManager.isKioskModeEnabled())

        logScrollView.visibility = if (shouldShowLog) View.VISIBLE else View.GONE

        btnToggleLog.text = if (showLog) "Hide Log" else "Show Log"
        btnToggleLog.setBackgroundColor(
            getColor(if (showLog) android.R.color.holo_blue_dark else android.R.color.holo_blue_light)
        )
    }

    /**
     * Actualiza el display de logs
     */
    private fun updateLogDisplay() {
        val logs = logger.getLocalLogs()
        val logText = logs.takeLast(50).joinToString("\n") // Mostrar últimos 50 logs

        logTextView.text = logText

        // Auto-scroll al final
        logScrollView.post {
            logScrollView.fullScroll(View.FOCUS_DOWN)
        }
    }

    /**
     * Alterna el estado de mute
     */
    private fun toggleMute() {
        preferencesManager.isMuted = !preferencesManager.isMuted

        // Aplicar mute al playlist manager
        playlistManager.setMuted(preferencesManager.isMuted)

        logger.i(Logger.Category.UI, "Audio ${if (preferencesManager.isMuted) "muted" else "unmuted"}")
        updateMuteButton()
    }

    /**
     * Actualiza el botón de mute
     */
    private fun updateMuteButton() {
        val isMuted = preferencesManager.isMuted
        btnMute.text = if (isMuted) "Unmute" else "Mute"
        btnMute.setBackgroundColor(
            getColor(if (isMuted) android.R.color.holo_red_light else android.R.color.holo_purple)
        )
    }

    /**
     * Copia logs al portapapeles
     */
    private fun copyLogsToClipboard() {
        try {
            val logs = logger.getLocalLogs()
            val logText = logs.joinToString("\n")

            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("DigitalSignage Logs", logText)
            clipboard.setPrimaryClip(clip)

            logger.i(Logger.Category.UI, "Logs copied to clipboard (${logs.size} entries)")
            Toast.makeText(this, "Logs copied to clipboard", Toast.LENGTH_SHORT).show()

        } catch (e: Exception) {
            logger.e(Logger.Category.UI, "Error copying logs", exception = e)
            Toast.makeText(this, "Error copying logs", Toast.LENGTH_SHORT).show()
        }
    }

    /**
     * Limpia el cache
     */
    private fun clearCache() {
        lifecycleScope.launch {
            try {
                logger.w(Logger.Category.STORAGE, "Manual cache clear requested")

                val success = fileManager.clearAllCache()

                runOnUiThread {
                    if (success) {
                        Toast.makeText(this@MainActivity, "Cache cleared successfully", Toast.LENGTH_SHORT).show()
                        logger.i(Logger.Category.STORAGE, "Cache cleared by user")
                    } else {
                        Toast.makeText(this@MainActivity, "Error clearing cache", Toast.LENGTH_SHORT).show()
                    }
                }

                // Forzar re-descarga en próximo sync
                syncManager.forceClearCache()

            } catch (e: Exception) {
                logger.e(Logger.Category.STORAGE, "Error clearing cache", exception = e)
                runOnUiThread {
                    Toast.makeText(this@MainActivity, "Error clearing cache", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    /**
     * Muestra información de debug
     */
    private fun showDebugInfo() {
        val deviceInfo = deviceManager.exportDeviceInfo()
        val syncStats = syncManager.getSyncStats()
        val kioskStatus = kioskManager.getKioskStatus()
        val storageInfo = fileManager.getStorageInfo()

        val debugText = buildString {
            appendLine("=== DEBUG INFO ===")
            appendLine("Device: ${deviceInfo["device_id"]}")
            appendLine("Registered: ${deviceInfo["is_registered"]}")
            appendLine("Last Sync: ${syncStats["last_sync"]}")
            appendLine("Sync Hash: ${syncStats["last_sync_hash"]}")
            appendLine("Kiosk: ${kioskStatus["kiosk_enabled"]}")
            appendLine("Orientation: ${kioskStatus["orientation"]}")
            appendLine("Cache Size: ${storageInfo["cache_size"]}")
            appendLine("Cache Usage: ${storageInfo["cache_usage_percent"]}")
            appendLine("Total Files: ${storageInfo["total_files"]}")
            appendLine("================")
        }

        logger.i(Logger.Category.APP, "Debug info displayed")
        logger.d(Logger.Category.APP, debugText)

        Toast.makeText(this, "Debug info logged", Toast.LENGTH_SHORT).show()
    }

    /**
     * Maneja toques en pantalla para detección de salida de kiosk
     */
    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (event.action == MotionEvent.ACTION_DOWN) {
            val screenWidth = resources.displayMetrics.widthPixels
            val screenHeight = resources.displayMetrics.heightPixels

            val handled = kioskManager.handleTouch(
                event.x,
                event.y,
                screenWidth,
                screenHeight
            )

            if (handled) {
                updateUIVisibility()
                return true
            }
        }

        return super.onTouchEvent(event)
    }

    /**
     * Lifecycle methods
     */
    override fun onResume() {
        super.onResume()
        kioskManager.reinforceKioskMode()
        logger.d(Logger.Category.APP, "Activity resumed")
    }

    override fun onPause() {
        super.onPause()
        logger.d(Logger.Category.APP, "Activity paused")
    }

    @Suppress("DEPRECATION", "OVERRIDE_DEPRECATION")
    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        kioskManager.onWindowFocusChanged(hasFocus)
    }

    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        if (kioskManager.isKioskModeEnabled()) {
            // En modo kiosk, ignorar botón de back
            logger.d(Logger.Category.UI, "Back button pressed in kiosk mode - ignored")
            return
        }
        super.onBackPressed()
    }

    override fun onDestroy() {
        super.onDestroy()

        // Limpiar recursos
        statusUpdateJob?.cancel()
        syncManager.shutdown()
        logger.shutdown()

        logger.i(Logger.Category.APP, "Application destroyed")
    }
}