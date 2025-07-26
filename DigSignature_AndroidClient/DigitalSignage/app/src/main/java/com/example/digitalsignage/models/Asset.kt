// models/Asset.kt
package com.digitalsignage.models

data class Asset(
    val id: String,
    val name: String,
    val type: String,
    val originalName: String,
    val localPath: String? = null,
    val downloadUrl: String? = null,
    val checksum: String? = null,
    val fileSize: Long = 0,
    val isDownloaded: Boolean = false,
    val downloadProgress: Int = 0,
    val lastModified: String? = null
)