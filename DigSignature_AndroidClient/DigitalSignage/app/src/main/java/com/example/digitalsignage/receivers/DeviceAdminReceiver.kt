// receivers/DeviceAdminReceiver.kt

package com.digitalsignage.receivers

import android.app.admin.DeviceAdminReceiver
import android.content.Context
import android.content.Intent

class DeviceAdminReceiver : DeviceAdminReceiver() {

    override fun onEnabled(context: Context, intent: Intent) {
        super.onEnabled(context, intent)
        // TODO: Implementar cuando se habilita admin
    }

    override fun onDisabled(context: Context, intent: Intent) {
        super.onDisabled(context, intent)
        // TODO: Implementar cuando se deshabilita admin
    }
}