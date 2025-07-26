// models/Player.kt
package com.digitalsignage.models

data class Player(
    val deviceId: String,
    val name: String,
    val status: String = "offline",
    val lastSync: String? = null,
    val lastSyncHash: String? = null,
    val appVersion: String = "1.0.0",
    val firmwareVersion: String = "",
    val batteryLevel: Int = 100,
    val storageFreeBytes: Long = 0,
    val temperatureCelsius: Float = 25.0f,
    val connectionType: String = "wifi",
    val signalStrength: Int = -50,
    val resolution: String = "1920x1080",
    val orientation: String = "landscape"
)