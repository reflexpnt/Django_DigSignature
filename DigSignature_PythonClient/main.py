#!/usr/bin/env python3
"""
PiSignage Device Simulator - Main Application
PyQt6-based simulator with dynamic zone system
"""

import sys
import os
import json
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QComboBox, QSpinBox,
                             QLineEdit, QTextEdit, QGroupBox, QCheckBox, QSlider,
                             QStatusBar, QMenuBar, QMenu, QDialog, QFormLayout,
                             QDialogButtonBox, QProgressBar, QTabWidget, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QUrl
from PyQt6.QtGui import QFont, QPixmap, QIcon, QAction
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

# Import our modules with error handling
try:
    from device_simulator import DeviceSimulator
except ImportError as e:
    print(f"Error importing device_simulator: {e}")
    sys.exit(1)

try:
    from media_player import DynamicMediaPlayerWidget
    print("✅ Dynamic MediaPlayerWidget imported successfully")
except ImportError as e:
    print(f"⚠️ Error importing dynamic media_player: {e}")
    # Create fallback class
    class DynamicMediaPlayerWidget(QWidget):
        layout_changed = pyqtSignal(str)
        zones_created = pyqtSignal(list)
        
        def __init__(self):
            super().__init__()
            self.setStyleSheet("background-color: black; color: white;")
            layout = QVBoxLayout(self)
            label = QLabel("Dynamic MediaPlayerWidget not available\nCheck media_player.py file")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        
        def create_layout(self, layout_code):
            print(f"Fallback: Would create layout {layout_code}")
            self.layout_changed.emit(layout_code)
            self.zones_created.emit([])
        
        def load_playlist(self, playlist_data):
            print(f"Fallback: Would load playlist {playlist_data.get('name', 'Unknown')}")
            
        def stop_playlist(self):
            print("Fallback: Would stop playlist")
            
        def get_playback_status(self):
            return {'layout': 'fallback', 'playlist_name': 'None', 'zones_active': 0, 'zones': []}

try:
    from config import DeviceConfig, DEVICE_PRESETS, generate_device_id
except ImportError as e:
    print(f"Error importing config: {e}")
    # Create minimal fallback
    class DeviceConfig:
        def __init__(self):
            self.device_id = "A1B2C3D4E5F6G7H8"
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
    
    DEVICE_PRESETS = {
        "Default Tablet": {
            "resolution": "1920x1080",
            "description": "Default configuration"
        }
    }
    
    def generate_device_id():
        import random
        import string
        chars = string.digits + 'ABCDEF'
        return ''.join(random.choices(chars, k=16))


