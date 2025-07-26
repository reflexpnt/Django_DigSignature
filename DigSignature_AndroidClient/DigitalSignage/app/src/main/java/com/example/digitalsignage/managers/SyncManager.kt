// managers/SyncManager.kt

package com.digitalsignage.managers

import android.content.Context
import com.digitalsignage.models.Asset
import com.digitalsignage.models.Playlist
import com.digitalsignage.models.SyncData
import com.digitalsignage.network.ApiClient
import com.digitalsignage.storage.PreferencesManager
import com.digitalsignage.utils.Constants
import com.digitalsignage.utils.DeviceUtils
import com.digitalsignage.utils.Logger
import kotlinx.coroutines.*
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.*

class SyncManager(
    private val context: Context,
    private val apiClient: ApiClient,
    private val preferencesManager: PreferencesManager,
    private val logger: Logger
) {

    // Callbacks para eventos de sincronización
    var onSyncStarted: (() -> Unit)? = null
    var onSyncCompleted: ((SyncData) -> Unit)? = null
    var onSyncError: ((String) -> Unit)? = null
    var onSyncProgress: ((String) -> Unit)? = null

    // Control de sincronización
    private var syncJob: Job? = null
    private val syncScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var isSyncing = false
    private var lastSyncTime: Long = 0

    // Configuración de sincronización
    private var syncInterval: Long = Constants.SYNC_INTERVAL_DEBUG
    private var forceNextSync = false

    // Estadísticas de sincronización
    private var syncSuccessCount = 0
    private var syncErrorCount = 0
    private var lastSyncHash = ""

    /**
     * Inicia la sincronización automática con el servidor
     */
    fun startAutoSync() {
        logger.i(Logger.Category.SYNC, "Starting automatic sync with interval: ${syncInterval / 1000}s")

        syncJob = syncScope.launch {
            while (isActive) {
                try {
                    performSyncInternal(isManual = false)
                    delay(syncInterval)
                } catch (e: CancellationException) {
                    logger.i(Logger.Category.SYNC, "Auto sync cancelled")
                    break
                } catch (e: Exception) {
                    logger.e(Logger.Category.SYNC, "Error in auto sync loop", exception = e)
                    delay(syncInterval * 2) // Esperar más tiempo si hay error
                }
            }
        }
    }

    /**
     * Detiene la sincronización automática
     */
    fun stopAutoSync() {
        logger.i(Logger.Category.SYNC, "Stopping automatic sync")
        syncJob?.cancel()
        syncJob = null
    }

    /**
     * Ejecuta una sincronización manual (método público)
     */
    suspend fun performManualSync(): Boolean {
        return performSyncInternal(isManual = true)
    }

    /**
     * Fuerza la próxima sincronización (ignora hash)
     */
    fun forceNextSync() {
        forceNextSync = true
        logger.i(Logger.Category.SYNC, "Next sync will be forced")
    }

    /**
     * Limpia el cache y fuerza re-sincronización
     */
    fun forceClearCache() {
        lastSyncHash = ""
        preferencesManager.lastSyncHash = ""
        forceNextSync = true
        logger.i(Logger.Category.SYNC, "Cache cleared, forcing next sync")
    }

    /**
     * Realiza el proceso de sincronización principal
     */
    private suspend fun performSyncInternal(isManual: Boolean): Boolean {
        if (isSyncing && !isManual) {
            logger.d(Logger.Category.SYNC, "Sync already in progress, skipping")
            return false
        }

        return try {
            isSyncing = true
            onSyncStarted?.invoke()

            logger.i(Logger.Category.SYNC, "Starting sync${if (isManual) " (manual)" else ""}")

            // Preparar datos para el servidor
            val syncRequest = buildSyncRequest()

            // Llamar al endpoint check_server
            val response = apiClient.checkServer(syncRequest)

            if (response.isSuccessful) {
                val responseData = response.body?.string()
                if (responseData != null) {
                    val result = processSyncResponse(responseData)
                    syncSuccessCount++
                    lastSyncTime = System.currentTimeMillis()

                    logger.i(Logger.Category.SYNC, "Sync completed successfully")
                    result
                } else {
                    throw Exception("Empty response from server")
                }
            } else {
                throw Exception("Server error: ${response.code} ${response.message}")
            }

        } catch (e: Exception) {
            syncErrorCount++
            val errorMessage = "Sync failed: ${e.message}"
            logger.e(Logger.Category.SYNC, errorMessage, exception = e)
            onSyncError?.invoke(errorMessage)
            false
        } finally {
            isSyncing = false
        }
    }

    /**
     * Construye la solicitud de sincronización para enviar al servidor
     */
    private suspend fun buildSyncRequest(): JSONObject {
        return withContext(Dispatchers.IO) {
            val deviceInfo = DeviceUtils.getDeviceInfo()
            val batteryLevel = DeviceUtils.getBatteryLevel(context)
            val storageInfo = DeviceUtils.getStorageInfo(context)

            // Hash actual almacenado (del último sync exitoso)
            val currentHash = preferencesManager.lastSyncHash.takeIf { it.isNotBlank() } ?: lastSyncHash

            JSONObject().apply {
                put("action", "check_server")
                put("device_id", preferencesManager.deviceId)
                put("last_sync_hash", if (forceNextSync) "" else currentHash)
                put("app_version", deviceInfo["app_version"])
                put("firmware_version", deviceInfo["firmware_version"])
                put("battery_level", batteryLevel)
                put("storage_free_mb", storageInfo["free_space_mb"])
                put("connection_type", DeviceUtils.getConnectionType(context))

                // Información adicional del dispositivo
                put("device_health", JSONObject().apply {
                    put("temperature_celsius", DeviceUtils.getDeviceTemperature())
                    put("signal_strength", DeviceUtils.getSignalStrength(context))
                })
            }
        }
    }

    /**
     * Procesa la respuesta del servidor y ejecuta acciones necesarias
     */
    private suspend fun processSyncResponse(responseData: String): Boolean {
        return try {
            val jsonResponse = JSONObject(responseData)
            val status = jsonResponse.optString("status")

            when (status) {
                "success" -> {
                    val needsSync = jsonResponse.optBoolean("needs_sync", false)
                    logger.d(Logger.Category.SYNC, "Server response: needs_sync=$needsSync")

                    if (needsSync && jsonResponse.has("sync_data")) {
                        // El servidor dice que necesitamos sincronizar
                        val newSyncHash = jsonResponse.optString("new_sync_hash", "")
                        val syncDataJson = jsonResponse.getJSONObject("sync_data")

                        onSyncProgress?.invoke("Processing sync data from server")

                        // Procesar datos de sincronización
                        val syncData = parseSyncData(syncDataJson)

                        // Actualizar hash local
                        if (newSyncHash.isNotBlank()) {
                            lastSyncHash = newSyncHash
                            preferencesManager.lastSyncHash = newSyncHash
                            logger.d(Logger.Category.SYNC, "Updated sync hash: $newSyncHash")
                        }

                        // Notificar sync completada con datos
                        onSyncCompleted?.invoke(syncData)

                        // Confirmar sincronización al servidor
                        confirmSyncToServer(newSyncHash)

                        // Resetear flag de force
                        forceNextSync = false

                        true
                    } else {
                        // No hay cambios, sync exitosa pero sin datos nuevos
                        logger.d(Logger.Category.SYNC, "No sync needed - content is up to date")

                        // Actualizar intervalo si el servidor lo especifica
                        if (jsonResponse.has("next_check_interval")) {
                            val newInterval = jsonResponse.getLong("next_check_interval") * 1000L
                            if (newInterval != syncInterval) {
                                updateSyncInterval(newInterval)
                            }
                        }

                        // Notificar sync completada sin cambios
                        onSyncCompleted?.invoke(SyncData(
                            syncId = "no-changes-${System.currentTimeMillis()}",
                            playlist = null,
                            assets = emptyList(),
                            needsSync = false
                        ))

                        true
                    }
                }

                "device_not_registered" -> {
                    logger.w(Logger.Category.SYNC, "Device not registered on server")
                    onSyncError?.invoke("Device not registered. Please check device registration.")
                    false
                }

                else -> {
                    val message = jsonResponse.optString("message", "Unknown server error")
                    logger.e(Logger.Category.SYNC, "Server error: $message")
                    onSyncError?.invoke(message)
                    false
                }
            }

        } catch (e: Exception) {
            logger.e(Logger.Category.SYNC, "Error processing sync response", exception = e)
            onSyncError?.invoke("Error processing server response: ${e.message}")
            false
        }
    }

    /**
     * Parsea los datos de sincronización del JSON del servidor
     */
    private fun parseSyncData(syncDataJson: JSONObject): SyncData {
        val syncId = syncDataJson.optString("sync_id", "sync-${System.currentTimeMillis()}")

        // Parsear playlist
        val playlist = if (syncDataJson.has("playlists")) {
            val playlistsArray = syncDataJson.getJSONArray("playlists")
            if (playlistsArray.length() > 0) {
                parsePlaylist(playlistsArray.getJSONObject(0))
            } else null
        } else null

        // Parsear assets
        val assets = if (syncDataJson.has("assets")) {
            parseAssets(syncDataJson.getJSONArray("assets"))
        } else emptyList()

        return SyncData(
            syncId = syncId,
            playlist = playlist,
            assets = assets,
            needsSync = true
        )
    }

    /**
     * Parsea una playlist del JSON del servidor
     */
    private fun parsePlaylist(playlistJson: JSONObject): Playlist {
        return Playlist(
            id = playlistJson.optString("id"),
            name = playlistJson.optString("name"),
            lastModified = System.currentTimeMillis()
        )
    }

    /**
     * Parsea la lista de assets del servidor
     */
    private fun parseAssets(assetsArray: JSONArray): List<Asset> {
        val assets = mutableListOf<Asset>()

        for (i in 0 until assetsArray.length()) {
            val assetJson = assetsArray.getJSONObject(i)

            val asset = Asset(
                id = assetJson.optString("id"),
                name = assetJson.optString("name"),
                type = assetJson.optString("type", "unknown"),
                checksum = assetJson.optString("checksum", ""),
                sizeBytes = assetJson.optLong("size_bytes", 0),
                originalName = assetJson.optString("original_name", "")
            )

            assets.add(asset)
        }

        return assets
    }

    /**
     * Confirma al servidor que la sincronización fue completada
     */
    private suspend fun confirmSyncToServer(syncHash: String) {
        try {
            val confirmationData = JSONObject().apply {
                put("device_id", preferencesManager.deviceId)
                put("sync_hash", syncHash)
                put("timestamp", SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).format(Date()))
            }

            val response = apiClient.confirmSync(confirmationData)

            if (response.isSuccessful) {
                logger.d(Logger.Category.SYNC, "Sync confirmation sent to server")
            } else {
                logger.w(Logger.Category.SYNC, "Failed to confirm sync to server: ${response.code}")
            }

        } catch (e: Exception) {
            logger.w(Logger.Category.SYNC, "Error sending sync confirmation", exception = e)
            // No es crítico si falla la confirmación
        }
    }

    /**
     * Actualiza el intervalo de sincronización
     */
    private fun updateSyncInterval(newInterval: Long) {
        if (newInterval > 0 && newInterval != syncInterval) {
            val oldInterval = syncInterval
            syncInterval = newInterval

            logger.i(Logger.Category.SYNC,
                "Sync interval updated: ${oldInterval / 1000}s -> ${newInterval / 1000}s")

            // Guardar en preferencias
            preferencesManager.syncInterval = newInterval

            // Reiniciar auto sync con nuevo intervalo
            if (syncJob?.isActive == true) {
                stopAutoSync()
                startAutoSync()
            }
        }
    }

    /**
     * Obtiene estadísticas de sincronización
     */
    fun getSyncStats(): Map<String, Any> {
        val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())

        return mapOf(
            "is_syncing" to isSyncing,
            "sync_interval_seconds" to (syncInterval / 1000),
            "last_sync" to if (lastSyncTime > 0) dateFormat.format(Date(lastSyncTime)) else "Never",
            "last_sync_hash" to lastSyncHash,
            "success_count" to syncSuccessCount,
            "error_count" to syncErrorCount,
            "success_rate" to if (syncSuccessCount + syncErrorCount > 0) {
                (syncSuccessCount.toFloat() / (syncSuccessCount + syncErrorCount) * 100).toInt()
            } else 0,
            "next_sync_in_seconds" to if (syncJob?.isActive == true && lastSyncTime > 0) {
                maxOf(0, (syncInterval - (System.currentTimeMillis() - lastSyncTime)) / 1000)
            } else 0
        )
    }

    /**
     * Verifica si hay una sincronización en progreso
     */
    fun isSyncInProgress(): Boolean = isSyncing

    /**
     * Obtiene el tiempo del último sync exitoso
     */
    fun getLastSyncTime(): Long = lastSyncTime

    /**
     * Obtiene el hash del último sync exitoso
     */
    fun getLastSyncHash(): String = lastSyncHash

    /**
     * Limpieza al destruir el manager
     */
    fun cleanup() {
        stopAutoSync()
        syncScope.cancel()
    }
}