// models/Content.kt
package com.digitalsignage.models

data class Content(
    val id: String,
    val type: String,
    val name: String,
    val downloadUrl: String? = null,
    val url: String? = null,
    val text: String? = null,
    val duration: Int,
    val fileSize: Long? = null,
    val checksum: String? = null,
    val metadata: Map<String, Any> = emptyMap()
)

data class ZoneContent(
    val zoneId: String,
    val content: Content,
    val configuration: Map<String, Any> = emptyMap()
)