// models/Scene.kt
package com.digitalsignage.models

data class Scene(
    val id: String,
    val name: String,
    val layout: String,
    val layoutStructure: LayoutStructure,
    val duration: Int,
    val transitionIn: String = "none",
    val transitionOut: String = "none",
    val zoneContents: List<ZoneContent> = emptyList()
)