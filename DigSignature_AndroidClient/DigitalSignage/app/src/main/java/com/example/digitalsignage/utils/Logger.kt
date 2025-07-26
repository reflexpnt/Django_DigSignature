// utils/Logger.kt

package com.digitalsignage.utils

import android.content.Context
import android.util.Log as AndroidLog
import kotlinx.coroutines.*
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.ConcurrentLinkedQueue

class Logger(
    private val context: Context,
    private val deviceId: String
) {

    // Queue thread-safe para logs
    private val logQueue = ConcurrentLinkedQueue<LogEntry>()
    private val localLogs = mutableListOf<String>()
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US)

    // Callbacks para UI
    var onLogAdded: ((String) -> Unit)? = null

    // Coroutines
    private val logScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var sendLogJob: Job? = null

    init {
        startLogSender()
    }

    /**
     * Niveles de log según Android
     */
    enum class Level(val value: String) {
        VERBOSE("VERBOSE"),
        DEBUG("DEBUG"),
        INFO("INFO"),
        WARN("WARN"),
        ERROR("ERROR"),
        FATAL("FATAL")
    }

    /**
     * Categorías de log según el simulador
     */
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

        // Agregar a cola para envío al servidor
        logQueue.offer(logEntry)

        // Agregar a logs locales para UI
        val formattedLog = formatLogForUI(logEntry)
        synchronized(localLogs) {
            localLogs.add(formattedLog)

            // Mantener solo los últimos N logs para UI
            if (localLogs.size > Constants.LOG_MAX_LINES) {
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
        onLogAdded?.invoke("Logs cleared")
    }

    /**
     * Convierte LogEntry a JSON para envío al servidor
     */
    private fun logEntryToJson(entry: LogEntry): JSONObject {
        return JSONObject().apply {
            put("device_id", deviceId)
            put("timestamp", entry.deviceTimestamp)
            put("level", entry.level)
            put("category", entry.category)
            put("tag", entry.tag)
            put("message", entry.message)
            put("thread_name", entry.threadName)
            entry.methodName?.let { put("method_name", it) }
            entry.lineNumber?.let { put("line_number", it) }
            entry.exceptionClass?.let { put("exception_class", it) }
            entry.stackTrace?.let { put("stack_trace", it) }
            entry.extraData?.let {
                put("extra_data", JSONObject(it))
            }
        }
    }

    /**
     * Inicia el servicio de envío de logs al servidor
     */
    private fun startLogSender() {
        sendLogJob = logScope.launch {
            while (isActive) {
                try {
                    sendLogsToServer()
                    delay(Constants.LOG_SEND_INTERVAL)
                } catch (e: Exception) {
                    // No logear errores de envío para evitar loops infinitos
                    AndroidLog.e("Logger", "Error sending logs to server", e)
                    delay(Constants.LOG_SEND_INTERVAL * 2) // Esperar más tiempo en caso de error
                }
            }
        }
    }

    /**
     * Envía logs al servidor en batch
     */
    private suspend fun sendLogsToServer() {
        val logsToSend = mutableListOf<LogEntry>()

        // Extraer logs de la cola (máximo batch size)
        repeat(Constants.LOG_BATCH_SIZE) {
            val log = logQueue.poll()
            if (log != null) {
                logsToSend.add(log)
            }
        }

        if (logsToSend.isEmpty()) return

        try {
            withContext(Dispatchers.IO) {
                val logsArray = JSONArray()
                logsToSend.forEach { entry ->
                    logsArray.put(logEntryToJson(entry))
                }

                // TODO: Implementar envío real usando ApiClient
                // Por ahora solo simular
                AndroidLog.d("Logger", "Would send ${logsToSend.size} logs to server")

                // Simular delay de red
                delay(100)
            }
        } catch (e: Exception) {
            // Re-encolar logs si falló el envío
            logsToSend.forEach { entry ->
                logQueue.offer(entry)
            }
            throw e
        }
    }

    /**
     * Envía un log individual inmediatamente (para eventos críticos)
     */
    suspend fun sendLogImmediately(
        level: Level,
        category: Category,
        message: String,
        tag: String,
        exception: Throwable? = null
    ) {
        val entry = LogEntry(
            deviceTimestamp = dateFormat.format(Date()),
            level = level.value,
            category = category.value,
            tag = tag,
            message = message,
            threadName = Thread.currentThread().name,
            exceptionClass = exception?.javaClass?.simpleName,
            stackTrace = exception?.stackTraceToString()
        )

        try {
            withContext(Dispatchers.IO) {
                val json = logEntryToJson(entry)
                // TODO: Implementar envío inmediato usando ApiClient
                AndroidLog.d("Logger", "Would send immediate log: $message")
            }
        } catch (e: Exception) {
            // Si falla el envío inmediato, agregar a cola normal
            logQueue.offer(entry)
        }
    }

    /**
     * Detiene el logger y envía logs pendientes
     */
    fun shutdown() {
        logScope.launch {
            // Enviar logs pendientes
            while (logQueue.isNotEmpty()) {
                sendLogsToServer()
                delay(100)
            }

            sendLogJob?.cancel()
        }
    }
}