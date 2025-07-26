// managers/SyncManager.kt

package com.digitalsignage.managers

import android.content.Context
import com.digitalsignage.models.*
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

    private val dateFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US)
    private var syncJob: Job? = null
    private val syncScope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    // Callbacks para notificar cambios
    var onSyncCompleted: ((SyncData) -> Unit)? = null
    var onSyncError: ((String) -> Unit)? = null

    /**
     * Resultado de sincronización
     */
    sealed class SyncResult {
        data class Success(val syncData: SyncData) : SyncResult()
        object NoUpdates : SyncResult()
        data class Error(val message: String, val exception: Throwable? = null) : SyncResult()
    }

    /**
     * Inicia la sincronización periódica
     */
    fun startPeriodicSync() {
        stopPeriodicSync()

        syncJob = syncScope.launch {
            logger.i(Logger.Category.SYNC, "Starting periodic sync with interval: ${preferencesManager.syncInterval}ms")

            while (isActive) {
                try {
                    performSync()
                    delay(preferencesManager.syncInterval)
                } catch (e: CancellationException) {
                    logger.d(Logger.Category.SYNC, "Sync job cancelled")
                    break
                } catch (e: Exception) {
                    logger.e(Logger.Category.SYNC, "Error in periodic sync", exception = e)
                    delay(preferencesManager.syncInterval * 2) // Esperar más tiempo en caso de error
                }
            }
        }
    }

    /**
     * Detiene la sincronización periódica
     */
    fun stopPeriodicSync() {
        syncJob?.cancel()
        syncJob = null
        logger.d(Logger.Category.SYNC, "Periodic sync stopped")
    }

    /**
     * Realiza una sincronización manual
     */
    suspend fun performSync(): SyncResult {
        return withContext(Dispatchers.IO) {
            try {
                logger.d(Logger.Category.SYNC, "Starting sync check")

                val healthData = DeviceUtils.getHealthData(context)
                val checkServerData = createCheckServerData(healthData)

                when (val result = apiClient.post(Constants.API_CHECK_SERVER, checkServerData)) {
                    is ApiClient.ApiResult.Success -> {
                        val response = JSONObject(result.data)
                        processSyncResponse(response)
                    }
                    is ApiClient.ApiResult.Error -> {
                        val errorMsg = "Sync API error: ${result.message}"
                        logger.e(Logger.Category.SYNC, errorMsg, exception = result.exception)
                        onSyncError?.invoke(errorMsg)
                        SyncResult.Error(errorMsg, result.exception)
                    }
                }

            } catch (e: Exception) {
                val errorMsg = "Sync exception: ${e.message}"
                logger.e(Logger.Category.SYNC, errorMsg, exception = e)
                onSyncError?.invoke(errorMsg)
                SyncResult.Error(errorMsg, e)
            }
        }
    }

    /**
     * Crea los datos para el check_server API
     */
    private fun createCheckServerData(healthData: HealthData): JSONObject {
        return JSONObject().apply {
            put("action", "check_server")
            put("device_id", preferencesManager.deviceId)
            put("last_sync_hash", preferencesManager.lastSyncHash ?: "")
            put("app_version", "1.0.0")
            put("firmware_version", android.os.Build.VERSION.RELEASE)
            put("battery_level", healthData.batteryLevel)
            put("storage_free_mb", healthData.storageFreeBytes / (1024 * 1024))
            put("connection_type", healthData.connectionType)
            put("device_health", JSONObject().apply {
                put("temperature_celsius", healthData.temperatureCelsius)
                put("signal_strength", healthData.signalStrength)
            })
        }
    }

    /**
     * Procesa la respuesta del servidor
     */
    private suspend fun processSyncResponse(response: JSONObject): SyncResult {
        return try {
            val needsSync = response.optBoolean("needs_sync", false)

            if (!needsSync) {
                logger.i(Logger.Category.SYNC, "No sync needed")
                return SyncResult.NoUpdates
            }

            logger.i(Logger.Category.SYNC, "Server indicates sync needed")

            val syncData = parseSyncData(response)

            // Actualizar hash de sincronización
            syncData.newSyncHash?.let { newHash ->
                preferencesManager.lastSyncHash = newHash
                logger.d(Logger.Category.SYNC, "Updated sync hash: ${newHash.take(8)}...")
            }

            // Actualizar timestamp de sincronización
            syncData.syncTimestamp?.let { timestamp ->
                preferencesManager.lastSync = timestamp
            }

            // Aplicar actualizaciones de configuración
            if (syncData.configUpdates.isNotEmpty()) {
                preferencesManager.updateFromServerConfig(syncData.configUpdates)
                logger.d(Logger.Category.SYNC, "Applied config updates")
            }

            // Notificar éxito
            onSyncCompleted?.invoke(syncData)
            logger.i(Logger.Category.SYNC, "Sync completed successfully")

            SyncResult.Success(syncData)

        } catch (e: Exception) {
            logger.e(Logger.Category.SYNC, "Error processing sync response", exception = e)
            SyncResult.Error("Error processing sync: ${e.message}", e)
        }
    }

    /**
     * Parsea los datos de sincronización del servidor
     */
    private fun parseSyncData(response: JSONObject): SyncData {
        val syncData = response.optJSONObject("sync_data")
            ?: throw IllegalArgumentException("Missing sync_data in response")

        return SyncData(
            needsSync = true,
            syncId = response.optString("sync_id"),
            syncTimestamp = response.optString("sync_timestamp"),
            newSyncHash = response.optString("new_sync_hash"),
            playlist = parsePlaylist(syncData),
            assets = parseAssets(syncData),
            configUpdates = parseConfigUpdates(syncData),
            clearCache = response.optBoolean("clear_cache", false)
        )
    }

    /**
     * Parsea la playlist desde los datos de sync
     */
    private fun parsePlaylist(syncData: JSONObject): Playlist? {
        val playlistsArray = syncData.optJSONArray("playlists") ?: return null
        if (playlistsArray.length() == 0) return null

        val playlistJson = playlistsArray.getJSONObject(0) // Tomar la primera playlist

        return Playlist(
            id = playlistJson.getString("id"),
            name = playlistJson.getString("name"),
            lastModified = playlistJson.optString("last_modified", ""),
            scenes = parseScenes(playlistJson.optJSONArray("scenes")),
            isActive = playlistJson.optBoolean("is_active", true),
            totalDuration = playlistJson.optInt("total_duration", 0)
        )
    }

    /**
     * Parsea las escenas de una playlist
     */
    private fun parseScenes(scenesArray: JSONArray?): List<Scene> {
        if (scenesArray == null) return emptyList()

        val scenes = mutableListOf<Scene>()

        for (i in 0 until scenesArray.length()) {
            val sceneJson = scenesArray.getJSONObject(i)

            val scene = Scene(
                id = sceneJson.getString("id"),
                name = sceneJson.getString("name"),
                layout = sceneJson.getString("layout"),
                layoutStructure = parseLayoutStructure(sceneJson.optJSONObject("layout_structure")),
                duration = sceneJson.getInt("duration"),
                transitionIn = sceneJson.optString("transition_in", "none"),
                transitionOut = sceneJson.optString("transition_out", "none"),
                zoneContents = parseZoneContents(sceneJson.optJSONArray("zone_contents"))
            )

            scenes.add(scene)
        }

        return scenes
    }

    /**
     * Parsea la estructura de layout
     */
    private fun parseLayoutStructure(layoutJson: JSONObject?): LayoutStructure {
        if (layoutJson == null) {
            return LayoutStructure(emptyList())
        }

        val zonesArray = layoutJson.optJSONArray("zones") ?: JSONArray()
        val zones = mutableListOf<Zone>()

        for (i in 0 until zonesArray.length()) {
            val zoneJson = zonesArray.getJSONObject(i)
            val positionJson = zoneJson.getJSONObject("position")

            val zone = Zone(
                id = zoneJson.getString("id"),
                name = zoneJson.getString("name"),
                position = Position(
                    x = positionJson.getDouble("x").toFloat(),
                    y = positionJson.getDouble("y").toFloat(),
                    width = positionJson.getDouble("width").toFloat(),
                    height = positionJson.getDouble("height").toFloat()
                ),
                zIndex = zoneJson.optInt("z_index", 1),
                allowedContentTypes = parseStringArray(zoneJson.optJSONArray("allowed_content_types"))
            )

            zones.add(zone)
        }

        return LayoutStructure(zones)
    }

    /**
     * Parsea los contenidos de zona
     */
    private fun parseZoneContents(contentsArray: JSONArray?): List<ZoneContent> {
        if (contentsArray == null) return emptyList()

        val contents = mutableListOf<ZoneContent>()

        for (i in 0 until contentsArray.length()) {
            val contentJson = contentsArray.getJSONObject(i)
            val content = contentJson.getJSONObject("content")

            val zoneContent = ZoneContent(
                zoneId = contentJson.getString("zone_id"),
                content = Content(
                    id = content.getString("id"),
                    type = content.getString("type"),
                    name = content.getString("name"),
                    downloadUrl = content.optString("download_url").takeIf { it.isNotEmpty() },
                    url = content.optString("url").takeIf { it.isNotEmpty() },
                    text = content.optString("text").takeIf { it.isNotEmpty() },
                    duration = content.getInt("duration"),
                    fileSize = content.optLong("file_size"),
                    checksum = content.optString("checksum").takeIf { it.isNotEmpty() }
                ),
                configuration = parseJsonObjectToMap(contentJson.optJSONObject("configuration"))
            )

            contents.add(zoneContent)
        }

        return contents
    }

    /**
     * Parsea los assets del sync
     */
    private fun parseAssets(syncData: JSONObject): List<Asset> {
        val assetsArray = syncData.optJSONArray("assets") ?: return emptyList()
        val assets = mutableListOf<Asset>()

        for (i in 0 until assetsArray.length()) {
            val assetJson = assetsArray.getJSONObject(i)

            val asset = Asset(
                id = assetJson.getString("id"),
                name = assetJson.getString("name"),
                type = assetJson.getString("type"),
                originalName = assetJson.optString("original_name", assetJson.getString("name")),
                downloadUrl = assetJson.optString("url").takeIf { it.isNotEmpty() },
                checksum = assetJson.optString("checksum").takeIf { it.isNotEmpty() },
                fileSize = assetJson.optLong("size_bytes", 0)
            )

            assets.add(asset)
        }

        return assets
    }

    /**
     * Parsea las actualizaciones de configuración
     */
    private fun parseConfigUpdates(syncData: JSONObject): Map<String, Any> {
        val configJson = syncData.optJSONObject("config_updates") ?: return emptyMap()
        return parseJsonObjectToMap(configJson)
    }

    /**
     * Utilidades de parsing
     */
    private fun parseStringArray(jsonArray: JSONArray?): List<String> {
        if (jsonArray == null) return emptyList()

        val list = mutableListOf<String>()
        for (i in 0 until jsonArray.length()) {
            list.add(jsonArray.getString(i))
        }
        return list
    }

    private fun parseJsonObjectToMap(jsonObject: JSONObject?): Map<String, Any> {
        if (jsonObject == null) return emptyMap()

        val map = mutableMapOf<String, Any>()
        jsonObject.keys().forEach { key ->
            map[key] = jsonObject.get(key)
        }
        return map
    }

    /**
     * Fuerza un clear cache local
     */
    suspend fun forceClearCache(): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                logger.w(Logger.Category.SYNC, "Forcing cache clear")

                // Limpiar preferencias de sync
                preferencesManager.clearSyncData()

                // TODO: Limpiar cache de assets físicos

                logger.i(Logger.Category.SYNC, "Cache cleared successfully")
                true
            } catch (e: Exception) {
                logger.e(Logger.Category.SYNC, "Error clearing cache", exception = e)
                false
            }
        }
    }

    /**
     * Obtiene estadísticas de sincronización
     */
    fun getSyncStats(): Map<String, Any> {
        return mapOf(
            "device_id" to preferencesManager.deviceId,
            "last_sync" to (preferencesManager.lastSync ?: "Never"),
            "last_sync_hash" to (preferencesManager.lastSyncHash?.take(8) ?: "None"),
            "sync_interval" to "${preferencesManager.syncInterval / 1000}s",
            "is_sync_running" to (syncJob?.isActive == true)
        )
    }

    /**
     * Limpia recursos al destruir
     */
    fun shutdown() {
        stopPeriodicSync()
        syncScope.cancel()
    }
}