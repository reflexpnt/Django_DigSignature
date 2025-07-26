// managers/AssetManager.kt

package com.digitalsignage.managers

import android.content.Context
import com.digitalsignage.models.Asset
import com.digitalsignage.network.ApiClient
import com.digitalsignage.storage.FileManager
import com.digitalsignage.utils.Constants
import com.digitalsignage.utils.Logger
import kotlinx.coroutines.*
import okhttp3.ResponseBody
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.io.InputStream
import java.security.MessageDigest
import java.util.concurrent.ConcurrentHashMap

class AssetManager(
    private val context: Context,
    private val apiClient: ApiClient,
    private val fileManager: FileManager,
    private val logger: Logger
) {

    // Callbacks para progreso y eventos
    var onDownloadProgress: ((assetId: String, progress: Int) -> Unit)? = null
    var onDownloadCompleted: ((assetId: String, success: Boolean) -> Unit)? = null
    var onSpaceCleared: ((assetsRemoved: Int, spaceFreed: Long) -> Unit)? = null

    // Control de descargas concurrentes
    private val activeDownloads = ConcurrentHashMap<String, Job>()
    private val downloadScope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    // Cache de checksums calculados
    private val checksumCache = ConcurrentHashMap<String, String>()

    /**
     * Procesa una lista de assets para sincronización
     * - Detecta assets nuevos y modificados
     * - Descarga assets necesarios
     * - Elimina assets obsoletos
     */
    suspend fun processAssetsForSync(assets: List<Asset>, deletedAssetIds: List<String> = emptyList()) {
        logger.i(Logger.Category.STORAGE, "Processing ${assets.size} assets for sync")

        try {
            // 1. Limpiar assets eliminados del servidor
            if (deletedAssetIds.isNotEmpty()) {
                cleanupDeletedAssets(deletedAssetIds)
            }

            // 2. Verificar espacio disponible antes de descargar
            ensureSufficientSpace(assets)

            // 3. Procesar assets nuevos y modificados
            val assetsToDownload = identifyAssetsToDownload(assets)

            if (assetsToDownload.isNotEmpty()) {
                logger.i(Logger.Category.STORAGE, "Need to download ${assetsToDownload.size} assets")
                downloadAssets(assetsToDownload)
            } else {
                logger.i(Logger.Category.STORAGE, "All assets are up to date")
            }

        } catch (e: Exception) {
            logger.e(Logger.Category.STORAGE, "Error processing assets for sync", exception = e)
            throw e
        }
    }

    /**
     * Identifica qué assets necesitan ser descargados
     * Compara checksums locales vs del servidor
     */
    private fun identifyAssetsToDownload(assets: List<Asset>): List<Asset> {
        val assetsToDownload = mutableListOf<Asset>()

        for (asset in assets) {
            val localFile = getAssetFile(asset)

            when {
                // Asset no existe localmente
                !localFile.exists() -> {
                    logger.d(Logger.Category.STORAGE, "Asset ${asset.id} not found locally")
                    assetsToDownload.add(asset)
                }

                // Asset existe pero checksum no coincide
                asset.checksum.isNotBlank() && !isAssetValidLocally(asset, localFile) -> {
                    logger.d(Logger.Category.STORAGE, "Asset ${asset.id} checksum mismatch, needs update")
                    assetsToDownload.add(asset)
                }

                // Asset está actualizado
                else -> {
                    logger.v(Logger.Category.STORAGE, "Asset ${asset.id} is up to date")
                }
            }
        }

        return assetsToDownload
    }

    /**
     * Verifica si un asset local es válido comparando checksums
     */
    private fun isAssetValidLocally(asset: Asset, localFile: File): Boolean {
        if (asset.checksum.isBlank()) {
            // Sin checksum del servidor, asumir válido
            return true
        }

        val localChecksum = calculateFileChecksum(localFile)
        return localChecksum == asset.checksum
    }

    /**
     * Descarga una lista de assets de forma concurrente
     */
    private suspend fun downloadAssets(assets: List<Asset>) {
        val downloadJobs = assets.map { asset ->
            downloadScope.async {
                downloadAsset(asset)
            }
        }

        // Esperar a que todas las descargas terminen
        downloadJobs.awaitAll()
    }

    /**
     * Descarga un asset individual con verificación de integridad
     */
    private suspend fun downloadAsset(asset: Asset): Boolean {
        val assetId = asset.id

        // Verificar si ya se está descargando
        if (activeDownloads.containsKey(assetId)) {
            logger.w(Logger.Category.STORAGE, "Asset $assetId is already being downloaded")
            return false
        }

        val downloadJob = downloadScope.launch {
            try {
                logger.i(Logger.Category.STORAGE, "Starting download of asset: ${asset.name} (${asset.id})")
                onDownloadProgress?.invoke(assetId, 0)

                // Crear directorio de destino
                val targetFile = getAssetFile(asset)
                targetFile.parentFile?.mkdirs()

                // Archivo temporal para descarga
                val tempFile = File(targetFile.parent, "${targetFile.name}.tmp")

                // Descargar desde servidor
                val success = downloadAssetFromServer(asset, tempFile)

                if (success) {
                    // Verificar checksum si está disponible
                    if (asset.checksum.isNotBlank()) {
                        val downloadedChecksum = calculateFileChecksum(tempFile)
                        if (downloadedChecksum != asset.checksum) {
                            logger.e(Logger.Category.STORAGE,
                                "Checksum verification failed for asset ${asset.id}. " +
                                        "Expected: ${asset.checksum}, Got: $downloadedChecksum")
                            tempFile.delete()
                            onDownloadCompleted?.invoke(assetId, false)
                            return@launch
                        }
                    }

                    // Mover archivo temporal al destino final
                    if (tempFile.renameTo(targetFile)) {
                        logger.i(Logger.Category.STORAGE, "Successfully downloaded asset: ${asset.name}")
                        onDownloadProgress?.invoke(assetId, 100)
                        onDownloadCompleted?.invoke(assetId, true)
                    } else {
                        logger.e(Logger.Category.STORAGE, "Failed to move downloaded file for asset ${asset.id}")
                        tempFile.delete()
                        onDownloadCompleted?.invoke(assetId, false)
                    }
                } else {
                    logger.e(Logger.Category.STORAGE, "Failed to download asset ${asset.id}")
                    tempFile.delete()
                    onDownloadCompleted?.invoke(assetId, false)
                }

            } catch (e: Exception) {
                logger.e(Logger.Category.STORAGE, "Error downloading asset $assetId", exception = e)
                onDownloadCompleted?.invoke(assetId, false)
            }
        }

        activeDownloads[assetId] = downloadJob
        downloadJob.join()
        activeDownloads.remove(assetId)

        return downloadJob.isCompleted && !downloadJob.isCancelled
    }

    /**
     * Descarga un asset desde el servidor usando la API
     */
    private suspend fun downloadAssetFromServer(asset: Asset, targetFile: File): Boolean {
        return try {
            val downloadUrl = "${Constants.SERVER_URL}/scheduling/api/v1/assets/${asset.id}/download/"

            logger.d(Logger.Category.NETWORK, "Downloading from: $downloadUrl")

            val response = apiClient.downloadFile(downloadUrl)

            if (response.isSuccessful) {
                val responseBody = response.body
                if (responseBody != null) {
                    saveResponseToFile(responseBody, targetFile, asset)
                } else {
                    logger.e(Logger.Category.NETWORK, "Empty response body for asset ${asset.id}")
                    false
                }
            } else {
                logger.e(Logger.Category.NETWORK,
                    "Download failed for asset ${asset.id}: ${response.code} ${response.message}")
                false
            }
        } catch (e: Exception) {
            logger.e(Logger.Category.NETWORK, "Network error downloading asset ${asset.id}", exception = e)
            false
        }
    }

    /**
     * Guarda la respuesta HTTP a un archivo con progreso
     */
    private suspend fun saveResponseToFile(responseBody: ResponseBody, targetFile: File, asset: Asset): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                val inputStream: InputStream = responseBody.byteStream()
                val outputStream = FileOutputStream(targetFile)

                val totalBytes = responseBody.contentLength()
                var downloadedBytes = 0L
                val buffer = ByteArray(4096)

                var bytesRead: Int
                while (inputStream.read(buffer).also { bytesRead = it } != -1) {
                    outputStream.write(buffer, 0, bytesRead)
                    downloadedBytes += bytesRead

                    // Reportar progreso (evitar demasiadas actualizaciones)
                    if (totalBytes > 0 && downloadedBytes % 8192 == 0L) {
                        val progress = ((downloadedBytes * 100) / totalBytes).toInt()
                        onDownloadProgress?.invoke(asset.id, progress)
                    }
                }

                outputStream.close()
                inputStream.close()

                logger.d(Logger.Category.STORAGE,
                    "Downloaded ${downloadedBytes} bytes for asset ${asset.id}")

                true
            } catch (e: Exception) {
                logger.e(Logger.Category.STORAGE, "Error saving asset ${asset.id} to file", exception = e)
                false
            }
        }
    }

    /**
     * Limpia assets que fueron eliminados del servidor
     */
    private fun cleanupDeletedAssets(deletedAssetIds: List<String>) {
        logger.i(Logger.Category.STORAGE, "Cleaning up ${deletedAssetIds.size} deleted assets")

        for (assetId in deletedAssetIds) {
            try {
                // Buscar archivos que coincidan con este asset ID
                val assetFiles = findAssetFiles(assetId)
                for (file in assetFiles) {
                    if (file.delete()) {
                        logger.d(Logger.Category.STORAGE, "Deleted asset file: ${file.name}")
                    } else {
                        logger.w(Logger.Category.STORAGE, "Failed to delete asset file: ${file.name}")
                    }
                }

                // Limpiar checksum del cache
                checksumCache.remove(assetId)

            } catch (e: Exception) {
                logger.e(Logger.Category.STORAGE, "Error deleting asset $assetId", exception = e)
            }
        }
    }

    /**
     * Asegura que hay suficiente espacio antes de descargar
     */
    private suspend fun ensureSufficientSpace(assets: List<Asset>) {
        val requiredSpace = assets.sumOf { it.sizeBytes }
        val availableSpace = fileManager.getAvailableSpace()

        logger.d(Logger.Category.STORAGE,
            "Required space: ${requiredSpace / 1024 / 1024}MB, Available: ${availableSpace / 1024 / 1024}MB")

        if (requiredSpace > availableSpace) {
            logger.w(Logger.Category.STORAGE, "Insufficient space, clearing old assets")
            val clearedSpace = clearOldAssets(requiredSpace - availableSpace)

            if (clearedSpace < (requiredSpace - availableSpace)) {
                throw Exception("Insufficient storage space even after cleanup")
            }
        }
    }

    /**
     * Limpia assets antiguos para liberar espacio
     */
    private suspend fun clearOldAssets(spaceNeeded: Long): Long {
        return withContext(Dispatchers.IO) {
            var spaceCleared = 0L
            var assetsRemoved = 0

            try {
                val assetDirs = listOf(
                    fileManager.getVideoDir(),
                    fileManager.getImageDir(),
                    fileManager.getHtmlDir()
                )

                // Obtener todos los archivos ordenados por fecha de último acceso
                val allFiles = mutableListOf<File>()
                for (dir in assetDirs) {
                    if (dir.exists()) {
                        dir.listFiles()?.let { files ->
                            allFiles.addAll(files.filter { it.isFile })
                        }
                    }
                }

                // Ordenar por fecha de último acceso (más antiguos primero)
                allFiles.sortBy { it.lastModified() }

                // Eliminar archivos hasta liberar suficiente espacio
                for (file in allFiles) {
                    if (spaceCleared >= spaceNeeded) break

                    val fileSize = file.length()
                    if (file.delete()) {
                        spaceCleared += fileSize
                        assetsRemoved++
                        logger.d(Logger.Category.STORAGE, "Removed old asset: ${file.name}")
                    }
                }

                logger.i(Logger.Category.STORAGE,
                    "Cleared ${spaceCleared / 1024 / 1024}MB by removing $assetsRemoved assets")

                onSpaceCleared?.invoke(assetsRemoved, spaceCleared)

            } catch (e: Exception) {
                logger.e(Logger.Category.STORAGE, "Error clearing old assets", exception = e)
            }

            spaceCleared
        }
    }

    /**
     * Calcula el checksum SHA256 de un archivo
     */
    private fun calculateFileChecksum(file: File): String {
        if (!file.exists()) return ""

        // Verificar cache primero
        val cacheKey = "${file.absolutePath}:${file.lastModified()}"
        checksumCache[cacheKey]?.let { return it }

        return try {
            val digest = MessageDigest.getInstance("SHA-256")
            file.inputStream().use { inputStream ->
                val buffer = ByteArray(8192)
                var bytesRead: Int
                while (inputStream.read(buffer).also { bytesRead = it } != -1) {
                    digest.update(buffer, 0, bytesRead)
                }
            }

            val checksum = digest.digest().joinToString("") { "%02x".format(it) }

            // Guardar en cache
            checksumCache[cacheKey] = checksum

            checksum
        } catch (e: Exception) {
            logger.e(Logger.Category.STORAGE, "Error calculating checksum for ${file.name}", exception = e)
            ""
        }
    }

    /**
     * Obtiene el archivo local para un asset
     */
    private fun getAssetFile(asset: Asset): File {
        val dir = when (asset.type.lowercase()) {
            "video" -> fileManager.getVideoDir()
            "image" -> fileManager.getImageDir()
            "html" -> fileManager.getHtmlDir()
            else -> fileManager.getAssetDir()
        }

        // Usar el nombre original si está disponible, sino usar el nombre del asset
        val fileName = if (asset.originalName?.isNotBlank() == true) {
            asset.originalName!!
        } else {
            "${asset.name}.${getExtensionForType(asset.type)}"
        }

        return File(dir, fileName)
    }

    /**
     * Busca archivos de un asset por ID (útil para limpieza)
     */
    private fun findAssetFiles(assetId: String): List<File> {
        val foundFiles = mutableListOf<File>()
        val searchDirs = listOf(
            fileManager.getVideoDir(),
            fileManager.getImageDir(),
            fileManager.getHtmlDir(),
            fileManager.getAssetDir()
        )

        for (dir in searchDirs) {
            if (dir.exists()) {
                dir.listFiles()?.forEach { file ->
                    // Buscar archivos que contengan el asset ID en el nombre
                    if (file.name.contains(assetId)) {
                        foundFiles.add(file)
                    }
                }
            }
        }

        return foundFiles
    }

    /**
     * Obtiene la extensión por defecto para un tipo de asset
     */
    private fun getExtensionForType(type: String): String {
        return when (type.lowercase()) {
            "video" -> "mp4"
            "image" -> "jpg"
            "html" -> "html"
            "audio" -> "mp3"
            else -> "bin"
        }
    }

    /**
     * Verifica si un asset está descargado y es válido
     */
    fun isAssetDownloaded(asset: Asset): Boolean {
        val localFile = getAssetFile(asset)
        return localFile.exists() && isAssetValidLocally(asset, localFile)
    }

    /**
     * Obtiene la ruta local de un asset descargado
     */
    fun getAssetLocalPath(asset: Asset): String? {
        val localFile = getAssetFile(asset)
        return if (localFile.exists()) localFile.absolutePath else null
    }

    /**
     * Cancela todas las descargas activas
     */
    fun cancelAllDownloads() {
        logger.i(Logger.Category.STORAGE, "Cancelling ${activeDownloads.size} active downloads")

        activeDownloads.values.forEach { job ->
            job.cancel()
        }
        activeDownloads.clear()
    }

    /**
     * Obtiene estadísticas del asset manager
     */
    fun getStats(): Map<String, Any> {
        val videoDir = fileManager.getVideoDir()
        val imageDir = fileManager.getImageDir()
        val htmlDir = fileManager.getHtmlDir()

        val videoCount = videoDir.listFiles()?.size ?: 0
        val imageCount = imageDir.listFiles()?.size ?: 0
        val htmlCount = htmlDir.listFiles()?.size ?: 0

        return mapOf(
            "total_assets" to (videoCount + imageCount + htmlCount),
            "video_assets" to videoCount,
            "image_assets" to imageCount,
            "html_assets" to htmlCount,
            "active_downloads" to activeDownloads.size,
            "cache_size" to fileManager.getCacheSize(),
            "available_space" to fileManager.getAvailableSpace()
        )
    }

    /**
     * Limpieza al destruir el manager
     */
    fun cleanup() {
        cancelAllDownloads()
        downloadScope.cancel()
        checksumCache.clear()
    }
}