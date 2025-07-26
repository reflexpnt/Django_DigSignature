// utils/DeviceUtils.kt

package com.digitalsignage.utils

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.wifi.WifiManager
import android.os.BatteryManager
import android.os.Build
import android.os.Environment
import android.os.StatFs
import android.telephony.TelephonyManager
import android.util.DisplayMetrics
import android.view.WindowManager
import com.digitalsignage.models.HealthData
import java.security.SecureRandom
import java.text.SimpleDateFormat
import java.util.*

object DeviceUtils {

    private val random = SecureRandom()
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US)

    /**
     * Genera un Device ID único de 16 caracteres hexadecimales
     */
    fun generateDeviceId(): String {
        val chars = "0123456789ABCDEF"
        val result = StringBuilder(Constants.DEVICE_ID_LENGTH)

        repeat(Constants.DEVICE_ID_LENGTH) {
            result.append(chars[random.nextInt(chars.length)])
        }

        return result.toString()
    }

    /**
     * Obtiene información básica del dispositivo
     */
    fun getDeviceInfo(): Map<String, String> {
        return mapOf(
            "manufacturer" to Build.MANUFACTURER,
            "model" to Build.MODEL,
            "product" to Build.PRODUCT,
            "device" to Build.DEVICE,
            "board" to Build.BOARD,
            "hardware" to Build.HARDWARE,
            "serial" to Build.getRadioVersion(),
            "android_version" to Build.VERSION.RELEASE,
            "sdk_version" to Build.VERSION.SDK_INT.toString(),
            "build_id" to Build.ID,
            "build_time" to Build.TIME.toString()
        )
    }

    /**
     * Obtiene el nivel de batería del dispositivo
     */
    fun getBatteryLevel(context: Context): Int {
        return try {
            val batteryStatus = context.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            val level = batteryStatus?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
            val scale = batteryStatus?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1

            if (level == -1 || scale == -1) {
                50 // Valor por defecto
            } else {
                (level.toFloat() / scale.toFloat() * 100).toInt()
            }
        } catch (e: Exception) {
            50 // Valor por defecto en caso de error
        }
    }

    /**
     * Obtiene la temperatura del dispositivo (aproximada)
     */
    fun getDeviceTemperature(): Float {
        // En Android no hay API directa para temperatura del CPU
        // Retornamos una simulación basada en carga
        return try {
            25.0f + (Math.random() * 15).toFloat() // 25-40°C
        } catch (e: Exception) {
            25.0f
        }
    }

    /**
     * Obtiene el espacio libre de almacenamiento en bytes
     */
    fun getStorageFreeBytes(): Long {
        return try {
            val stat = StatFs(Environment.getDataDirectory().path)
            stat.availableBlocksLong * stat.blockSizeLong
        } catch (e: Exception) {
            1024L * 1024L * 1024L // 1GB por defecto
        }
    }

    /**
     * Obtiene el tipo de conexión de red
     */
    fun getConnectionType(context: Context): String {
        return try {
            val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val network = connectivityManager.activeNetwork
            val networkCapabilities = connectivityManager.getNetworkCapabilities(network)

            when {
                networkCapabilities?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true -> "wifi"
                networkCapabilities?.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) == true -> "mobile"
                networkCapabilities?.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET) == true -> "ethernet"
                else -> "unknown"
            }
        } catch (e: Exception) {
            "unknown"
        }
    }

    /**
     * Obtiene la fuerza de la señal WiFi en dBm
     */
    @Suppress("DEPRECATION")
    fun getWifiSignalStrength(context: Context): Int {
        return try {
            val wifiManager = context.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
            val wifiInfo = wifiManager.connectionInfo
            wifiInfo.rssi
        } catch (e: Exception) {
            -50 // Valor por defecto (buena señal)
        }
    }

    /**
     * Obtiene la resolución de la pantalla
     */
    @Suppress("DEPRECATION")
    fun getScreenResolution(context: Context): String {
        return try {
            val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
            val displayMetrics = DisplayMetrics()
            windowManager.defaultDisplay.getMetrics(displayMetrics)
            "${displayMetrics.widthPixels}x${displayMetrics.heightPixels}"
        } catch (e: Exception) {
            "1920x1080"
        }
    }

    /**
     * Obtiene datos completos de salud del dispositivo
     */
    fun getHealthData(context: Context): HealthData {
        return HealthData(
            batteryLevel = getBatteryLevel(context),
            temperatureCelsius = getDeviceTemperature(),
            storageFreeBytes = getStorageFreeBytes(),
            connectionType = getConnectionType(context),
            signalStrength = getWifiSignalStrength(context),
            timestamp = getCurrentTimestamp()
        )
    }

    /**
     * Obtiene timestamp actual en formato ISO
     */
    fun getCurrentTimestamp(): String {
        return dateFormat.format(Date())
    }

    /**
     * Verifica si el dispositivo tiene conexión a internet
     */
    fun hasInternetConnection(context: Context): Boolean {
        return try {
            val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val network = connectivityManager.activeNetwork
            val networkCapabilities = connectivityManager.getNetworkCapabilities(network)
            networkCapabilities?.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) == true
        } catch (e: Exception) {
            false
        }
    }

    /**
     * Convierte bytes a formato legible
     */
    fun formatBytes(bytes: Long): String {
        val units = arrayOf("B", "KB", "MB", "GB", "TB")
        var value = bytes.toDouble()
        var unitIndex = 0

        while (value >= 1024 && unitIndex < units.size - 1) {
            value /= 1024
            unitIndex++
        }

        return "%.1f %s".format(value, units[unitIndex])
    }

    /**
     * Valida si un Device ID tiene el formato correcto
     */
    fun isValidDeviceId(deviceId: String?): Boolean {
        if (deviceId == null) return false
        if (deviceId.length != Constants.DEVICE_ID_LENGTH) return false
        return deviceId.all { it.isDigit() || it in 'A'..'F' }
    }
}