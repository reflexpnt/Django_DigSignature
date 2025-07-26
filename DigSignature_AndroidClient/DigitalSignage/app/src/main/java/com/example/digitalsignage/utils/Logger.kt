// utils/Logger.kt

package com.digitalsignage.utils

import android.content.Context
import android.util.Log as AndroidLog
import com.digitalsignage.network.ApiClient
import kotlinx.coroutines.*
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.atomic.AtomicInteger

class Logger(
    private val context: Context,
    private val deviceId: String
) {

    enum class Level(val value: String) {
        VERBOSE("VERBOSE"),
        DEBUG("DEBUG"),
        INFO("INFO"),
        WARN("WARN"),
        ERROR("ERROR"),
        FATAL("FATAL")
    }

    enum class Category(val value: String) {
        SYSTEM("SYSTEM"),
        SYNC("SYNC"),
        PLAYBACK("PLAYBACK"),
        NETWORK("NETWORK"),
        STORAGE("STORAGE"),
        UI("UI"),
        HARDWARE("HARDWARE"),
        APP("APP")
    }

    data class LogEntry(
        val deviceTimestamp: String,
        val level: String,
        val category: String,
        val tag: String,
        val message: String,
        val threadName: String,
        val methodName: String? = null,
        val lineNumber: Int? = null,
        val exceptionClass: String? = null,
        val stackTrace: String? = null,
        val extraData: Map<String, Any>? = null
    )

    // Configuración
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US)
    private var apiClient: ApiClient? = null

    // Gestión de logs locales para UI
    private val localLogs = mutableListOf<String>()
    private val maxLocalLogs = Constants.LOG_MAX_LINES

    // Sistema de envío de logs
    private val logQueue = ConcurrentLinkedQueue<LogEntry>()
    private val logScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var logSenderJob: Job? = null
    private val failedLogsCounter = AtomicInteger(0)
    private var lastFailureLogTime = 0L

    // Callbacks para UI
    var onLogAdded: ((String) -> Unit)? = null

    init {
        dateFormat.timeZone = TimeZone.getTimeZone("UTC")
        startLogSender()
    }

    /**
     * Establece el ApiClient para envío de logs
     */
    fun setApiClient(apiClient: ApiClient) {
        this.apiClient = apiClient
        apiClient.setLogger(this)
    }

    /**
     * Log principal con todos los parámetros
     */
    fun log(
        level: Level,
        category: Category,
        message: String,
        tag: String,
        exception: Throwable? = null,
        extraData: Map<String, Any>? = null
    ) {
        val timestamp = dateFormat.format(Date())
        val threadName = Thread.currentThread().name

        // Crear entrada de log
        val logEntry = LogEntry(
            deviceTimestamp = timestamp,
            level = level.value,
            category = category.value,
            tag = tag,
            message = message,
            threadName = threadName,
            exceptionClass = exception?.javaClass?.simpleName,
            stackTrace = exception?.stackTraceToString(),
            extraData = extraData
        )

        // Log local para Android Logcat
        when (level) {
            Level.VERBOSE -> AndroidLog.v(tag, message, exception)
            Level.DEBUG -> AndroidLog.d(tag, message, exception)
            Level.INFO -> AndroidLog.i(tag, message, exception)
            Level.WARN -> AndroidLog.w(tag, message, exception)
            Level.ERROR -> AndroidLog.e(tag, message, exception)
            Level.FATAL -> AndroidLog.wtf(tag, message, exception)
        }

        // Agregar a cola para envío al servidor (inmediato)
        queueLogForSending(logEntry)

        // Agregar a logs locales para UI
        val formattedLog = formatLogForUI(logEntry)
        synchronized(localLogs) {
            localLogs.add(formattedLog)

            // Mantener solo los últimos N logs para UI
            if (localLogs.size > maxLocalLogs) {
                localLogs.removeAt(0)
            }
        }

        // Notificar a UI
        onLogAdded?.invoke(formattedLog)
    }

    /**
     * Métodos de conveniencia para logging rápido
     */
    fun v(category: Category, message: String, tag: String = "DigitalSignage") {
        log(Level.VERBOSE, category, message, tag)
    }

    fun d(category: Category, message: String, tag: String = "DigitalSignage") {
        log(Level.DEBUG, category, message, tag)
    }

    fun i(category: Category, message: String, tag: String = "DigitalSignage") {
        log(Level.INFO, category, message, tag)
    }

    fun w(category: Category, message: String, tag: String = "DigitalSignage", exception: Throwable? = null) {
        log(Level.WARN, category, message, tag, exception)
    }

    fun e(category: Category, message: String, tag: String = "DigitalSignage", exception: Throwable? = null) {
        log(Level.ERROR, category, message, tag, exception)
    }

    fun wtf(category: Category, message: String, tag: String = "DigitalSignage", exception: Throwable? = null) {
        log(Level.FATAL, category, message, tag, exception)
    }

    /**
     * Logs específicos para diferentes eventos
     */
    fun logSync(message: String, exception: Throwable? = null) {
        val level = if (exception != null) Level.ERROR else Level.INFO
        log(level, Category.SYNC, message, "SyncManager", exception)
    }

    fun logPlayback(message: String, exception: Throwable? = null) {
        val level = if (exception != null) Level.ERROR else Level.INFO
        log(level, Category.PLAYBACK, message, "PlaylistManager", exception)
    }

    fun logNetwork(message: String, exception: Throwable? = null) {
        val level = if (exception != null) Level.ERROR else Level.INFO
        log(level, Category.NETWORK, message, "NetworkManager", exception)
    }

    /**
     * Encola un log para envío inmediato al servidor
     */
    private fun queueLogForSending(logEntry: LogEntry) {
        logQueue.offer(logEntry)

        // Si la cola está creciendo demasiado, remover logs antiguos
        while (logQueue.size > Constants.LOG_MAX_QUEUE_SIZE) {
            logQueue.poll()
        }
    }

    /**
     * Inicia el servicio de envío de logs al servidor
     */
    private fun startLogSender() {
        logSenderJob = logScope.launch {
            while (isActive) {
                try {
                    sendQueuedLogsToServer()
                    delay(Constants.LOG_SEND_INTERVAL)
                } catch (e: Exception) {
                    // No logear errores de envío para evitar loops infinitos
                    AndroidLog.e("Logger", "Error in log sender", e)
                    delay(Constants.LOG_SEND_INTERVAL * 2) // Esperar más tiempo en caso de error
                }
            }
        }
    }

    /**
     * Envía logs encolados al servidor
     */
    private suspend fun sendQueuedLogsToServer() {
        if (apiClient == null) return

        val logsToSend = mutableListOf<LogEntry>()

        // Extraer logs de la cola (máximo batch size para no sobrecargar)
        repeat(Constants.LOG_BATCH_SIZE) {
            val log = logQueue.poll()
            if (log != null) {
                logsToSend.add(log)
            }
        }

        if (logsToSend.isEmpty()) return

        try {
            // Enviar logs individuales inmediatamente
            for (logEntry in logsToSend) {
                sendLogEntryImmediately(logEntry)
            }

            // Reset del contador de errores en caso de éxito
            if (failedLogsCounter.get() > 0) {
                failedLogsCounter.set(0)
            }

        } catch (e: Exception) {
            // Re-encolar logs si falló el envío
            logsToSend.forEach { entry ->
                logQueue.offer(entry)
            }

            handleLogSendingFailure()
            throw e
        }
    }

    /**
     * Envía un log individual inmediatamente al servidor
     */
    private suspend fun sendLogEntryImmediately(logEntry: LogEntry) {
        val apiClient = this.apiClient ?: return

        try {
            val logData = JSONObject().apply {
                put("device_id", deviceId)
                put("timestamp", logEntry.deviceTimestamp)
                put("level", logEntry.level)
                put("category", logEntry.category)
                put("tag", logEntry.tag)
                put("message", logEntry.message)
                put("thread_name", logEntry.threadName)

                logEntry.methodName?.let { put("method_name", it) }
                logEntry.lineNumber?.let { put("line_number", it) }
                logEntry.exceptionClass?.let { put("exception_class", it) }
                logEntry.stackTrace?.let { put("stack_trace", it) }
                logEntry.extraData?.let {
                    put("extra_data", JSONObject(it))
                }
            }

            val response = apiClient.sendLogEntry(logData)

            if (!response.isSuccessful) {
                // Re-encolar si falló
                logQueue.offer(logEntry)
                throw Exception("Server returned ${response.code()}: ${response.message()}")
            }

        } catch (e: Exception) {
            // Re-encolar el log que falló
            logQueue.offer(logEntry)
            throw e
        }
    }

    /**
     * Maneja fallos en el envío de logs
     */
    private fun handleLogSendingFailure() {
        val currentFailures = failedLogsCounter.incrementAndGet()
        val currentTime = System.currentTimeMillis()

        // Solo logear advertencia de fallo una vez cada 5 minutos para evitar spam
        if (currentTime - lastFailureLogTime > 300_000) { // 5 minutos
            val warningMessage = "Failed to send logs to server (failure count: $currentFailures)"

            // Crear log de advertencia pero NO enviarlo al servidor para evitar loop
            val warningLogEntry = LogEntry(
                deviceTimestamp = dateFormat.format(Date()),
                level = Level.WARN.value,
                category = Category.NETWORK.value,
                tag = "LogSender",
                message = warningMessage,
                threadName = Thread.currentThread().name
            )

            // Solo agregar a logs locales y Android Logcat
            AndroidLog.w("LogSender", warningMessage)

            val formattedLog = formatLogForUI(warningLogEntry)
            synchronized(localLogs) {
                localLogs.add(formattedLog)
                if (localLogs.size > maxLocalLogs) {
                    localLogs.removeAt(0)
                }
            }
            onLogAdded?.invoke(formattedLog)

            lastFailureLogTime = currentTime
        }
    }

    /**
     * Envía un log crítico inmediatamente (para eventos importantes)
     */
    suspend fun sendCriticalLogImmediately(
        level: Level,
        category: Category,
        message: String,
        tag: String = "DigitalSignage",
        exception: Throwable? = null
    ) {
        // Crear el log entry
        val logEntry = LogEntry(
            deviceTimestamp = dateFormat.format(Date()),
            level = level.value,
            category = category.value,
            tag = tag,
            message = message,
            threadName = Thread.currentThread().name,
            exceptionClass = exception?.javaClass?.simpleName,
            stackTrace = exception?.stackTraceToString()
        )

        // Log local inmediato
        when (level) {
            Level.ERROR -> AndroidLog.e(tag, message, exception)
            Level.FATAL -> AndroidLog.wtf(tag, message, exception)
            Level.WARN -> AndroidLog.w(tag, message, exception)
            else -> AndroidLog.i(tag, message, exception)
        }

        // Agregar a UI
        val formattedLog = formatLogForUI(logEntry)
        synchronized(localLogs) {
            localLogs.add(formattedLog)
            if (localLogs.size > maxLocalLogs) {
                localLogs.removeAt(0)
            }
        }
        onLogAdded?.invoke(formattedLog)

        // Intentar envío inmediato al servidor
        try {
            sendLogEntryImmediately(logEntry)
        } catch (e: Exception) {
            // Si falla, encolar para reintento posterior
            logQueue.offer(logEntry)
        }
    }

    /**
     * Formatea log para mostrar en UI
     */
    private fun formatLogForUI(entry: LogEntry): String {
        val time = entry.deviceTimestamp.substring(11, 19) // Solo HH:mm:ss
        val levelIcon = when (entry.level) {
            "VERBOSE" -> "🔍"
            "DEBUG" -> "🐛"
            "INFO" -> "ℹ️"
            "WARN" -> "⚠️"
            "ERROR" -> "❌"
            "FATAL" -> "💥"
            else -> "📝"
        }

        return "$time $levelIcon [${entry.category}] ${entry.message}"
    }

    /**
     * Obtiene todos los logs locales para mostrar en UI
     */
    fun getLocalLogs(): List<String> {
        synchronized(localLogs) {
            return localLogs.toList()
        }
    }

    /**
     * Limpia logs locales
     */
    fun clearLocalLogs() {
        synchronized(localLogs) {
            localLogs.clear()
        }
        i(Category.UI, "Local logs cleared")
        onLogAdded?.invoke("=== LOGS CLEARED ===")
    }

    /**
     * Obtiene estadísticas del logger
     */
    fun getLoggerStats(): Map<String, Any> {
        return mapOf(
            "local_logs_count" to localLogs.size,
            "queued_logs_count" to logQueue.size,
            "failed_sends_count" to failedLogsCounter.get(),
            "sender_active" to (logSenderJob?.isActive ?: false),
            "last_failure_time" to if (lastFailureLogTime > 0) {
                SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date(lastFailureLogTime))
            } else "Never"
        )
    }

    /**
     * Fuerza el envío inmediato de todos los logs en cola
     */
    suspend fun flushLogsToServer(): Boolean {
        return try {
            sendQueuedLogsToServer()
            logQueue.isEmpty()
        } catch (e: Exception) {
            AndroidLog.e("Logger", "Error flushing logs", e)
            false
        }
    }

    /**
     * Configura el nivel mínimo de logs a enviar al servidor
     */
    fun setMinimumLogLevel(level: Level) {
        // TODO: Implementar filtrado por nivel si es necesario
        i(Category.SYSTEM, "Minimum log level set to ${level.value}")
    }

    /**
     * Exporta logs para debugging
     */
    fun exportLogsForDebugging(): String {
        val logs = getLocalLogs()
        val header = """
            === DIGITAL SIGNAGE LOGS EXPORT ===
            Device ID: $deviceId
            Export Time: ${SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(Date())}
            Total Logs: ${logs.size}
            Queued for Server: ${logQueue.size}
            Failed Sends: ${failedLogsCounter.get()}
            =====================================
            
        """.trimIndent()

        return header + logs.joinToString("\n")
    }

    /**
     * Detiene el logger y limpia recursos
     */
    fun cleanup() {
        i(Category.SYSTEM, "Logger shutting down")

        // Intentar enviar logs pendientes
        logScope.launch {
            try {
                sendQueuedLogsToServer()
            } catch (e: Exception) {
                AndroidLog.e("Logger", "Error sending final logs", e)
            }
        }

        // Cancelar trabajos
        logSenderJob?.cancel()
        logScope.cancel()

        // Limpiar colas
        logQueue.clear()
        synchronized(localLogs) {
            localLogs.clear()
        }
    }

    /**
     * Reestablece la conexión del logger (útil después de errores de red)
     */
    fun reconnect() {
        i(Category.NETWORK, "Logger reconnecting...")
        failedLogsCounter.set(0)
        lastFailureLogTime = 0L

        // Reiniciar sender si no está activo
        if (logSenderJob?.isActive != true) {
            startLogSender()
        }
    }

    /**
     * Métodos específicos para casos comunes
     */
    fun logAppStart() {
        i(Category.APP, "Digital Signage App started")
    }

    fun logAppStop() {
        i(Category.APP, "Digital Signage App stopping")
    }

    fun logSyncStart() {
        i(Category.SYNC, "Synchronization started")
    }

    fun logSyncSuccess(assetsCount: Int) {
        i(Category.SYNC, "Sync completed successfully. Assets processed: $assetsCount")
    }

    fun logSyncError(error: String) {
        e(Category.SYNC, "Sync failed: $error")
    }

    fun logDownloadStart(assetName: String) {
        i(Category.STORAGE, "Download started: $assetName")
    }

    fun logDownloadSuccess(assetName: String, sizeBytes: Long) {
        i(Category.STORAGE, "Download completed: $assetName (${sizeBytes / 1024}KB)")
    }

    fun logDownloadError(assetName: String, error: String) {
        e(Category.STORAGE, "Download failed: $assetName - $error")
    }

    fun logPlaylistChange(newPlaylist: String) {
        i(Category.PLAYBACK, "Playlist changed to: $newPlaylist")
    }

    fun logKioskModeChange(enabled: Boolean) {
        i(Category.UI, "Kiosk mode ${if (enabled) "enabled" else "disabled"}")
    }

    fun logNetworkChange(connectionType: String) {
        i(Category.NETWORK, "Network connection changed to: $connectionType")
    }

    fun logStorageWarning(freeSpaceMB: Long) {
        w(Category.STORAGE, "Low storage warning: ${freeSpaceMB}MB free")
    }

    fun logBatteryWarning(level: Int) {
        w(Category.HARDWARE, "Low battery warning: $level%")
    }
}