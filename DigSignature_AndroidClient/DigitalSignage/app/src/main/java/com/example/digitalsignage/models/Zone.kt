// models/Zone.kt
package com.digitalsignage.models

data class Zone(
    val id: String,
    val name: String,
    val position: Position,
    val zIndex: Int = 1,
    val allowedContentTypes: List<String> = emptyList()
)

data class Position(
    val x: Float,
    val y: Float,
    val width: Float,
    val height: Float
)

data class LayoutStructure(
    val zones: List<Zone>
)