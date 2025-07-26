// storage/PreferencesManager.kt

package com.digitalsignage.storage

import android.content.Context
import android.content.SharedPreferences
import com.digitalsignage.utils.Constants
import com.digitalsignage.utils.DeviceUtils

class PreferencesManager(context: Context) {

    private val prefs: SharedPreferences = context.getSharedPreferences(
        Constants.PREFS_NAME,
        Context.MODE_PRIVATE
    )

    /**
     * Device ID único - se genera automáticamente si no existe
     */
    var deviceId: String
        get() {
            val savedId = prefs.getString(Constants.PREF_DEVICE_ID, null)
            return if (DeviceUtils.isValidDeviceId(savedId)) {
                savedId!!
            } else {
                // Generar nuevo Device ID si no existe o es inválido
                val newId = DeviceUtils.generateDeviceId()
                prefs.edit().putString(Constants.PREF_DEVICE_ID, newId).apply()
                newId
            }
        }
        set(value) {
            prefs.edit().putString(Constants.PREF_DEVICE_ID, value).apply()
        }

    /**
     * Nombre del dispositivo
     */
    var deviceName: String
        get() = prefs.getString(Constants.PREF_DEVICE_NAME, Constants.DEFAULT_DEVICE_NAME) ?: Constants.DEFAULT_DEVICE_NAME
        set(value) {
            prefs.edit().putString(Constants.PREF_DEVICE_NAME, value).apply()
        }

    /**
     * Última sincronización exitosa
     */
    var lastSync: String?
        get() = prefs.getString(Constants.PREF_LAST_SYNC, null)
        set(value) {
            prefs.edit().putString(Constants.PREF_LAST_SYNC, value).apply()
        }

    /**
     * Hash de la última sincronización
     */
    var lastSyncHash: String?
        get() = prefs.getString(Constants.PREF_LAST_SYNC_HASH, null)
        set(value) {
            prefs.edit().putString(Constants.PREF_LAST_SYNC_HASH, value).apply()
        }

    /**
     * Estado de registro en el servidor
     */
    var isRegistered: Boolean
        get() = prefs.getBoolean(Constants.PREF_IS_REGISTERED, false)
        set(value) {
            prefs.edit().putBoolean(Constants.PREF_IS_REGISTERED, value).apply()
        }

    /**
     * Orientación de la pantalla
     */
    var orientation: String
        get() = prefs.getString(Constants.PREF_ORIENTATION, Constants.ORIENTATION_LANDSCAPE) ?: Constants.ORIENTATION_LANDSCAPE
        set(value) {
            prefs.edit().putString(Constants.PREF_ORIENTATION, value).apply()
        }

    /**
     * Estado de silencio
     */
    var isMuted: Boolean
        get() = prefs.getBoolean(Constants.PREF_IS_MUTED, false)
        set(value) {
            prefs.edit().putBoolean(Constants.PREF_IS_MUTED, value).apply()
        }

    /**
     * Intervalo de sincronización en milisegundos
     */
    var syncInterval: Long
        get() = prefs.getLong(Constants.PREF_SYNC_INTERVAL, Constants.SYNC_INTERVAL_DEBUG)
        set(value) {
            prefs.edit().putLong(Constants.PREF_SYNC_INTERVAL, value).apply()
        }

    /**
     * Playlist actual almacenada como JSON
     */
    var currentPlaylistJson: String?
        get() = prefs.getString(Constants.PREF_CURRENT_PLAYLIST, null)
        set(value) {
            prefs.edit().putString(Constants.PREF_CURRENT_PLAYLIST, value).apply()
        }

    /**
     * Limpia todos los datos de sincronización (mantiene device info)
     */
    fun clearSyncData() {
        prefs.edit()
            .remove(Constants.PREF_LAST_SYNC)
            .remove(Constants.PREF_LAST_SYNC_HASH)
            .remove(Constants.PREF_CURRENT_PLAYLIST)
            .apply()
    }

    /**
     * Limpia todos los datos de la app
     */
    fun clearAllData() {
        prefs.edit().clear().apply()
    }

    /**
     * Obtiene todas las preferencias como mapa (para debugging)
     */
    fun getAllPreferences(): Map<String, Any?> {
        return prefs.all
    }

    /**
     * Verifica si es la primera ejecución de la app
     */
    fun isFirstRun(): Boolean {
        return !prefs.contains(Constants.PREF_DEVICE_ID)
    }

    /**
     * Marca que la app ya se ejecutó al menos una vez
     */
    fun markFirstRunComplete() {
        // El deviceId se genera automáticamente, así que solo aseguramos que existe
        val deviceIdValue = deviceId
    }

    /**
     * Actualiza configuración desde el servidor
     */
    fun updateFromServerConfig(config: Map<String, Any>) {
        val editor = prefs.edit()

        config["sync_interval"]?.let {
            if (it is Number) {
                editor.putLong(Constants.PREF_SYNC_INTERVAL, it.toLong() * 1000) // Servidor envía en segundos
            }
        }

        config["audio_enabled"]?.let {
            if (it is Boolean) {
                editor.putBoolean(Constants.PREF_IS_MUTED, !it) // Invertimos para isMuted
            }
        }

        config["orientation"]?.let {
            if (it is String) {
                editor.putString(Constants.PREF_ORIENTATION, it)
            }
        }

        editor.apply()
    }

    /**
     * Exporta configuración actual para enviar al servidor
     */
    fun exportConfig(): Map<String, Any> {
        return mapOf(
            "device_id" to deviceId,
            "device_name" to deviceName,
            "orientation" to orientation,
            "is_muted" to isMuted,
            "sync_interval" to (syncInterval / 1000), // Convertir a segundos
            "last_sync" to (lastSync ?: ""),
            "last_sync_hash" to (lastSyncHash ?: ""),
            "is_registered" to isRegistered
        )
    }
}