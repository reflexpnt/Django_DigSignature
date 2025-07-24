#!/usr/bin/env python3
"""
Configuration module for PiSignage Device Simulator - Simplified Version
"""

# Device Presets - Different types of devices to simulate
DEVICE_PRESETS = { 
    "Android Tablet 10\" (1920x1080)": {
        "resolution": "1920x1080",
        "orientation": "landscape",
        "battery_level": 85,
        "temperature": 35,
        "storage_free_mb": 4096,
        "connection_type": "wifi",
        "signal_strength": -40,
        "device_name": "Samsung Galaxy Tab A 10.1",
        "description": "Standard Android tablet for digital signage"
    },
    
    "Android Phone (720p)": {
        "resolution": "1280x720",
        "orientation": "portrait",
        "battery_level": 65,
        "temperature": 40,
        "storage_free_mb": 1024,
        "connection_type": "mobile",
        "signal_strength": -65,
        "device_name": "Android Phone Portrait",
        "description": "Phone in portrait mode for vertical displays"
    },
    
    "Smart TV 4K": {
        "resolution": "3840x2160",
        "orientation": "landscape",
        "battery_level": 100,  # Always plugged in
        "temperature": 45,
        "storage_free_mb": 8192,
        "connection_type": "ethernet",
        "signal_strength": -30,
        "device_name": "Smart TV 65\" 4K",
        "description": "Large format display for lobbies/public areas"
    },
    
    "Raspberry Pi": {
        "resolution": "1920x1080",
        "orientation": "landscape",
        "battery_level": 100,  # Always plugged in
        "temperature": 55,  # Runs warmer
        "storage_free_mb": 512,  # Limited storage
        "connection_type": "ethernet",
        "signal_strength": -35,
        "device_name": "Raspberry Pi 4B",
        "description": "Original PiSignage hardware"
    }
}


class DeviceConfig:
    """Simple device configuration class"""
    
    def __init__(self):
        self.device_id = "A1B2C3D4E5F6G7BB"
        self.device_name = "PyQt6 Simulator"
        self.server_url = "http://localhost:8000"
        self.resolution = "1920x1080"
        self.sync_interval = 30
        self.battery_level = 85
        self.temperature = 38
        self.storage_free_mb = 2048
        self.connection_type = "wifi"
        self.signal_strength = -45
        self.offline_mode = False


def generate_device_id():
    """Generate a random 16-character hexadecimal device ID"""
    import random
    import string
    
    chars = string.digits + 'ABCDEF'
    return ''.join(random.choices(chars, k=16))
