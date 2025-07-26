// models/Playlist.kt
package com.digitalsignage.models

data class Playlist(
    val id: String,
    val name: String,
    val lastModified: String,
    val scenes: List<Scene> = emptyList(),
    val isActive: Boolean = true,
    val totalDuration: Int = 0
)