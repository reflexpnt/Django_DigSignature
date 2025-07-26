// services/DownloadService.kt

package com.digitalsignage.services

import android.app.Service
import android.content.Intent
import android.os.IBinder

class DownloadService : Service() {

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // TODO: Implementar servicio de descarga
        return START_STICKY
    }
}