#!/usr/bin/env python3
"""
Simple launcher for PiSignage Device Simulator
"""

import sys
import os
from pathlib import Path

def main():
    print("🚀 PiSignage Device Simulator")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ main.py not found in current directory")
        print("   Please run this script from the simulator directory")
        return
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required, you have {sys.version}")
        return
    
    print(f"✅ Python {sys.version.split()[0]}")
    
    # Try to import PyQt6
    try:
        from PyQt6.QtWidgets import QApplication
        print("✅ PyQt6 is available")
    except ImportError:
        print("❌ PyQt6 not installed")
        print("   Install with: pip install PyQt6")
        return
    
    # Try to import requests
    try:
        import requests
        print("✅ requests is available")
    except ImportError:
        print("❌ requests not installed")
        print("   Install with: pip install requests")
        return
    
    print("\n🎮 Starting simulator...")
    
    # Create necessary files if they don't exist
    create_missing_files()
    
    # Import and run main
    try:
        from main import main as run_main
        run_main()
    except Exception as e:
        print(f"❌ Error running simulator: {e}")
        import traceback
        traceback.print_exc()

def create_missing_files():
    """Create missing files with minimal content"""
    
    # Create device_simulator.py if missing
    if not Path("device_simulator.py").exists():
        print("📝 Creating device_simulator.py...")
        with open("device_simulator.py", "w") as f:
            f.write('''# This file was auto-generated
# Replace with the full device_simulator.py content from the artifacts
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import requests
from datetime import datetime, timezone
from pathlib import Path

class DeviceSimulator(QObject):
    log_message = pyqtSignal(str, str, str)
    status_changed = pyqtSignal(str)
    media_file_received = pyqtSignal(str)
    sync_completed = pyqtSignal(dict)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.is_running = False
        
    def start(self):
        print("Simulator started (minimal version)")
        self.status_changed.emit("Running")
        return True
        
    def stop(self):
        self.is_running = False
        self.status_changed.emit("Stopped")
        
    def force_sync(self):
        print("Force sync requested")
        
    def send_test_logs(self):
        print("Test logs sent")
''')
    
    # Create config.py if missing
    if not Path("config.py").exists():
        print("📝 Creating config.py...")
        with open("config.py", "w") as f:
            f.write('''# This file was auto-generated
DEVICE_PRESETS = {
    "Default Tablet": {
        "resolution": "1920x1080",
        "description": "Default configuration"
    }
}

class DeviceConfig:
    def __init__(self):
        self.device_id = "A1B2C3D4E5F6G7H8"
        self.device_name = "PyQt6 Simulator"
        self.server_url = "http://localhost:8000"

def generate_device_id():
    import random
    import string
    chars = string.digits + 'ABCDEF'
    return ''.join(random.choices(chars, k=16))
''')

if __name__ == "__main__":
    main()