// services/LogService.kt

package com.digitalsignage.services

import android.app.Service
import android.content.Intent
import android.os.IBinder

class LogService : Service() {

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // TODO: Implementar servicio de logging
        return START_STICKY
    }
}