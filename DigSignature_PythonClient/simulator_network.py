#!/usr/bin/env python3
"""
Simulator Network Module
Handles device registration and network operations
"""

import json
import requests
from PyQt6.QtCore import QObject, pyqtSignal


class NetworkManager(QObject):
    """Handles network operations for the simulator"""
    
    # Signals
    log_message = pyqtSignal(str, str, str, str)  # level, category, message, tag
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.session = requests.Session()
        
    def register_device(self):
        """Register device with server"""
        if self.config.get('offline_mode'):
            print("📴 Offline mode - skipping registration")
            self.log_message.emit("WARN", "REGISTRATION", "Offline mode - skipping registration", "DeviceRegistration")
            return True
            
        url = f"{self.config['server_url']}/players/api/register/"
        data = {
            "device_id": self.config['device_id'],
            "name": self.config['device_name'],
            "app_version": "1.0.0-simulator",
            "firmware_version": "PyQt6-Simulator"
        }
        
        try:
            print(f"📡 Registering device: {self.config['device_id']}")
            self.log_message.emit("INFO", "REGISTRATION", f"Attempting to register device: {self.config['device_id']}", "DeviceRegistration")
            
            response = self.session.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Device registered: {result['player']['name']}")
                self.log_message.emit("INFO", "REGISTRATION", f"Device registered successfully: {result['player']['name']}", "DeviceRegistration")
                return True
                
            elif response.status_code == 400 and "already exists" in response.text:
                print("ℹ️ Device already registered")
                self.log_message.emit("INFO", "REGISTRATION", "Device already registered", "DeviceRegistration")
                return True
                
            else:
                error_msg = f"Registration failed: HTTP {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                self.log_message.emit("ERROR", "REGISTRATION", error_msg, "DeviceRegistration")
                return False
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Registration network error: {e}"
            print(f"❌ {error_msg}")
            self.log_message.emit("ERROR", "NETWORK", error_msg, "DeviceRegistration")
            return False
            
    def test_connection(self):
        """Test connection to server"""
        try:
            url = f"{self.config['server_url']}/players/api/list/"
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                print("✅ Server connection test successful")
                self.log_message.emit("INFO", "NETWORK", "Server connection test successful", "NetworkTest")
                return True
            else:
                print(f"⚠️ Server responded with status: {response.status_code}")
                self.log_message.emit("WARN", "NETWORK", f"Server responded with status: {response.status_code}", "NetworkTest")
                return False
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Connection test failed: {e}"
            print(f"❌ {error_msg}")
            self.log_message.emit("ERROR", "NETWORK", error_msg, "NetworkTest")
            return False
            
    def update_config(self, new_config):
        """Update configuration"""
        self.config.update(new_config)