class SimulatorControlPanel(QWidget):
    """Panel de control del simulador"""
    
    # Signals
    start_simulation = pyqtSignal()
    stop_simulation = pyqtSignal()
    sync_now = pyqtSignal()
    send_logs = pyqtSignal()
    go_fullscreen = pyqtSignal()
    config_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.device_simulator = None  # Initialize reference
        
        # Create default config
        self.default_config = DeviceConfig()
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Device Configuration
        device_group = QGroupBox("Device Configuration")
        device_layout = QFormLayout(device_group)
        
        # Device preset selector
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(DEVICE_PRESETS.keys()))
        self.preset_combo.currentTextChanged.connect(self.load_preset)
        device_layout.addRow("Preset:", self.preset_combo)
        
        # Device ID - Read from config
        device_id_layout = QHBoxLayout()
        self.device_id_input = QLineEdit(self.default_config.device_id)
        self.device_id_input.setMaxLength(16)
        device_id_layout.addWidget(self.device_id_input)
        
        # Button to generate new device ID
        generate_id_btn = QPushButton("🎲")
        generate_id_btn.setToolTip("Generate new random Device ID")
        generate_id_btn.setMaximumWidth(30)
        generate_id_btn.clicked.connect(self.generate_new_device_id)
        device_id_layout.addWidget(generate_id_btn)
        
        device_layout.addRow("Device ID:", device_id_layout)
        
        # Device Name - Read from config
        self.device_name_input = QLineEdit(self.default_config.device_name)
        device_layout.addRow("Device Name:", self.device_name_input)
        
        # Screen Resolution - Read from config
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1920x1080", "1280x720", "1024x768", "800x600", "3840x2160"])
        self.resolution_combo.setCurrentText(self.default_config.resolution)
        device_layout.addRow("Resolution:", self.resolution_combo)
        
        layout.addWidget(device_group)
        
        # Server Configuration
        server_group = QGroupBox("Server Configuration")
        server_layout = QFormLayout(server_group)
        
        # Server URL - Read from config
        self.server_url_input = QLineEdit(self.default_config.server_url)
        server_layout.addRow("Server URL:", self.server_url_input)
        
        # Sync interval spin box with immediate update - Read from config
        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setRange(10, 3600)
        self.sync_interval_spin.setValue(self.default_config.sync_interval)
        self.sync_interval_spin.setSuffix(" seconds")
        self.sync_interval_spin.valueChanged.connect(self.on_sync_interval_changed)
        server_layout.addRow("Sync Interval:", self.sync_interval_spin)
        
        layout.addWidget(server_group)
        
        # Simulation Controls
        controls_group = QGroupBox("Simulation Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶ Start Simulation")
        self.start_btn.clicked.connect(self.start_simulation.emit)
        self.start_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; font-weight: bold; }")
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹ Stop Simulation")
        self.stop_btn.clicked.connect(self.stop_simulation.emit)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; font-weight: bold; }")
        button_layout.addWidget(self.stop_btn)
        
        controls_layout.addLayout(button_layout)
        
        # Manual actions
        manual_layout = QHBoxLayout()
        
        sync_btn = QPushButton("🔄 Sync Now")
        sync_btn.clicked.connect(self.sync_now.emit)
        manual_layout.addWidget(sync_btn)
        
        logs_btn = QPushButton("📝 Send Logs")
        logs_btn.clicked.connect(self.send_logs.emit)
        manual_layout.addWidget(logs_btn)
        
        # New button to open server logs
        server_logs_btn = QPushButton("🌐 Server Logs")
        server_logs_btn.clicked.connect(self.open_server_logs)
        server_logs_btn.setToolTip("Open device logs in web browser")
        manual_layout.addWidget(server_logs_btn)
        
        fullscreen_btn = QPushButton("🖥️ Fullscreen")
        fullscreen_btn.clicked.connect(self.go_fullscreen.emit)
        manual_layout.addWidget(fullscreen_btn)
        
        controls_layout.addLayout(manual_layout)
        
        layout.addWidget(controls_group)
        
        # Device Health Simulation
        health_group = QGroupBox("Device Health Simulation")
        health_layout = QFormLayout(health_group)
        
        # Health sliders with immediate update - Read from config
        self.battery_slider = QSlider(Qt.Orientation.Horizontal)
        self.battery_slider.setRange(0, 100)
        self.battery_slider.setValue(self.default_config.battery_level)
        self.battery_label = QLabel(f"{self.default_config.battery_level}%")
        battery_layout = QHBoxLayout()
        battery_layout.addWidget(self.battery_slider)
        battery_layout.addWidget(self.battery_label)
        self.battery_slider.valueChanged.connect(self.on_battery_changed)
        health_layout.addRow("Battery:", battery_layout)
        
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(20, 80)
        self.temperature_slider.setValue(self.default_config.temperature)
        self.temp_label = QLabel(f"{self.default_config.temperature}°C")
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temp_label)
        self.temperature_slider.valueChanged.connect(self.on_temperature_changed)
        health_layout.addRow("Temperature:", temp_layout)
        
        self.storage_spin = QSpinBox()
        self.storage_spin.setRange(100, 32000)
        self.storage_spin.setValue(self.default_config.storage_free_mb)
        self.storage_spin.setSuffix(" MB")
        self.storage_spin.valueChanged.connect(self.on_storage_changed)
        health_layout.addRow("Free Storage:", self.storage_spin)
        
        layout.addWidget(health_group)
        
        # Network Simulation
        network_group = QGroupBox("Network Simulation")
        network_layout = QFormLayout(network_group)
        
        self.connection_combo = QComboBox()
        self.connection_combo.addItems(["wifi", "mobile", "ethernet"])
        self.connection_combo.setCurrentText(self.default_config.connection_type)
        network_layout.addRow("Connection:", self.connection_combo)
        
        self.signal_slider = QSlider(Qt.Orientation.Horizontal)
        self.signal_slider.setRange(-120, -30)
        self.signal_slider.setValue(self.default_config.signal_strength)
        self.signal_label = QLabel(f"{self.default_config.signal_strength} dBm")
        signal_layout = QHBoxLayout()
        signal_layout.addWidget(self.signal_slider)
        signal_layout.addWidget(self.signal_label)
        self.signal_slider.valueChanged.connect(self.on_signal_changed)
        network_layout.addRow("Signal Strength:", signal_layout)
        
        self.offline_checkbox = QCheckBox("Simulate Offline Mode")
        self.offline_checkbox.setChecked(self.default_config.offline_mode)
        self.offline_checkbox.stateChanged.connect(self.on_offline_mode_changed)
        network_layout.addRow("", self.offline_checkbox)
        
        layout.addWidget(network_group)
        
        layout.addStretch()
    
    def set_device_simulator(self, device_simulator):
        """Set device simulator reference for config updates"""
        self.device_simulator = device_simulator
        
    def on_sync_interval_changed(self, value):
        """Handle sync interval change"""
        if self.device_simulator:
            config = self.get_config()
            self.device_simulator.update_config(config)
            
    def on_battery_changed(self, value):
        """Handle battery level change"""
        self.battery_label.setText(f"{value}%")
        if self.device_simulator:
            config = self.get_config()
            self.device_simulator.update_config(config)
            
    def on_temperature_changed(self, value):
        """Handle temperature change"""
        self.temp_label.setText(f"{value}°C")
        if self.device_simulator:
            config = self.get_config()
            self.device_simulator.update_config(config)
            
    def on_storage_changed(self, value):
        """Handle storage change"""
        if self.device_simulator:
            config = self.get_config()
            self.device_simulator.update_config(config)
            
    def on_signal_changed(self, value):
        """Handle signal strength change"""
        self.signal_label.setText(f"{value} dBm")
        if self.device_simulator:
            config = self.get_config()
            self.device_simulator.update_config(config)
            
    def on_offline_mode_changed(self, state):
        """Handle offline mode checkbox change"""
        if self.device_simulator:
            config = self.get_config()
            self.device_simulator.update_config(config)
            
    def open_server_logs(self):
        """Open server logs in web browser"""
        device_id = self.device_id_input.text()
        server_url = self.server_url_input.text().rstrip('/')
        logs_url = f"{server_url}/players/{device_id}/logs/"
        
        try:
            import webbrowser
            webbrowser.open(logs_url)
            print(f"Opening server logs: {logs_url}")
        except Exception as e:
            print(f"Failed to open browser: {e}")
            # Show the URL in a message box as fallback
            QMessageBox.information(
                self, 
                "Server Logs URL", 
                f"Open this URL in your browser:\n\n{logs_url}"
            )
    
    def generate_new_device_id(self):
        """Generate and set a new random device ID"""
        new_id = generate_device_id()
        self.device_id_input.setText(new_id)
        print(f"Generated new device ID: {new_id}")
            
    def load_preset(self, preset_name):
        """Load device preset configuration"""
        if preset_name in DEVICE_PRESETS:
            preset = DEVICE_PRESETS[preset_name]
            
            # Update resolution
            self.resolution_combo.setCurrentText(preset['resolution'])
            
            # Update device name if it has one
            if 'device_name' in preset:
                self.device_name_input.setText(preset['device_name'])
            
            # Update health values
            if 'battery_level' in preset:
                self.battery_slider.setValue(preset['battery_level'])
                
            if 'temperature' in preset:
                self.temperature_slider.setValue(preset['temperature'])
                
            if 'storage_free_mb' in preset:
                self.storage_spin.setValue(preset['storage_free_mb'])
            
            # Update network values
            if 'connection_type' in preset:
                self.connection_combo.setCurrentText(preset['connection_type'])
                
            if 'signal_strength' in preset:
                self.signal_slider.setValue(preset['signal_strength'])
                
            # Update orientation if present (for future use)
            if 'orientation' in preset:
                # Could add orientation combo box later
                pass
        
    def get_config(self):
        """Get current configuration"""
        return {
            'device_id': self.device_id_input.text(),
            'device_name': self.device_name_input.text(),
            'server_url': self.server_url_input.text(),
            'resolution': self.resolution_combo.currentText(),
            'sync_interval': self.sync_interval_spin.value(),
            'battery_level': self.battery_slider.value(),
            'temperature': self.temperature_slider.value(),
            'storage_free_mb': self.storage_spin.value(),
            'connection_type': self.connection_combo.currentText(),
            'signal_strength': self.signal_slider.value(),
            'offline_mode': self.offline_checkbox.isChecked()
        }
        
    def set_simulation_running(self, running):
        """Update UI based on simulation state"""
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)


