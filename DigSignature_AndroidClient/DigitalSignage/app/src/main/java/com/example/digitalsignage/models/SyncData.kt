// models/SyncData.kt
package com.digitalsignage.models

data class SyncData(
    val needsSync: Boolean,
    val syncId: String? = null,
    val syncTimestamp: String? = null,
    val newSyncHash: String? = null,
    val playlist: Playlist? = null,
    val assets: List<Asset> = emptyList(),
    val configUpdates: Map<String, Any> = emptyMap(),
    val clearCache: Boolean = false
)

data class HealthData(
    val batteryLevel: Int,
    val temperatureCelsius: Float,
    val storageFreeBytes: Long,
    val connectionType: String,
    val signalStrength: Int,
    val timestamp: String
)