// managers/KioskManager.kt

package com.digitalsignage.managers

import android.app.Activity
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.ActivityInfo
import android.content.pm.PackageManager
import android.os.Build
import android.provider.Settings
import android.view.View
import android.view.WindowManager
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.digitalsignage.storage.PreferencesManager
import com.digitalsignage.utils.Constants
import com.digitalsignage.utils.Logger

class KioskManager(
    private val activity: Activity,
    private val preferencesManager: PreferencesManager,
    private val logger: Logger
) {

    private var isKioskEnabled = false
    private var windowInsetsController: WindowInsetsControllerCompat? = null

    // Variables para detección de salida del kiosk
    private var tapCount = 0
    private var lastTapTime = 0L

    /**
     * Callback para cuando se detecta intento de salida del kiosk
     */
    var onKioskExitDetected: (() -> Unit)? = null

    init {
        setupWindowInsetsController()
    }

    /**
     * Configura el controlador de ventana para ocultar barras del sistema
     */
    private fun setupWindowInsetsController() {
        WindowCompat.setDecorFitsSystemWindows(activity.window, false)
        windowInsetsController = WindowCompat.getInsetsController(activity.window, activity.window.decorView)

        windowInsetsController?.apply {
            // Comportamiento cuando se muestran las barras del sistema
            systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        }
    }

    /**
     * Activa el modo kiosk agresivo
     */
    fun enableKioskMode() {
        if (isKioskEnabled) return

        logger.i(Logger.Category.UI, "Enabling aggressive kiosk mode")

        try {
            // Configurar orientación
            setOrientation()

            // Ocultar barras del sistema
            hideSystemBars()

            // Configurar flags de ventana para modo kiosk
            setKioskWindowFlags()

            // Mantener pantalla encendida
            activity.window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

            // Configurar modo inmersivo sticky
            enableImmersiveMode()

            isKioskEnabled = true
            logger.i(Logger.Category.UI, "Kiosk mode enabled successfully")

        } catch (e: Exception) {
            logger.e(Logger.Category.UI, "Error enabling kiosk mode", exception = e)
        }
    }

    /**
     * Desactiva el modo kiosk
     */
    fun disableKioskMode() {
        if (!isKioskEnabled) return

        logger.i(Logger.Category.UI, "Disabling kiosk mode")

        try {
            // Restaurar barras del sistema
            showSystemBars()

            // Limpiar flags de ventana
            clearKioskWindowFlags()

            // Permitir orientación automática
            activity.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED

            isKioskEnabled = false
            logger.i(Logger.Category.UI, "Kiosk mode disabled")

        } catch (e: Exception) {
            logger.e(Logger.Category.UI, "Error disabling kiosk mode", exception = e)
        }
    }

    /**
     * Alterna el modo kiosk
     */
    fun toggleKioskMode() {
        if (isKioskEnabled) {
            disableKioskMode()
        } else {
            enableKioskMode()
        }
    }

    /**
     * Configura la orientación según preferencias
     */
    private fun setOrientation() {
        val orientation = when (preferencesManager.orientation) {
            Constants.ORIENTATION_PORTRAIT -> ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
            Constants.ORIENTATION_LANDSCAPE -> ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE
            else -> ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE
        }

        activity.requestedOrientation = orientation
        logger.d(Logger.Category.UI, "Set orientation: ${preferencesManager.orientation}")
    }

    /**
     * Cambia la orientación y la persiste
     */
    fun setOrientation(orientation: String) {
        preferencesManager.orientation = orientation

        val androidOrientation = when (orientation) {
            Constants.ORIENTATION_PORTRAIT -> ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
            Constants.ORIENTATION_LANDSCAPE -> ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE
            else -> ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE
        }

        activity.requestedOrientation = androidOrientation
        logger.i(Logger.Category.UI, "Orientation changed to: $orientation")
    }

    /**
     * Alterna entre portrait y landscape
     */
    fun toggleOrientation() {
        val newOrientation = if (preferencesManager.orientation == Constants.ORIENTATION_LANDSCAPE) {
            Constants.ORIENTATION_PORTRAIT
        } else {
            Constants.ORIENTATION_LANDSCAPE
        }

        setOrientation(newOrientation)
    }

    /**
     * Oculta las barras del sistema de forma agresiva
     */
    private fun hideSystemBars() {
        windowInsetsController?.hide(
            WindowInsetsCompat.Type.systemBars()
        )

        // Ocultar también la barra de navegación
        windowInsetsController?.hide(
            WindowInsetsCompat.Type.navigationBars()
        )

        logger.d(Logger.Category.UI, "System bars hidden")
    }

    /**
     * Muestra las barras del sistema
     */
    private fun showSystemBars() {
        windowInsetsController?.show(
            WindowInsetsCompat.Type.systemBars()
        )

        logger.d(Logger.Category.UI, "System bars shown")
    }

    /**
     * Configura flags específicos para modo kiosk
     */
    @Suppress("DEPRECATION")
    private fun setKioskWindowFlags() {
        val window = activity.window

        window.addFlags(
            WindowManager.LayoutParams.FLAG_FULLSCREEN or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                    WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
        )

        // Prevenir capturas de pantalla en modo kiosk (opcional)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        }
    }

    /**
     * Limpia los flags de modo kiosk
     */
    @Suppress("DEPRECATION")
    private fun clearKioskWindowFlags() {
        val window = activity.window

        window.clearFlags(
            WindowManager.LayoutParams.FLAG_FULLSCREEN or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                    WindowManager.LayoutParams.FLAG_SECURE
        )
    }

    /**
     * Habilita modo inmersivo sticky
     */
    @Suppress("DEPRECATION")
    private fun enableImmersiveMode() {
        val decorView = activity.window.decorView

        decorView.systemUiVisibility = (
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY or
                        View.SYSTEM_UI_FLAG_FULLSCREEN or
                        View.SYSTEM_UI_FLAG_HIDE_NAVIGATION or
                        View.SYSTEM_UI_FLAG_LAYOUT_STABLE or
                        View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION or
                        View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                )

        logger.d(Logger.Category.UI, "Immersive mode enabled")
    }

    /**
     * Detecta toques en la esquina para salir del modo kiosk
     */
    fun handleTouch(x: Float, y: Float, screenWidth: Int, screenHeight: Int): Boolean {
        if (!isKioskEnabled) return false

        // Detectar toque en esquina superior derecha
        val cornerThreshold = minOf(screenWidth, screenHeight) * Constants.KIOSK_TAP_CORNER_PERCENTAGE
        val isInCorner = x > (screenWidth - cornerThreshold) && y < cornerThreshold

        if (!isInCorner) {
            // Reset contador si toca fuera de la esquina
            tapCount = 0
            return false
        }

        val currentTime = System.currentTimeMillis()

        // Verificar timeout entre toques
        if (currentTime - lastTapTime > Constants.KIOSK_TAP_TIMEOUT) {
            tapCount = 1
        } else {
            tapCount++
        }

        lastTapTime = currentTime

        logger.d(Logger.Category.UI, "Corner tap detected: $tapCount/${Constants.KIOSK_EXIT_TAPS}")

        // Si se alcanzan los toques requeridos, solicitar salida
        if (tapCount >= Constants.KIOSK_EXIT_TAPS) {
            logger.i(Logger.Category.UI, "Kiosk exit sequence completed")
            tapCount = 0
            onKioskExitDetected?.invoke()
            return true
        }

        return true
    }

    /**
     * Fuerza el re-establecimiento del modo kiosk (llamar en onResume)
     */
    fun reinforceKioskMode() {
        if (isKioskEnabled) {
            // Re-aplicar configuraciones en caso de que el sistema las haya revertido
            hideSystemBars()
            enableImmersiveMode()

            logger.d(Logger.Category.UI, "Kiosk mode reinforced")
        }
    }

    /**
     * Maneja cambios de foco de la ventana
     */
    fun onWindowFocusChanged(hasFocus: Boolean) {
        if (hasFocus && isKioskEnabled) {
            // Re-aplicar modo inmersivo cuando la app recupera el foco
            hideSystemBars()
            enableImmersiveMode()

            logger.d(Logger.Category.UI, "Window focus regained, kiosk mode reapplied")
        }
    }

    /**
     * Verifica si hay permisos necesarios para modo kiosk avanzado
     */
    fun checkKioskPermissions(): Map<String, Boolean> {
        val permissions = mutableMapOf<String, Boolean>()

        // Verificar si se puede modificar configuraciones del sistema
        permissions["modify_system_settings"] = Settings.System.canWrite(activity)

        // Verificar si la app puede ser administrador de dispositivos
        // TODO: Implementar verificación de device admin si es necesario
        permissions["device_admin"] = false

        // Verificar si se pueden ocultar apps del launcher
        // TODO: Implementar verificación de launcher permissions si es necesario
        permissions["launcher_control"] = false

        return permissions
    }

    /**
     * Solicita permisos necesarios para modo kiosk avanzado
     */
    fun requestKioskPermissions() {
        try {
            // Solicitar permiso para modificar configuraciones del sistema
            if (!Settings.System.canWrite(activity)) {
                val intent = Intent(Settings.ACTION_MANAGE_WRITE_SETTINGS).apply {
                    data = android.net.Uri.parse("package:${activity.packageName}")
                }
                activity.startActivity(intent)

                logger.i(Logger.Category.UI, "Requesting system settings permission")
            }

        } catch (e: Exception) {
            logger.w(Logger.Category.UI, "Error requesting kiosk permissions", exception = e)
        }
    }

    /**
     * Obtiene el estado actual del modo kiosk
     */
    fun isKioskModeEnabled(): Boolean = isKioskEnabled

    /**
     * Obtiene información de estado para debugging
     */
    fun getKioskStatus(): Map<String, Any> {
        return mapOf(
            "kiosk_enabled" to isKioskEnabled,
            "orientation" to preferencesManager.orientation,
            "tap_count" to tapCount,
            "last_tap_time" to lastTapTime,
            "permissions" to checkKioskPermissions()
        )
    }
}