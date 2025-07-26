// managers/DeviceManager.kt

package com.digitalsignage.managers

import android.content.Context
import com.digitalsignage.models.Player
import com.digitalsignage.network.ApiClient
import com.digitalsignage.storage.PreferencesManager
import com.digitalsignage.utils.Constants
import com.digitalsignage.utils.DeviceUtils
import com.digitalsignage.utils.Logger
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

class DeviceManager(
    private val context: Context,
    private val apiClient: ApiClient,
    private val preferencesManager: PreferencesManager,
    private val logger: Logger
) {

    /**
     * Resultado del registro de dispositivo
     */
    sealed class RegistrationResult {
        object Success : RegistrationResult()
        data class Error(val message: String, val exception: Throwable? = null) : RegistrationResult()
        object AlreadyRegistered : RegistrationResult()
    }

    /**
     * Registra el dispositivo en el servidor si no está registrado
     */
    suspend fun ensureDeviceRegistered(): RegistrationResult {
        return withContext(Dispatchers.IO) {
            try {
                // Verificar si ya está registrado
                if (preferencesManager.isRegistered) {
                    logger.i(Logger.Category.SYSTEM, "Device already registered: ${preferencesManager.deviceId}")
                    return@withContext RegistrationResult.AlreadyRegistered
                }

                logger.i(Logger.Category.SYSTEM, "Registering device: ${preferencesManager.deviceId}")

                // Preparar datos de registro
                val registrationData = createRegistrationData()

                // Enviar registro al servidor
                when (val result = apiClient.post(Constants.API_REGISTER, registrationData)) {
                    is ApiClient.ApiResult.Success -> {
                        // Parsear respuesta
                        val response = JSONObject(result.data)

                        if (response.optBoolean("success", false)) {
                            // Registro exitoso
                            preferencesManager.isRegistered = true

                            // Actualizar información del dispositivo si el servidor la devuelve
                            updateDeviceFromResponse(response)

                            logger.i(Logger.Category.SYSTEM, "Device registered successfully")
                            RegistrationResult.Success
                        } else {
                            val errorMsg = response.optString("message", "Registration failed")
                            logger.e(Logger.Category.SYSTEM, "Registration failed: $errorMsg")
                            RegistrationResult.Error(errorMsg)
                        }
                    }
                    is ApiClient.ApiResult.Error -> {
                        logger.e(Logger.Category.NETWORK, "Registration API error: ${result.message}", exception = result.exception)
                        RegistrationResult.Error(result.message, result.exception)
                    }
                }

            } catch (e: Exception) {
                logger.e(Logger.Category.SYSTEM, "Device registration exception", exception = e)
                RegistrationResult.Error("Registration exception: ${e.message}", e)
            }
        }
    }

    /**
     * Crea los datos JSON para el registro
     */
    private fun createRegistrationData(): JSONObject {
        val deviceInfo = DeviceUtils.getDeviceInfo()
        val healthData = DeviceUtils.getHealthData(context)

        return JSONObject().apply {
            put("device_id", preferencesManager.deviceId)
            put("name", preferencesManager.deviceName)
            put("app_version", "1.0.0")
            put("firmware_version", deviceInfo["android_version"])
            put("battery_level", healthData.batteryLevel)
            put("storage_free_mb", healthData.storageFreeBytes / (1024 * 1024))
            put("temperature_celsius", healthData.temperatureCelsius.toDouble()) // ← CAMBIO: Float a Double
            put("connection_type", healthData.connectionType)
            put("signal_strength", healthData.signalStrength)
            put("resolution", DeviceUtils.getScreenResolution(context))
            put("orientation", preferencesManager.orientation)

            // Información adicional del dispositivo
            put("device_info", JSONObject().apply {
                deviceInfo.forEach { (key, value) ->
                    put(key, value)
                }
            })

            // Capacidades del dispositivo
            put("capabilities", JSONObject().apply {
                put("video_formats", JSONArray(listOf("mp4", "avi", "mov", "mkv")))
                put("image_formats", JSONArray(listOf("jpg", "jpeg", "png", "gif", "bmp")))
                put("html_support", true)
                put("audio_support", true)
                put("kiosk_mode", true)
                put("remote_control", true)
            })
        }
    }

    /**
     * Actualiza información del dispositivo desde la respuesta del servidor
     */
    private fun updateDeviceFromResponse(response: JSONObject) {
        try {
            // El servidor puede devolver configuración actualizada
            response.optJSONObject("device_config")?.let { config ->
                val configMap = mutableMapOf<String, Any>()
                config.keys().forEach { key ->
                    configMap[key] = config.get(key)
                }
                preferencesManager.updateFromServerConfig(configMap)
                logger.d(Logger.Category.SYSTEM, "Updated device config from server")
            }

            // Actualizar nombre si el servidor lo cambió
            response.optString("device_name")?.takeIf { it.isNotEmpty() }?.let { serverName ->
                if (serverName != preferencesManager.deviceName) {
                    preferencesManager.deviceName = serverName
                    logger.d(Logger.Category.SYSTEM, "Device name updated to: $serverName")
                }
            }

        } catch (e: Exception) {
            logger.w(Logger.Category.SYSTEM, "Error updating device from server response", exception = e)
        }
    }

    /**
     * Obtiene información actual del dispositivo
     */
    fun getCurrentDeviceInfo(): Player {
        val deviceInfo = DeviceUtils.getDeviceInfo()
        val healthData = DeviceUtils.getHealthData(context)

        return Player(
            deviceId = preferencesManager.deviceId,
            name = preferencesManager.deviceName,
            status = if (preferencesManager.isRegistered) "online" else "unregistered",
            lastSync = preferencesManager.lastSync,
            lastSyncHash = preferencesManager.lastSyncHash,
            appVersion = "1.0.0",
            firmwareVersion = deviceInfo["android_version"] ?: "Unknown",
            batteryLevel = healthData.batteryLevel,
            storageFreeBytes = healthData.storageFreeBytes,
            temperatureCelsius = healthData.temperatureCelsius,
            connectionType = healthData.connectionType,
            signalStrength = healthData.signalStrength,
            resolution = DeviceUtils.getScreenResolution(context),
            orientation = preferencesManager.orientation
        )
    }

    /**
     * Fuerza el re-registro del dispositivo
     */
    suspend fun forceReregister(): RegistrationResult {
        return withContext(Dispatchers.IO) {
            logger.i(Logger.Category.SYSTEM, "Forcing device re-registration")

            // Limpiar estado de registro
            preferencesManager.isRegistered = false

            // Intentar registro nuevamente
            ensureDeviceRegistered()
        }
    }

    /**
     * Actualiza el nombre del dispositivo
     */
    suspend fun updateDeviceName(newName: String): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                val oldName = preferencesManager.deviceName
                preferencesManager.deviceName = newName

                logger.i(Logger.Category.SYSTEM, "Device name changed from '$oldName' to '$newName'")

                // TODO: Enviar actualización al servidor si está registrado
                if (preferencesManager.isRegistered) {
                    // Implementar API para actualizar info del dispositivo
                    logger.d(Logger.Category.SYSTEM, "Should notify server about name change")
                }

                true
            } catch (e: Exception) {
                logger.e(Logger.Category.SYSTEM, "Error updating device name", exception = e)
                false
            }
        }
    }

    /**
     * Verifica el estado de registro con el servidor
     */
    suspend fun verifyRegistrationStatus(): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                if (!preferencesManager.isRegistered) {
                    return@withContext false
                }

                // TODO: Implementar verificación con el servidor
                // Por ahora, confiamos en el estado local
                logger.d(Logger.Category.SYSTEM, "Registration status verified locally")
                true

            } catch (e: Exception) {
                logger.w(Logger.Category.SYSTEM, "Error verifying registration status", exception = e)
                false
            }
        }
    }

    /**
     * Reinicia el estado del dispositivo (útil para debugging)
     */
    suspend fun resetDevice(): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                logger.w(Logger.Category.SYSTEM, "Resetting device state")

                // Limpiar todas las preferencias
                preferencesManager.clearAllData()

                logger.i(Logger.Category.SYSTEM, "Device reset completed. New ID: ${preferencesManager.deviceId}")
                true

            } catch (e: Exception) {
                logger.e(Logger.Category.SYSTEM, "Error resetting device", exception = e)
                false
            }
        }
    }

    /**
     * Exporta información del dispositivo para debugging
     */
    fun exportDeviceInfo(): Map<String, Any> {
        val deviceInfo = DeviceUtils.getDeviceInfo()
        val healthData = DeviceUtils.getHealthData(context)
        val prefs = preferencesManager.getAllPreferences()

        return mapOf(
            "device_id" to preferencesManager.deviceId,
            "device_name" to preferencesManager.deviceName,
            "is_registered" to preferencesManager.isRegistered,
            "health_data" to mapOf(
                "battery" to healthData.batteryLevel,
                "temperature" to healthData.temperatureCelsius,
                "storage_free" to DeviceUtils.formatBytes(healthData.storageFreeBytes),
                "connection" to healthData.connectionType,
                "signal" to healthData.signalStrength
            ),
            "device_info" to deviceInfo,
            "preferences" to prefs
        )
    }
}