// storage/FileManager.kt

package com.digitalsignage.storage

import android.content.Context
import com.digitalsignage.utils.Constants
import com.digitalsignage.utils.Logger
import java.io.File
import java.io.FileOutputStream
import java.security.MessageDigest
import kotlin.math.min

class FileManager(
    private val context: Context,
    private val logger: Logger
) {

    private val cacheDir: File by lazy {
        File(context.cacheDir, "digitalsignage").apply {
            if (!exists()) {
                mkdirs()
                logger.d(Logger.Category.STORAGE, "Created cache directory: $absolutePath")
            }
        }
    }

    /**
     * Directorios específicos por tipo de contenido
     */
    private val videosDir: File by lazy {
        File(cacheDir, Constants.CACHE_DIR_VIDEOS).apply { mkdirs() }
    }

    private val imagesDir: File by lazy {
        File(cacheDir, Constants.CACHE_DIR_IMAGES).apply { mkdirs() }
    }

    private val htmlDir: File by lazy {
        File(cacheDir, Constants.CACHE_DIR_HTML).apply { mkdirs() }
    }

    private val assetsDir: File by lazy {
        File(cacheDir, Constants.CACHE_DIR_ASSETS).apply { mkdirs() }
    }

    /**
     * Resultado de operaciones de archivo
     */
    sealed class FileResult {
        data class Success(val file: File) : FileResult()
        data class Error(val message: String, val exception: Throwable? = null) : FileResult()
    }

    /**
     * Guarda datos binarios en el cache
     */
    suspend fun saveAsset(
        assetId: String,
        contentType: String,
        originalName: String,
        data: ByteArray
    ): FileResult {
        return try {
            val targetDir = getDirectoryForContentType(contentType)
            val extension = getFileExtension(originalName)
            val fileName = "${assetId}.${extension}"
            val file = File(targetDir, fileName)

            logger.d(Logger.Category.STORAGE, "Saving asset: $fileName (${data.size} bytes)")

            FileOutputStream(file).use { output ->
                output.write(data)
                output.flush()
            }

            logger.i(Logger.Category.STORAGE, "Asset saved: ${file.name}")
            FileResult.Success(file)

        } catch (e: Exception) {
            val errorMsg = "Error saving asset $assetId: ${e.message}"
            logger.e(Logger.Category.STORAGE, errorMsg, exception = e)
            FileResult.Error(errorMsg, e)
        }
    }

    /**
     * Obtiene un asset del cache
     */
    fun getAsset(assetId: String, contentType: String): File? {
        val targetDir = getDirectoryForContentType(contentType)

        // Buscar archivo con cualquier extensión que empiece con el assetId
        val matchingFiles = targetDir.listFiles { _, name ->
            name.startsWith("$assetId.")
        }

        return matchingFiles?.firstOrNull()?.takeIf { it.exists() }
    }

    /**
     * Verifica si un asset existe en cache
     */
    fun assetExists(assetId: String, contentType: String): Boolean {
        return getAsset(assetId, contentType) != null
    }

    /**
     * Obtiene el directorio según el tipo de contenido
     */
    private fun getDirectoryForContentType(contentType: String): File {
        return when (contentType.lowercase()) {
            Constants.CONTENT_TYPE_VIDEO -> videosDir
            Constants.CONTENT_TYPE_IMAGE -> imagesDir
            Constants.CONTENT_TYPE_HTML -> htmlDir
            else -> assetsDir
        }
    }

    /**
     * Extrae la extensión del archivo manteniendo la original
     */
    private fun getFileExtension(fileName: String): String {
        val lastDot = fileName.lastIndexOf('.')
        return if (lastDot != -1 && lastDot < fileName.length - 1) {
            fileName.substring(lastDot + 1).lowercase()
        } else {
            "bin" // Extensión por defecto
        }
    }

    /**
     * Calcula el checksum MD5 de un archivo
     */
    fun calculateChecksum(file: File): String? {
        return try {
            val md = MessageDigest.getInstance("MD5")
            file.inputStream().use { input ->
                val buffer = ByteArray(8192)
                var bytesRead: Int
                while (input.read(buffer).also { bytesRead = it } != -1) {
                    md.update(buffer, 0, bytesRead)
                }
            }
            md.digest().joinToString("") { "%02x".format(it) }
        } catch (e: Exception) {
            logger.w(Logger.Category.STORAGE, "Error calculating checksum for ${file.name}", exception = e)
            null
        }
    }

    /**
     * Verifica la integridad de un archivo usando checksum
     */
    fun verifyFileIntegrity(file: File, expectedChecksum: String?): Boolean {
        if (expectedChecksum.isNullOrEmpty()) {
            logger.d(Logger.Category.STORAGE, "No checksum provided for ${file.name}, skipping verification")
            return true
        }

        val actualChecksum = calculateChecksum(file)
        val isValid = actualChecksum?.equals(expectedChecksum, ignoreCase = true) == true

        if (!isValid) {
            logger.w(Logger.Category.STORAGE, "Checksum mismatch for ${file.name}. Expected: $expectedChecksum, Got: $actualChecksum")
        }

        return isValid
    }

    /**
     * Obtiene un archivo fallback desde res/raw
     */
    fun getFallbackAsset(contentType: String): File? {
        return try {
            val fallbackFileName = when (contentType) {
                Constants.CONTENT_TYPE_VIDEO -> Constants.FALLBACK_VIDEO
                Constants.CONTENT_TYPE_IMAGE -> Constants.FALLBACK_IMAGE
                Constants.CONTENT_TYPE_HTML -> Constants.FALLBACK_HTML
                else -> null
            }

            if (fallbackFileName == null) {
                logger.w(Logger.Category.STORAGE, "No fallback available for content type: $contentType")
                return null
            }

            // Copiar desde res/raw al cache si no existe
            val fallbackFile = File(assetsDir, fallbackFileName)

            if (!fallbackFile.exists()) {
                copyFromRawResource(fallbackFileName, fallbackFile)
            }

            if (fallbackFile.exists()) {
                logger.d(Logger.Category.STORAGE, "Using fallback asset: ${fallbackFile.name}")
                fallbackFile
            } else {
                null
            }

        } catch (e: Exception) {
            logger.e(Logger.Category.STORAGE, "Error getting fallback asset", exception = e)
            null
        }
    }

    /**
     * Copia un archivo desde res/raw al sistema de archivos
     */
    private fun copyFromRawResource(fileName: String, targetFile: File) {
        try {
            val resourceName = fileName.substringBeforeLast('.')
            val resourceId = context.resources.getIdentifier(resourceName, "raw", context.packageName)

            if (resourceId == 0) {
                logger.w(Logger.Category.STORAGE, "Resource not found: $resourceName")
                return
            }

            context.resources.openRawResource(resourceId).use { input ->
                FileOutputStream(targetFile).use { output ->
                    input.copyTo(output)
                }
            }

            logger.d(Logger.Category.STORAGE, "Copied fallback resource: ${targetFile.name}")

        } catch (e: Exception) {
            logger.e(Logger.Category.STORAGE, "Error copying from raw resource", exception = e)
        }
    }

    /**
     * Lista todos los assets en cache
     */
    fun listCachedAssets(): Map<String, List<File>> {
        return mapOf(
            "videos" to (videosDir.listFiles()?.toList() ?: emptyList()),
            "images" to (imagesDir.listFiles()?.toList() ?: emptyList()),
            "html" to (htmlDir.listFiles()?.toList() ?: emptyList()),
            "assets" to (assetsDir.listFiles()?.toList() ?: emptyList())
        )
    }

    /**
     * Obtiene el tamaño total del cache
     */
    fun getCacheSize(): Long {
        return cacheDir.walkTopDown()
            .filter { it.isFile }
            .sumOf { it.length() }
    }

    /**
     * Limpia el cache si excede el tamaño máximo
     */
    fun cleanupCache() {
        try {
            val maxSizeBytes = Constants.CACHE_MAX_SIZE_MB * 1024L * 1024L
            val currentSize = getCacheSize()

            if (currentSize <= maxSizeBytes) {
                logger.d(Logger.Category.STORAGE, "Cache size OK: ${formatBytes(currentSize)} / ${formatBytes(maxSizeBytes)}")
                return
            }

            logger.w(Logger.Category.STORAGE, "Cache size exceeded: ${formatBytes(currentSize)} / ${formatBytes(maxSizeBytes)}")

            // Obtener todos los archivos ordenados por fecha de último acceso
            val allFiles = cacheDir.walkTopDown()
                .filter { it.isFile }
                .sortedBy { it.lastModified() }
                .toList()

            var deletedSize = 0L
            var deletedCount = 0

            // Eliminar archivos más antiguos hasta estar bajo el límite
            for (file in allFiles) {
                if (getCacheSize() <= maxSizeBytes) break

                val fileSize = file.length()
                if (file.delete()) {
                    deletedSize += fileSize
                    deletedCount++
                    logger.d(Logger.Category.STORAGE, "Deleted cache file: ${file.name}")
                }
            }

            logger.i(Logger.Category.STORAGE, "Cache cleanup completed: $deletedCount files (${formatBytes(deletedSize)}) deleted")

        } catch (e: Exception) {
            logger.e(Logger.Category.STORAGE, "Error during cache cleanup", exception = e)
        }
    }

    /**
     * Limpia todo el cache
     */
    fun clearAllCache(): Boolean {
        return try {
            val deletedFiles = cacheDir.walkTopDown()
                .filter { it.isFile }
                .count()

            cacheDir.deleteRecursively()
            cacheDir.mkdirs()

            // Recrear subdirectorios
            videosDir.mkdirs()
            imagesDir.mkdirs()
            htmlDir.mkdirs()
            assetsDir.mkdirs()

            logger.i(Logger.Category.STORAGE, "Cleared all cache: $deletedFiles files deleted")
            true

        } catch (e: Exception) {
            logger.e(Logger.Category.STORAGE, "Error clearing cache", exception = e)
            false
        }
    }

    /**
     * Obtiene información del almacenamiento
     */
    fun getStorageInfo(): Map<String, String> {
        val cacheSize = getCacheSize()
        val maxSize = Constants.CACHE_MAX_SIZE_MB * 1024L * 1024L
        val cachedAssets = listCachedAssets()
        val totalFiles = cachedAssets.values.sumOf { it.size }

        return mapOf(
            "cache_size" to formatBytes(cacheSize),
            "max_cache_size" to formatBytes(maxSize),
            "cache_usage_percent" to "%.1f%%".format((cacheSize.toDouble() / maxSize) * 100),
            "total_files" to totalFiles.toString(),
            "videos_count" to cachedAssets["videos"]?.size.toString(),
            "images_count" to cachedAssets["images"]?.size.toString(),
            "html_count" to cachedAssets["html"]?.size.toString(),
            "cache_directory" to cacheDir.absolutePath
        )
    }

    /**
     * Formatea bytes en formato legible
     */
    private fun formatBytes(bytes: Long): String {
        val units = arrayOf("B", "KB", "MB", "GB")
        var value = bytes.toDouble()
        var unitIndex = 0

        while (value >= 1024 && unitIndex < units.size - 1) {
            value /= 1024
            unitIndex++
        }

        return "%.1f %s".format(value, units[unitIndex])
    }
}