class LogDisplayWidget(QWidget):
    """Widget for displaying device logs"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Log controls
        controls_layout = QHBoxLayout()
        
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_logs)
        controls_layout.addWidget(clear_btn)
        
        controls_layout.addStretch()
        
        auto_scroll_cb = QCheckBox("Auto-scroll")
        auto_scroll_cb.setChecked(True)
        self.auto_scroll = auto_scroll_cb
        controls_layout.addWidget(auto_scroll_cb)
        
        layout.addLayout(controls_layout)
        
        # Log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit { 
                background-color: #1e1e1e; 
                color: #ffffff; 
                border: 1px solid #555;
            }
        """)
        layout.addWidget(self.log_text)
        
    def add_log(self, level, category, message):
        """Add log entry with color coding"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Color coding based on level
        colors = {
            'VERBOSE': '#6c757d',
            'DEBUG': '#17a2b8', 
            'INFO': '#28a745',
            'WARN': '#ffc107',
            'ERROR': '#dc3545',
            'FATAL': '#6f42c1'
        }
        
        color = colors.get(level, '#ffffff')
        
        # Format log entry
        html = f'<span style="color: #888">{timestamp}</span> '
        html += f'<span style="color: {color}; font-weight: bold">[{level}]</span> '
        html += f'<span style="color: #17a2b8">{category}</span>: '
        html += f'<span style="color: white">{message}</span><br>'
        
        self.log_text.insertHtml(html)
        
        # Auto-scroll to bottom
        if self.auto_scroll.isChecked():
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    def clear_logs(self):
        """Clear all logs"""
        self.log_text.clear()


class PiSignageSimulatorMainWindow(QMainWindow):
    """Main window for PiSignage device simulator with dynamic zones"""
    
    def __init__(self):
        super().__init__()
        self.device_simulator = None
        self.fullscreen_window = None
        self.downloaded_assets = {}  # Store downloaded asset paths
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        self.setWindowTitle("PiSignage Device Simulator - Dynamic Zone System")
        self.setMinimumSize(1200, 800)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main widget with tabs
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QHBoxLayout(main_widget)
        
        # Left side - Control panel
        self.control_panel = SimulatorControlPanel()
        self.control_panel.setMaximumWidth(350)
        layout.addWidget(self.control_panel)
        
        # Right side - Tabs
        tab_widget = QTabWidget()
        
        # Media display tab - Use Dynamic MediaPlayerWidget
        self.media_player = DynamicMediaPlayerWidget()
        tab_widget.addTab(self.media_player, "📺 Dynamic Media Display")
        
        # Logs tab
        self.log_display = LogDisplayWidget()
        tab_widget.addTab(self.log_display, "📝 Device Logs")
        
        layout.addWidget(tab_widget, 1)
        
        # Status bar with additional info
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Dynamic Zone System")
        
        # Add permanent widget to status bar for layout info
        self.layout_info = QLabel("Layout: None | Zones: 0")
        self.layout_info.setStyleSheet("color: #666; padding: 2px 8px;")
        self.status_bar.addPermanentWidget(self.layout_info)
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_window_action = QAction('New Simulator Window', self)
        new_window_action.triggered.connect(self.create_new_window)
        file_menu.addAction(new_window_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        test_layout_menu = view_menu.addMenu('Test Layouts')
        
        layouts = ['1', '2a', '2b', '3a', '3b', '4', '4b', '2ab']
        for layout in layouts:
            action = QAction(f'Layout {layout}', self)
            action.triggered.connect(lambda checked, l=layout: self.test_layout(l))
            test_layout_menu.addAction(action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        config_action = QAction('Device Configuration', self)
        tools_menu.addAction(config_action)
        
        clear_assets_action = QAction('Clear Downloaded Assets', self)
        clear_assets_action.triggered.connect(self.clear_downloaded_assets)
        tools_menu.addAction(clear_assets_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_connections(self):
        """Setup signal connections"""
        self.control_panel.start_simulation.connect(self.start_simulation)
        self.control_panel.stop_simulation.connect(self.stop_simulation)
        self.control_panel.sync_now.connect(self.sync_now)
        self.control_panel.send_logs.connect(self.send_test_logs)
        self.control_panel.go_fullscreen.connect(self.toggle_fullscreen)
        
        # Connect media player signals
        self.media_player.layout_changed.connect(self.on_layout_changed)
        self.media_player.zones_created.connect(self.on_zones_created)
        
    def test_layout(self, layout_code):
        """Test layout without server data"""
        print(f"🧪 Testing layout: {layout_code}")
        self.media_player.create_layout(layout_code)
        self.log_display.add_log("INFO", "UI", f"Testing layout: {layout_code}")
        
    def on_layout_changed(self, layout_code):
        """Handle layout change signal"""
        status = self.media_player.get_playback_status()
        self.layout_info.setText(f"Layout: {layout_code} | Zones: {status['zones_active']}")
        
    def on_zones_created(self, zone_names):
        """Handle zones created signal"""
        self.log_display.add_log("INFO", "LAYOUT", f"Created zones: {', '.join(zone_names)}")
        
    def clear_downloaded_assets(self):
        """Clear downloaded assets cache"""
        self.downloaded_assets.clear()
        self.log_display.add_log("INFO", "UI", "Downloaded assets cache cleared")
        
    def start_simulation(self):
        """Start device simulation"""
        config = self.control_panel.get_config()
        
        try:
            print("🚀 Creating DeviceSimulator instance...")
            self.device_simulator = DeviceSimulator(config)
            
            # Set simulator reference in control panel for config updates
            self.control_panel.set_device_simulator(self.device_simulator)
            
            # Connect signals after object is created
            print("🔌 Connecting UI signals...")
            self.device_simulator.log_message.connect(self.log_display.add_log)
            self.device_simulator.media_file_received.connect(self.on_media_file_received)
            self.device_simulator.sync_completed.connect(self.on_sync_completed)
            self.device_simulator.status_changed.connect(self.update_status)
            print("   ✅ UI signals connected")
            
            print("▶️ Starting device simulator...")
            if self.device_simulator.start():
                self.control_panel.set_simulation_running(True)
                self.status_bar.showMessage("Simulation running...")
                self.log_display.add_log("INFO", "SIMULATOR", "Device simulation started with dynamic zone system")
                print("✅ Simulation started successfully!")
            else:
                self.status_bar.showMessage("Failed to start simulation")
                print("❌ Failed to start simulation")
                
        except Exception as e:
            error_msg = f"Error starting simulation: {e}"
            self.status_bar.showMessage(error_msg)
            self.log_display.add_log("ERROR", "SIMULATOR", f"Failed to start: {e}")
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            
    def on_media_file_received(self, file_path):
        """Handle when a media file is downloaded and ready to play"""
        print(f"📺 Main window received media file signal: {file_path}")
        
        # Store the downloaded asset path for later use
        asset_name = os.path.basename(file_path)
        self.downloaded_assets[asset_name] = file_path
        
        self.log_display.add_log("INFO", "MEDIA", f"Asset downloaded: {asset_name}")
        
    def on_sync_completed(self, sync_data):
        """Handle when sync is completed"""
        playlists = sync_data.get('playlists', [])
        assets = sync_data.get('assets', [])
        
        self.log_display.add_log("INFO", "SYNC", f"Sync completed: {len(playlists)} playlists, {len(assets)} assets")
        
        # Process the playlist with dynamic zone system
        if playlists:
            playlist = playlists[0]  # Use first playlist
            self.process_playlist_dynamic(playlist, assets)
            
    def process_playlist_dynamic(self, playlist, assets):
        """Process playlist and setup dynamic zone playback"""
        playlist_name = playlist.get('name', 'Unknown')
        layout_code = playlist.get('layout', '1')
        items = playlist.get('items', [])
        
        self.log_display.add_log("INFO", "LAYOUT", f"Processing playlist '{playlist_name}' with layout '{layout_code}'")
        
        # Create complete playlist data for Dynamic MediaPlayerWidget
        playlist_data = {
            'name': playlist_name,
            'layout': layout_code,
            'ticker': playlist.get('ticker', {}),
            'items': []
        }
        
        # Process each playlist item
        items_processed = 0
        for item in items:
            asset_id = item.get('asset_id')
            
            # Find the corresponding asset
            asset = None
            for a in assets:
                if str(a['id']) == str(asset_id):
                    asset = a
                    break
            
            if asset:
                asset_name = asset['name']
                
                # Find the downloaded file path
                file_path = None
                for downloaded_name, downloaded_path in self.downloaded_assets.items():
                    # More flexible matching
                    if (asset_name in downloaded_name or 
                        downloaded_name.startswith(asset_name) or
                        asset_name.startswith(downloaded_name.split('.')[0])):
                        file_path = downloaded_path
                        break
                
                if file_path and os.path.exists(file_path):
                    # Create item data for Dynamic MediaPlayerWidget
                    item_data = {
                        'asset_id': asset_id,
                        'asset_type': asset.get('type', 'video'),
                        'file_path': file_path,
                        'duration': item.get('duration', 10),
                        'zone': item.get('zone', 'main'),
                        'order': item.get('order', 0)
                    }
                    
                    playlist_data['items'].append(item_data)
                    items_processed += 1
                    
                    self.log_display.add_log("INFO", "LAYOUT", 
                        f"Added to {item.get('zone', 'main')} zone: {asset_name} ({asset.get('type', 'unknown')})")
                else:
                    self.log_display.add_log("WARN", "LAYOUT", f"File not found for asset: {asset_name}")
            else:
                self.log_display.add_log("WARN", "LAYOUT", f"Asset not found for item: {asset_id}")
        
        # Load the playlist into Dynamic MediaPlayerWidget
        if playlist_data['items']:
            print(f"🎬 Loading playlist with {len(playlist_data['items'])} items into Dynamic MediaPlayerWidget")
            self.media_player.load_playlist(playlist_data)
            
            self.log_display.add_log("INFO", "LAYOUT", 
                f"Loaded playlist with {len(playlist_data['items'])} items in layout '{layout_code}'")
        else:
            self.log_display.add_log("WARN", "LAYOUT", "No valid items found in playlist")
            
    def stop_simulation(self):
        """Stop device simulation"""
        if self.device_simulator:
            self.device_simulator.stop()
            self.device_simulator = None
            
        # Clear reference in control panel
        self.control_panel.set_device_simulator(None)
        
        # Stop media playback
        if hasattr(self.media_player, 'stop_playlist'):
            self.media_player.stop_playlist()
        
        # Clear downloaded assets
        self.downloaded_assets.clear()
            
        self.control_panel.set_simulation_running(False)
        self.status_bar.showMessage("Simulation stopped")
        self.layout_info.setText("Layout: None | Zones: 0")
        self.log_display.add_log("INFO", "SIMULATOR", "Device simulation stopped")
        
    def sync_now(self):
        """Trigger manual sync"""
        if self.device_simulator:
            self.device_simulator.force_sync()
            # Add visual feedback in logs
            self.log_display.add_log("INFO", "UI", "Manual sync triggered from control panel")
            
    def send_test_logs(self):
        """Send test logs to server"""
        if self.device_simulator:
            self.device_simulator.send_test_logs()
            # Add visual feedback in logs
            self.log_display.add_log("INFO", "UI", "Test logs sent to server from control panel")
            
    def toggle_fullscreen(self):
        """Toggle fullscreen media display"""
        if self.fullscreen_window is None:
            self.create_fullscreen_window()
        else:
            self.close_fullscreen_window()
            
    def create_fullscreen_window(self):
        """Create fullscreen window for media display"""
        self.fullscreen_window = QMainWindow()
        self.fullscreen_window.setWindowTitle("PiSignage Player - Fullscreen Dynamic Layout")
        
        # Create new dynamic media widget for fullscreen
        fullscreen_media = DynamicMediaPlayerWidget()
        self.fullscreen_window.setCentralWidget(fullscreen_media)
        
        # Copy current playlist state if available
        current_status = self.media_player.get_playback_status()
        if current_status['playlist_name'] != 'None':
            # Try to copy current playlist data to fullscreen
            # For now, just show the same layout
            current_layout = current_status.get('layout', '1')
            fullscreen_media.create_layout(current_layout)
            
        self.fullscreen_window.showFullScreen()
        
        # Connect close event
        def close_fullscreen_event(event):
            self.close_fullscreen_window()
            event.accept()
        
        self.fullscreen_window.closeEvent = close_fullscreen_event
        
        self.log_display.add_log("INFO", "UI", "Fullscreen mode activated")
        
    def close_fullscreen_window(self):
        """Close fullscreen window"""
        if self.fullscreen_window:
            self.fullscreen_window.close()
            self.fullscreen_window = None
            self.log_display.add_log("INFO", "UI", "Fullscreen mode deactivated")
            
    def update_status(self, message):
        """Update status bar message"""
        self.status_bar.showMessage(message)
        
    def create_new_window(self):
        """Create new simulator window"""
        new_window = PiSignageSimulatorMainWindow()
        new_window.show()
        self.log_display.add_log("INFO", "UI", "New simulator window created")
        
    def show_about(self):
        """Show about dialog"""
        about_text = """PiSignage Device Simulator - Dynamic Zone System

