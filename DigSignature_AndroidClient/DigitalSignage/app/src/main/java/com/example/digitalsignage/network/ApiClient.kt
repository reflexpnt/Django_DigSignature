// network/ApiClient.kt

package com.digitalsignage.network

import android.content.Context
import com.digitalsignage.utils.Constants
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

class ApiClient(private val context: Context) {

    private val client: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .addInterceptor(LoggingInterceptor())
            .addInterceptor(UserAgentInterceptor())
            .build()
    }

    /**
     * Interceptor para logging de requests/responses
     */
    private class LoggingInterceptor : Interceptor {
        override fun intercept(chain: Interceptor.Chain): Response {
            val request = chain.request()
            val startTime = System.currentTimeMillis()

            android.util.Log.d("ApiClient", "🌐 ${request.method} ${request.url}")

            try {
                val response = chain.proceed(request)
                val endTime = System.currentTimeMillis()
                val duration = endTime - startTime

                android.util.Log.d("ApiClient", "✅ ${response.code} ${request.url} (${duration}ms)")

                return response
            } catch (e: Exception) {
                val endTime = System.currentTimeMillis()
                val duration = endTime - startTime

                android.util.Log.e("ApiClient", "❌ ERROR ${request.url} (${duration}ms): ${e.message}")
                throw e
            }
        }
    }

    /**
     * Interceptor para User-Agent personalizado
     */
    private class UserAgentInterceptor : Interceptor {
        override fun intercept(chain: Interceptor.Chain): Response {
            val originalRequest = chain.request()
            val requestWithUserAgent = originalRequest.newBuilder()
                .header("User-Agent", "DigitalSignage-Android/1.0.0")
                .build()
            return chain.proceed(requestWithUserAgent)
        }
    }

    /**
     * Resultado de una operación de API
     */
    sealed class ApiResult<T> {
        data class Success<T>(val data: T) : ApiResult<T>()
        data class Error<T>(val message: String, val code: Int? = null, val exception: Throwable? = null) : ApiResult<T>()
    }

    /**
     * GET request genérico
     */
    suspend fun get(
        endpoint: String,
        queryParams: Map<String, String> = emptyMap()
    ): ApiResult<String> = withContext(Dispatchers.IO) {

        try {
            val baseUrl = "${Constants.SERVER_URL}$endpoint"
            var urlBuilder = baseUrl

            if (queryParams.isNotEmpty()) {
                val params = queryParams.map { "${it.key}=${it.value}" }.joinToString("&")
                urlBuilder = "$baseUrl?$params"
            }

            val request = Request.Builder()
                .url(urlBuilder)
                .get()
                .build()

            val response = client.newCall(request).execute()

            return@withContext handleResponse(response)

        } catch (e: IOException) {
            ApiResult.Error("Network error: ${e.message}", exception = e)
        } catch (e: Exception) {
            ApiResult.Error("Unexpected error: ${e.message}", exception = e)
        }
    }

    /**
     * POST request con JSON
     */
    suspend fun post(
        endpoint: String,
        jsonData: JSONObject
    ): ApiResult<String> = withContext(Dispatchers.IO) {

        try {
            val mediaType = "application/json; charset=utf-8".toMediaType()
            val requestBody = jsonData.toString().toRequestBody(mediaType)

            val request = Request.Builder()
                .url("${Constants.SERVER_URL}$endpoint")
                .post(requestBody)
                .build()

            val response = client.newCall(request).execute()

            return@withContext handleResponse(response)

        } catch (e: IOException) {
            ApiResult.Error("Network error: ${e.message}", exception = e)
        } catch (e: Exception) {
            ApiResult.Error("Unexpected error: ${e.message}", exception = e)
        }
    }

    /**
     * PUT request con JSON
     */
    suspend fun put(
        endpoint: String,
        jsonData: JSONObject
    ): ApiResult<String> = withContext(Dispatchers.IO) {

        try {
            val mediaType = "application/json; charset=utf-8".toMediaType()
            val requestBody = jsonData.toString().toRequestBody(mediaType)

            val request = Request.Builder()
                .url("${Constants.SERVER_URL}$endpoint")
                .put(requestBody)
                .build()

            val response = client.newCall(request).execute()

            return@withContext handleResponse(response)

        } catch (e: IOException) {
            ApiResult.Error("Network error: ${e.message}", exception = e)
        } catch (e: Exception) {
            ApiResult.Error("Unexpected error: ${e.message}", exception = e)
        }
    }

    /**
     * DELETE request
     */
    suspend fun delete(
        endpoint: String
    ): ApiResult<String> = withContext(Dispatchers.IO) {

        try {
            val request = Request.Builder()
                .url("${Constants.SERVER_URL}$endpoint")
                .delete()
                .build()

            val response = client.newCall(request).execute()

            return@withContext handleResponse(response)

        } catch (e: IOException) {
            ApiResult.Error("Network error: ${e.message}", exception = e)
        } catch (e: Exception) {
            ApiResult.Error("Unexpected error: ${e.message}", exception = e)
        }
    }

    /**
     * Descarga un archivo desde una URL
     */
    suspend fun downloadFile(
        url: String,
        onProgress: ((bytesDownloaded: Long, totalBytes: Long) -> Unit)? = null
    ): ApiResult<ByteArray> = withContext(Dispatchers.IO) {

        try {
            val request = Request.Builder()
                .url(url)
                .get()
                .build()

            val response = client.newCall(request).execute()

            if (!response.isSuccessful) {
                return@withContext ApiResult.Error("Download failed: ${response.code}", response.code)
            }

            val responseBody = response.body
                ?: return@withContext ApiResult.Error("Empty response body")

            val totalBytes = responseBody.contentLength()
            val inputStream = responseBody.byteStream()
            val buffer = ByteArray(Constants.DOWNLOAD_CHUNK_SIZE)
            var bytesDownloaded = 0L
            var bytesRead: Int
            val outputStream = java.io.ByteArrayOutputStream()

            while (inputStream.read(buffer).also { bytesRead = it } != -1) {
                outputStream.write(buffer, 0, bytesRead)
                bytesDownloaded += bytesRead

                onProgress?.invoke(bytesDownloaded, totalBytes)
            }

            inputStream.close()
            responseBody.close()

            ApiResult.Success(outputStream.toByteArray())

        } catch (e: IOException) {
            ApiResult.Error("Download error: ${e.message}", exception = e)
        } catch (e: Exception) {
            ApiResult.Error("Unexpected download error: ${e.message}", exception = e)
        }
    }

    /**
     * Maneja la respuesta HTTP común
     */
    private fun handleResponse(response: Response): ApiResult<String> {
        return try {
            val responseBody = response.body?.string() ?: ""

            when {
                response.isSuccessful -> {
                    ApiResult.Success(responseBody)
                }
                response.code == 404 -> {
                    ApiResult.Error("Resource not found", 404)
                }
                response.code == 401 -> {
                    ApiResult.Error("Unauthorized", 401)
                }
                response.code == 403 -> {
                    ApiResult.Error("Forbidden", 403)
                }
                response.code == 500 -> {
                    ApiResult.Error("Server error", 500)
                }
                response.code >= 400 -> {
                    ApiResult.Error("Client error: $responseBody", response.code)
                }
                else -> {
                    ApiResult.Error("Unknown error: ${response.code}", response.code)
                }
            }
        } catch (e: Exception) {
            ApiResult.Error("Error reading response: ${e.message}", response.code, e)
        } finally {
            response.close()
        }
    }

    /**
     * Verifica si el servidor está disponible
     */
    suspend fun ping(): ApiResult<Boolean> {
        return when (val result = get("/")) {
            is ApiResult.Success -> ApiResult.Success(true)
            is ApiResult.Error -> ApiResult.Success(false) // Servidor no disponible pero no es error crítico
        }
    }
}