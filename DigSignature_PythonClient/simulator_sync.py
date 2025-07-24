#!/usr/bin/env python3
"""
Simulator Sync Module
Handles synchronization with Django server
"""

import json
import requests
from PyQt6.QtCore import QObject, pyqtSignal


class SyncManager(QObject):
    """Handles sync operations with the server"""
    
    # Signals
    log_message = pyqtSignal(str, str, str, str)  # level, category, message, tag
    sync_completed = pyqtSignal(dict)  # sync_data
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.session = requests.Session()
        self.last_sync_hash = ""
        
    def check_server(self, health_data):
        """Check server for updates"""
        if self.config.get('offline_mode'):
            self.log_message.emit("DEBUG", "SYNC", "Offline mode - skipping server check", "SyncManager")
            return {"needs_sync": False}
            
        url = f"{self.config['server_url']}/scheduling/api/v1/device/check_server/"
        
        data = {
            "action": "check_server",
            "device_id": self.config['device_id'],
            "last_sync_hash": self.last_sync_hash,
            "app_version": "1.0.0-simulator",
            "firmware_version": "PyQt6-Simulator",
            "battery_level": health_data['battery'],
            "storage_free_mb": health_data['storage'],
            "connection_type": health_data['connection'],
            "device_health": {
                "temperature_celsius": health_data['temperature'],
                "signal_strength": health_data['signal']
            }
        }
        
        try:
            # Show full hash instead of truncated
            hash_display = self._format_hash(self.last_sync_hash)
            self.log_message.emit("DEBUG", "SYNC", f"Checking server - Battery: {health_data['battery']}%, Temp: {health_data['temperature']}°C, Hash: {hash_display}", "SyncManager")
            
            response = self.session.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                needs_sync = result.get('needs_sync', False)
                
                print(f"✅ Server check successful - needs_sync: {needs_sync}")
                self.log_message.emit("INFO", "SYNC", f"Server check successful - needs_sync: {needs_sync}", "SyncManager")
                
                if needs_sync and 'sync_data' in result:
                    self.log_message.emit("INFO", "SYNC", "Sync data received from server", "SyncManager")
                    
                    # Update sync hash
                    self.last_sync_hash = result.get('new_sync_hash', '')
                    new_hash_display = self._format_hash(self.last_sync_hash)
                    self.log_message.emit("DEBUG", "SYNC", f"Updated sync hash: {new_hash_display}", "SyncManager")
                    
                    # Process playlists info
                    sync_data = result['sync_data']
                    playlists = sync_data.get('playlists', [])
                    assets = sync_data.get('assets', [])
                    
                    if playlists:
                        playlist = playlists[0]
                        self.log_message.emit("INFO", "PLAYLIST", f"Received playlist: {playlist['name']}", "PlaylistManager")
                        
                    if assets:
                        self.log_message.emit("INFO", "DOWNLOAD", f"Processing {len(assets)} assets for download", "AssetManager")
                    
                    return {"needs_sync": True, "sync_data": sync_data}
                    
                # Handle emergency messages
                if 'emergency_messages' in result:
                    self.log_message.emit("WARN", "EMERGENCY", f"Received {len(result['emergency_messages'])} emergency messages", "EmergencyHandler")
                    
                # Handle system commands
                if 'system_commands' in result:
                    self.log_message.emit("INFO", "SYSTEM", f"Received {len(result['system_commands'])} system commands", "CommandHandler")
                
                return {"needs_sync": False}
                
            elif response.status_code == 404:
                print("⚠️ Device not registered on server")
                self.log_message.emit("WARN", "SYNC", "Device not registered on server - attempting re-registration", "SyncManager")
                return {"needs_sync": False, "error": "not_registered"}
                
            else:
                error_msg = f"Server check failed: HTTP {response.status_code} - {response.text[:200]}"
                print(f"❌ {error_msg}")
                self.log_message.emit("ERROR", "SYNC", error_msg, "SyncManager")
                return {"needs_sync": False, "error": "server_error"}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Server check network error: {e}"
            print(f"❌ {error_msg}")
            self.log_message.emit("ERROR", "NETWORK", error_msg, "SyncManager")
            return {"needs_sync": False, "error": "network_error"}
            
    def send_confirmation(self, sync_data):
        """Send sync confirmation to server"""
        url = f"{self.config['server_url']}/scheduling/api/v1/device/sync_confirmation/"
        data = {
            "device_id": self.config['device_id'],
            "sync_hash": self.last_sync_hash,
            "sync_stats": {
                "assets_downloaded": len(sync_data.get('assets', [])),
                "bytes_transferred": 1024000,  # Simulated
                "duration_seconds": 10  # Simulated
            }
        }
        
        try:
            response = self.session.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                print("✅ Sync confirmation sent")
                self.log_message.emit("INFO", "SYNC", "Sync confirmation sent successfully", "SyncConfirmation")
            else:
                print(f"⚠️ Sync confirmation failed: {response.status_code}")
                self.log_message.emit("WARN", "SYNC", f"Sync confirmation failed: HTTP {response.status_code}", "SyncConfirmation")
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Sync confirmation error: {e}"
            print(f"❌ {error_msg}")
            self.log_message.emit("ERROR", "NETWORK", error_msg, "SyncConfirmation")
            
    def _format_hash(self, hash_str):
        """Format hash for display (show more characters)"""
        if not hash_str:
            return "None"
        elif len(hash_str) <= 32:
            return hash_str
        else:
            return f"{hash_str[:16]}...{hash_str[-8:]}"
            
    def update_config(self, new_config):
        """Update configuration"""
        self.config.update(new_config)