A PyQt6-based simulator for testing PiSignage Django server.

Features:
• Dynamic zone creation based on server layouts
• Multi-media support (video, image, HTML)
• Real-time sync simulation
• Layout testing and visualization
• Health monitoring simulation
• Log centralization

Layout Support:
• Layout 1: Full screen
• Layout 2a: Main + Side (75% + 25%)
• Layout 2b: Main + Bottom (75% + 25%)
• Layout 3a: Side + Main + Side (25% + 50% + 25%)
• Layout 3b: Main + Side + Bottom
• Layout 4: 4 Quadrants
• Layout 4b: Main + 3 Small zones
• Layout 2ab: Main + Side + Bottom

Version: 1.0.0 - Dynamic Zone System"""
        
        QMessageBox.about(self, "About PiSignage Simulator", about_text)
        
    def closeEvent(self, event):
        """Handle application close"""
        if self.device_simulator:
            self.device_simulator.stop()
            
        if self.fullscreen_window:
            self.fullscreen_window.close()
            
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PiSignage Simulator")
    app.setOrganizationName("PiSignage")
    app.setApplicationVersion("1.0.0 - Dynamic Zone System")
    
    # Set application icon (if available)
    # app.setWindowIcon(QIcon("icon.png"))
    
    # Print startup information
    print("🎪 PiSignage Device Simulator - Dynamic Zone System")
    print("   Features: Dynamic zone creation, multi-media support, layout testing")
    print("   Supported layouts: 1, 2a, 2b, 3a, 3b, 4, 4b, 2ab")
    print("   Controls: View menu -> Test Layouts for immediate layout testing")
    print()
    
    window = PiSignageSimulatorMainWindow()
    window.show()
    
    # Test initial layout
    window.test_layout('1')
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()