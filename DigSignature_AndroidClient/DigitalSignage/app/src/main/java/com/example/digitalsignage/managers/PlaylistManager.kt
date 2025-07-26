// managers/PlaylistManager.kt

package com.digitalsignage.managers

import android.content.Context
import android.widget.FrameLayout
import com.digitalsignage.models.Asset
import com.digitalsignage.models.Playlist
import com.digitalsignage.storage.FileManager
import com.digitalsignage.utils.Logger
import kotlinx.coroutines.*

class PlaylistManager(
    private val context: Context,
    private val container: FrameLayout,
    private val logger: Logger,
    private val fileManager: FileManager,
    private val assetManager: AssetManager
) {

    private var currentPlaylist: Playlist? = null
    private var isMuted = false

    /**
     * Actualiza la playlist actual
     */
    fun updatePlaylist(playlist: Playlist, assets: List<Asset>) {
        logger.i(Logger.Category.PLAYBACK, "Updating playlist: ${playlist.name}")
        currentPlaylist = playlist

        // TODO: Implementar cambio de playlist con doble buffer
        playFallbackContent()
    }

    /**
     * Reproduce contenido fallback
     */
    fun playFallbackContent() {
        logger.i(Logger.Category.PLAYBACK, "Playing fallback content")

        // TODO: Implementar reproducción de fallback desde res/raw
        container.removeAllViews()

        // Por ahora, solo limpiar el contenedor
    }

    /**
     * Establece el estado de mute
     */
    fun setMuted(muted: Boolean) {
        isMuted = muted
        logger.d(Logger.Category.PLAYBACK, "Audio ${if (muted) "muted" else "unmuted"}")
    }
}