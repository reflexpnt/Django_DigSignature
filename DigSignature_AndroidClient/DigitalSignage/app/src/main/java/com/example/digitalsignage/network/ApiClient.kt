// network/ApiClient.kt

package com.digitalsignage.network

import android.content.Context
import com.digitalsignage.utils.Constants
import com.digitalsignage.utils.Logger
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

class ApiClient(private val context: Context) {

    private val client: OkHttpClient
    private var logger: Logger? = null

    init {
        client = OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS)
            .addInterceptor(LoggingInterceptor())
            .build()
    }

    /**
     * Establece el logger para uso interno
     */
    fun setLogger(logger: Logger) {
        this.logger = logger
    }

    /**
     * Registra un dispositivo en el servidor
     */
    suspend fun registerDevice(deviceData: JSONObject): Response {
        return withContext(Dispatchers.IO) {
            val url = "${Constants.SERVER_URL}/players/api/register/"

            val requestBody = deviceData.toString()
                .toRequestBody("application/json; charset=utf-8".toMediaType())

            val request = Request.Builder()
                .url(url)
                .post(requestBody)
                .build()

            logger?.d(Logger.Category.NETWORK, "Registering device: $url")
            client.newCall(request).execute()
        }
    }

    /**
     * Verifica el servidor para sincronización (endpoint principal)
     */
    suspend fun checkServer(syncRequest: JSONObject): Response {
        return withContext(Dispatchers.IO) {
            val url = "${Constants.SERVER_URL}/scheduling/api/v1/device/check_server/"

            val requestBody = syncRequest.toString()
                .toRequestBody("application/json; charset=utf-8".toMediaType())

            val request = Request.Builder()
                .url(url)
                .post(requestBody)
                .build()

            logger?.d(Logger.Category.NETWORK, "Checking server for sync: $url")
            client.newCall(request).execute()
        }
    }

    /**
     * Confirma sincronización completada al servidor
     */
    suspend fun confirmSync(confirmationData: JSONObject): Response {
        return withContext(Dispatchers.IO) {
            val url = "${Constants.SERVER_URL}/scheduling/api/v1/device/sync_confirmation/"

            val requestBody = confirmationData.toString()
                .toRequestBody("application/json; charset=utf-8".toMediaType())

            val request = Request.Builder()
                .url(url)
                .post(requestBody)
                .build()

            logger?.d(Logger.Category.NETWORK, "Confirming sync: $url")
            client.newCall(request).execute()
        }
    }

    /**
     * Descarga un archivo (asset) desde el servidor
     */
    suspend fun downloadFile(downloadUrl: String): Response {
        return withContext(Dispatchers.IO) {
            val fullUrl = if (downloadUrl.startsWith("http")) {
                downloadUrl
            } else {
                "${Constants.SERVER_URL}$downloadUrl"
            }

            val request = Request.Builder()
                .url(fullUrl)
                .get()
                .build()

            logger?.d(Logger.Category.NETWORK, "Downloading file: $fullUrl")
            client.newCall(request).execute()
        }
    }

    /**
     * Envía un log individual al servidor
     */
    suspend fun sendLogEntry(logData: JSONObject): Response {
        return withContext(Dispatchers.IO) {
            val url = "${Constants.SERVER_URL}/players/api/logs/single/"

            val requestBody = logData.toString()
                .toRequestBody("application/json; charset=utf-8".toMediaType())

            val request = Request.Builder()
                .url(url)
                .post(requestBody)
                .build()

            // No usar logger aquí para evitar loops infinitos
            client.newCall(request).execute()
        }
    }

    /**
     * Envía logs en batch al servidor
     */
    suspend fun sendLogsBatch(batchData: JSONObject): Response {
        return withContext(Dispatchers.IO) {
            val url = "${Constants.SERVER_URL}/players/api/logs/batch/"

            val requestBody = batchData.toString()
                .toRequestBody("application/json; charset=utf-8".toMediaType())

            val request = Request.Builder()
                .url(url)
                .post(requestBody)
                .build()

            // No usar logger aquí para evitar loops infinitos
            client.newCall(request).execute()
        }
    }

    /**
     * Confirma mensaje de emergencia
     */
    suspend fun acknowledgeEmergencyMessage(ackData: JSONObject): Response {
        return withContext(Dispatchers.IO) {
            val url = "${Constants.SERVER_URL}/scheduling/api/v1/device/emergency_ack/"

            val requestBody = ackData.toString()
                .toRequestBody("application/json; charset=utf-8".toMediaType())

            val request = Request.Builder()
                .url(url)
                .post(requestBody)
                .build()

            logger?.d(Logger.Category.NETWORK, "Acknowledging emergency message: $url")
            client.newCall(request).execute()
        }
    }

    /**
     * Descarga thumbnail de un asset
     */
    suspend fun downloadThumbnail(assetId: String): Response {
        return withContext(Dispatchers.IO) {
            val url = "${Constants.SERVER_URL}/scheduling/api/v1/assets/$assetId/thumbnail/"

            val request = Request.Builder()
                .url(url)
                .get()
                .build()

            logger?.d(Logger.Category.NETWORK, "Downloading thumbnail: $url")
            client.newCall(request).execute()
        }
    }

    /**
     * Interceptor para logging de requests HTTP
     */
    private inner class LoggingInterceptor : Interceptor {
        override fun intercept(chain: Interceptor.Chain): Response {
            val request = chain.request()
            val startTime = System.currentTimeMillis()

            try {
                val response = chain.proceed(request)
                val endTime = System.currentTimeMillis()
                val duration = endTime - startTime

                // Log de la request exitosa
                logger?.v(Logger.Category.NETWORK,
                    "${request.method} ${request.url} -> ${response.code} (${duration}ms)")

                return response

            } catch (e: IOException) {
                val endTime = System.currentTimeMillis()
                val duration = endTime - startTime

                // Log de error de red
                logger?.e(Logger.Category.NETWORK,
                    "${request.method} ${request.url} -> NETWORK_ERROR (${duration}ms): ${e.message}",
                    exception = e)

                throw e
            }
        }
    }

    /**
     * Verifica conectividad con el servidor
     */
    suspend fun checkConnectivity(): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                val url = "${Constants.SERVER_URL}/scheduling/api/v1/device/check_server/"

                val testRequest = JSONObject().apply {
                    put("action", "connectivity_test")
                    put("device_id", "test")
                    put("last_sync_hash", "")
                }

                val requestBody = testRequest.toString()
                    .toRequestBody("application/json; charset=utf-8".toMediaType())

                val request = Request.Builder()
                    .url(url)
                    .post(requestBody)
                    .build()

                val response = client.newCall(request).execute()
                val isConnected = response.isSuccessful

                logger?.d(Logger.Category.NETWORK,
                    "Connectivity check: ${if (isConnected) "SUCCESS" else "FAILED (${response.code})"}")

                response.close()
                isConnected

            } catch (e: Exception) {
                logger?.w(Logger.Category.NETWORK, "Connectivity check failed", exception = e)
                false
            }
        }
    }

    /**
     * Obtiene información del servidor
     */
    suspend fun getServerInfo(): JSONObject? {
        return withContext(Dispatchers.IO) {
            try {
                val url = "${Constants.SERVER_URL}/api/server/info/"

                val request = Request.Builder()
                    .url(url)
                    .get()
                    .build()

                val response = client.newCall(request).execute()

                if (response.isSuccessful) {
                    val responseBody = response.body()?.string()
                    if (responseBody != null) {
                        JSONObject(responseBody)
                    } else null
                } else {
                    logger?.w(Logger.Category.NETWORK, "Failed to get server info: ${response.code()}")
                    null
                }

            } catch (e: Exception) {
                logger?.w(Logger.Category.NETWORK, "Error getting server info", exception = e)
                null
            }
        }
    }

    /**
     * Cancela todas las requests pendientes
     */
    fun cancelAllRequests() {
        client.dispatcher.cancelAll()
        logger?.i(Logger.Category.NETWORK, "All network requests cancelled")
    }

    /**
     * Obtiene estadísticas del cliente HTTP
     */
    fun getNetworkStats(): Map<String, Any> {
        val dispatcher = client.dispatcher

        return mapOf(
            "running_calls" to dispatcher.runningCallsCount(),
            "queued_calls" to dispatcher.queuedCallsCount(),
            "max_requests" to dispatcher.maxRequests,
            "max_requests_per_host" to dispatcher.maxRequestsPerHost,
            "connection_pool_idle_count" to client.connectionPool.idleConnectionCount(),
            "connection_pool_total_count" to client.connectionPool.connectionCount()
        )
    }
}