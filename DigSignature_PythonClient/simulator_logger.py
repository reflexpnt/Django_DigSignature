#!/usr/bin/env python3
"""
Simulator Logger Module
Handles all logging operations and sending logs to server
"""

import json
import requests
from datetime import datetime, timezone
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class SimulatorLogger(QObject):
    """Handles logging operations for the simulator"""
    
    # Signals
    log_message = pyqtSignal(str, str, str)  # level, category, message
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.session = requests.Session()
        
        # Log queue
        self.log_queue = []
        self.max_queue_size = 50
        
        # Auto-flush timer
        self.flush_timer = QTimer()
        self.flush_timer.timeout.connect(self.flush_queue)
        
    def start(self):
        """Start the logger"""
        try:
            print("🔧 Starting logger...")
            # Start auto-flush timer (every 10 seconds)
            self.flush_timer.start(10000)
            
            # Queue and emit initial log
            self.queue_log("INFO", "LOGGER", "Logger started", "SimulatorLogger")
            print("   ✅ Logger started and timer active")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start logger: {e}")
            return False
            
    def stop(self):
        """Stop the logger and flush remaining logs"""
        try:
            self.flush_timer.stop()
            self.flush_queue()  # Send remaining logs
            self.queue_log("INFO", "LOGGER", "Logger stopped", "SimulatorLogger")
            
        except Exception as e:
            print(f"❌ Error stopping logger: {e}")
            
    def queue_log(self, level, category, message, tag="Simulator"):
        """Queue a log entry for sending and emit to UI"""
        # Print to console for debugging
        print(f"[{level}] {category}: {message}")
        
        # Always emit to UI immediately
        try:
            self.log_message.emit(level, category, message)
        except Exception as e:
            print(f"❌ Error emitting log signal: {e}")
        
        # Queue for server sending
        log_entry = {
            "timestamp": self.get_timestamp(),
            "level": level,
            "category": category,
            "tag": tag,
            "message": message,
            "thread_name": "MainThread",
            "method_name": "",
            "line_number": None,
            "extra_data": {}
        }
        
        self.log_queue.append(log_entry)
        
        # Auto-flush if queue is full
        if len(self.log_queue) >= self.max_queue_size:
            self.flush_queue()
            
    def flush_queue(self):
        """Send queued logs to server"""
        if not self.log_queue:
            return
            
        if self.config.get('offline_mode'):
            print(f"📴 Offline mode - {len(self.log_queue)} logs not sent")
            self.log_queue.clear()
            return
            
        # Copy and clear queue
        logs_to_send = self.log_queue.copy()
        self.log_queue.clear()
        
        # Send to server
        self.send_logs(logs_to_send, is_auto_flush=True)
        
    def send_logs(self, logs, is_auto_flush=False):
        """Send logs to server"""
        if self.config.get('offline_mode'):
            if not is_auto_flush:
                print("📴 Offline mode - not sending logs")
                self.queue_log("WARN", "NETWORK", "Offline mode - logs not sent to server", "LogSender")
            return
            
        url = f"{self.config['server_url']}/players/api/logs/batch/"
        data = {
            "device_id": self.config['device_id'],
            "app_version": "1.0.0-simulator",
            "logs": logs,
            "device_context": {
                "battery_level": self.config.get('battery_level', 85),
                "memory_available_mb": 1024,
                "storage_free_mb": self.config.get('storage_free_mb', 2048),
                "temperature_celsius": self.config.get('temperature', 38)
            }
        }
        
        try:
            response = self.session.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                created_logs = result.get('created_logs', 0)
                
                if is_auto_flush:
                    print(f"🔄 Auto-flushed {created_logs} logs to server")
                else:
                    print(f"📝 Sent {created_logs} logs to server")
                    # Don't emit a log about sending logs to avoid recursion
                    
            else:
                error_msg = f"Failed to send logs: HTTP {response.status_code}"
                print(f"⚠️ {error_msg}")
                if not is_auto_flush:
                    # Don't queue logs about log sending failures to avoid recursion
                    print(f"   Response: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error sending logs: {e}"
            print(f"❌ {error_msg}")
            # Don't queue network errors about log sending to avoid recursion
                
    def get_timestamp(self):
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()
        
    def get_queue_size(self):
        """Get current queue size"""
        return len(self.log_queue)
        
    def update_config(self, new_config):
        """Update configuration"""
        old_offline = self.config.get('offline_mode', False)
        self.config.update(new_config)
        new_offline = new_config.get('offline_mode', False)
        
        if old_offline != new_offline:
            if new_offline:
                self.queue_log("INFO", "CONFIG", "Offline mode enabled", "ConfigManager")
            else:
                self.queue_log("INFO", "CONFIG", "Offline mode disabled", "ConfigManager")
