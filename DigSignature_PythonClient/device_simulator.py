#!/usr/bin/env python3
"""
Device Simulator Core - Modular Version
Main orchestrator for the device simulation
"""

import json
import os
from pathlib import Path
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from simulator_logger import SimulatorLogger
from simulator_network import NetworkManager
from simulator_sync import SyncManager
from simulator_assets import AssetManager


class DeviceSimulator(QObject):
    """Main device simulator coordinator"""
    
    # Signals
    log_message = pyqtSignal(str, str, str)  # level, category, message
    status_changed = pyqtSignal(str)
    media_file_received = pyqtSignal(str)  # file_path
    sync_completed = pyqtSignal(dict)  # sync_data
    error_occurred = pyqtSignal(str, str)  # error_type, message
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.is_running = False
        
        # Initialize components
        print("🔧 Initializing simulator components...")
        self.logger = SimulatorLogger(config)
        self.network = NetworkManager(config)
        self.sync_manager = SyncManager(config)
        self.asset_manager = AssetManager(config)
        print("   ✅ Components initialized")
        
        # Connect internal signals
        self._connect_signals()
        
        # Setup timers
        self._setup_timers()
        
        # Create local directories
        self._setup_directories()
        
    def _connect_signals(self):
        """Connect signals between components"""
        print("🔌 Connecting internal signals...")
        
        # Logger signals - Direct connection for UI display
        self.logger.log_message.connect(self.log_message.emit)
        print("   ✅ Logger signals connected")
        
        # Network signals - Connect to logger's queue_log method
        self.network.log_message.connect(
            lambda level, cat, msg, tag: self.logger.queue_log(level, cat, msg, tag)
        )
        print("   ✅ Network signals connected")
        
        # Sync signals
        self.sync_manager.log_message.connect(
            lambda level, cat, msg, tag: self.logger.queue_log(level, cat, msg, tag)
        )
        self.sync_manager.sync_completed.connect(self._on_sync_completed)
        print("   ✅ Sync signals connected")
        
        # Asset signals
        self.asset_manager.log_message.connect(
            lambda level, cat, msg, tag: self.logger.queue_log(level, cat, msg, tag)
        )
        self.asset_manager.media_ready.connect(self.media_file_received.emit)
        print("   ✅ Asset signals connected")
        
    def _setup_timers(self):
        """Setup periodic timers"""
        # Main sync timer
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self._periodic_sync)
        
        # Health monitoring timer
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self._send_health_logs)
        
    def _setup_directories(self):
        """Create local directories"""
        try:
            device_id = self.config['device_id']
            self.local_dir = Path(f"simulator_assets_{device_id}")
            self.local_dir.mkdir(exist_ok=True)
            
            print(f"INFO: Local directory created: {self.local_dir}")
            
        except Exception as e:
            print(f"ERROR: Failed to create directories: {e}")
        
    def start(self):
        """Start device simulation"""
        try:
            print("🚀 Starting device simulation...")
            print(f"   Device ID: {self.config['device_id']}")
            print(f"   Server URL: {self.config['server_url']}")
            
            # Start logger first
            print("   Starting logger...")
            if not self.logger.start():
                print("❌ Failed to start logger")
                return False
            print("   ✅ Logger started")
            
            # Log startup
            self.logger.queue_log("INFO", "SYSTEM", "Device simulation starting...", "SimulatorCore")
            
            # Register device
            print("   Registering device...")
            if not self.network.register_device():
                print("❌ Failed to register device")
                self.logger.queue_log("ERROR", "SYSTEM", "Failed to register device", "SimulatorCore")
                return False
            print("   ✅ Device registered")
                
            # Start periodic operations
            sync_interval = self.config.get('sync_interval', 30) * 1000
            self.sync_timer.start(sync_interval)
            self.health_timer.start(60000)  # Health every 60s
            
            self.is_running = True
            self.status_changed.emit("Running")
            
            # Log successful startup
            self.logger.queue_log("INFO", "SYSTEM", 
                f"Device simulation started successfully - ID: {self.config['device_id']}, Sync interval: {self.config.get('sync_interval', 30)}s", 
                "SimulatorCore")
            
            # Initial sync after a short delay
            QTimer.singleShot(1000, self._periodic_sync)
            
            print("✅ Device simulation started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start simulator: {e}")
            self.logger.queue_log("ERROR", "SYSTEM", f"Failed to start simulator: {e}", "SimulatorCore")
            return False
            
    def stop(self):
        """Stop device simulation"""
        try:
            print("🛑 Stopping device simulation...")
            
            # Stop timers
            self.sync_timer.stop()
            self.health_timer.stop()
            
            # Log shutdown
            self.logger.queue_log("INFO", "SYSTEM", "Device simulation stopping...", "SimulatorCore")
            
            # Stop components
            self.logger.stop()
            
            self.is_running = False
            self.status_changed.emit("Stopped")
            
            print("✅ Device simulation stopped")
            
        except Exception as e:
            print(f"❌ Error stopping simulator: {e}")
            
    def _periodic_sync(self):
        """Perform periodic sync check"""
        if not self.is_running:
            return
            
        try:
            # Get current health data
            health_data = self._get_current_health()
            
            # Log sync attempt
            self.logger.queue_log("DEBUG", "SYNC", "Starting periodic sync check", "SyncManager")
            
            # Check server for updates
            sync_result = self.sync_manager.check_server(health_data)
            
            if sync_result.get('needs_sync'):
                sync_data = sync_result.get('sync_data')
                if sync_data:
                    self._process_sync_data(sync_data)
                    
        except Exception as e:
            self.logger.queue_log("ERROR", "SYNC", f"Periodic sync error: {e}", "SyncManager")
            
    def _process_sync_data(self, sync_data):
        """Process received sync data"""
        try:
            # Process assets
            assets = sync_data.get('assets', [])
            if assets:
                self.asset_manager.download_assets(assets, self.local_dir)
                
            # Emit completion signal
            self.sync_completed.emit(sync_data)
            
        except Exception as e:
            self.logger.queue_log("ERROR", "SYNC", f"Error processing sync data: {e}", "SyncProcessor")
            
    def _on_sync_completed(self, sync_data):
        """Handle sync completion"""
        # Send confirmation to server
        self.sync_manager.send_confirmation(sync_data)
        
    def _send_health_logs(self):
        """Send periodic health logs"""
        if not self.is_running:
            return
            
        health_data = self._get_current_health()
        
        health_log = {
            "timestamp": self.logger.get_timestamp(),
            "level": "INFO",
            "category": "SYSTEM",
            "tag": "HealthMonitor",
            "message": f"Device health: Battery {health_data['battery']}%, Temp {health_data['temperature']}°C, Storage {health_data['storage']}MB",
            "extra_data": health_data
        }
        
        self.logger.send_logs([health_log])
        
    def _get_current_health(self):
        """Get current device health data"""
        return {
            "battery": self.config.get('battery_level', 85),
            "temperature": self.config.get('temperature', 38),
            "storage": self.config.get('storage_free_mb', 2048),
            "connection": self.config.get('connection_type', 'wifi'),
            "signal": self.config.get('signal_strength', -45)
        }
        
    def update_config(self, new_config):
        """Update configuration and apply changes"""
        old_sync_interval = self.config.get('sync_interval', 30)
        old_offline_mode = self.config.get('offline_mode', False)
        
        self.config.update(new_config)
        
        # Update sync interval if changed
        new_sync_interval = self.config.get('sync_interval', 30)
        if self.is_running and old_sync_interval != new_sync_interval:
            new_interval_ms = new_sync_interval * 1000
            self.sync_timer.setInterval(new_interval_ms)
            self.logger.queue_log("INFO", "CONFIG", f"Sync interval updated: {old_sync_interval}s → {new_sync_interval}s", "ConfigManager")
            print(f"🔄 Sync interval updated: {old_sync_interval}s → {new_sync_interval}s")
        
        # Log offline mode changes
        new_offline_mode = self.config.get('offline_mode', False)
        if old_offline_mode != new_offline_mode:
            if new_offline_mode:
                self.logger.queue_log("INFO", "CONFIG", "Offline mode enabled - sync and log sending disabled", "ConfigManager")
            else:
                self.logger.queue_log("INFO", "CONFIG", "Offline mode disabled - sync and log sending enabled", "ConfigManager")
        
        # Update components
        self.logger.update_config(new_config)
        self.network.update_config(new_config)
        self.sync_manager.update_config(new_config)
        self.asset_manager.update_config(new_config)
        
    def force_sync(self):
        """Force immediate sync"""
        print("🔄 Forcing sync check...")
        self.logger.queue_log("INFO", "SYNC", "Manual sync triggered by user", "UserAction")
        self._periodic_sync()
        
    def send_test_logs(self):
        """Send test logs to server"""
        self.logger.queue_log("INFO", "TEST", "Sending test logs to server", "UserAction")
        
        test_logs = [
            {
                "timestamp": self.logger.get_timestamp(),
                "level": "INFO",
                "category": "APP",
                "tag": "TestRunner",
                "message": "Manual test log from simulator - user triggered"
            },
            {
                "timestamp": self.logger.get_timestamp(),
                "level": "DEBUG",
                "category": "NETWORK",
                "tag": "ConnectivityTest",
                "message": f"Network test - Connection: {self.config.get('connection_type', 'wifi')}, Signal: {self.config.get('signal_strength', -45)}dBm"
            },
            {
                "timestamp": self.logger.get_timestamp(),
                "level": "WARN",
                "category": "SYSTEM",
                "tag": "TestRunner",
                "message": f"Test warning - Battery: {self.config.get('battery_level', 85)}%, Temperature: {self.config.get('temperature', 38)}°C"
            }
        ]
        
        self.logger.send_logs(test_logs)
        self.logger.queue_log("INFO", "TEST", f"Sent {len(test_logs)} test logs to server", "TestRunner")
        
    def get_status_info(self):
        """Get current status information"""
        return {
            'device_id': self.config['device_id'],
            'is_running': self.is_running,
            'sync_interval': self.config.get('sync_interval', 30),
            'health': self._get_current_health(),
            'log_queue_size': self.logger.get_queue_size(),
            'assets_count': self.asset_manager.get_asset_count(),
            'offline_mode': self.config.get('offline_mode', False)
        }
