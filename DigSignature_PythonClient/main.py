#!/usr/bin/env python3
"""
PiSignage Device Simulator - Main Application
PyQt6-based simulator that mimics Android device behavior
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
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
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
    from config import DeviceConfig, DEVICE_PRESETS
except ImportError as e:
    print(f"Error importing config: {e}")
    # Create minimal fallback
    class DeviceConfig:
        pass
    DEVICE_PRESETS = {
        "Default Tablet": {
            "resolution": "1920x1080",
            "description": "Default configuration"
        }
    }


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
        
        # Device ID
        self.device_id_input = QLineEdit("A1B2C3D4E5F6G7H8")
        self.device_id_input.setMaxLength(16)
        device_layout.addRow("Device ID:", self.device_id_input)
        
        # Device Name
        self.device_name_input = QLineEdit("PyQt6 Simulator")
        device_layout.addRow("Device Name:", self.device_name_input)
        
        # Screen Resolution
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1920x1080", "1280x720", "1024x768", "800x600"])
        device_layout.addRow("Resolution:", self.resolution_combo)
        
        layout.addWidget(device_group)
        
        # Server Configuration
        server_group = QGroupBox("Server Configuration")
        server_layout = QFormLayout(server_group)
        
        self.server_url_input = QLineEdit("http://localhost:8000")
        server_layout.addRow("Server URL:", self.server_url_input)
        
        # Sync interval spin box with immediate update
        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setRange(10, 3600)
        self.sync_interval_spin.setValue(30)
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
        
        # Health sliders with immediate update
        self.battery_slider = QSlider(Qt.Orientation.Horizontal)
        self.battery_slider.setRange(0, 100)
        self.battery_slider.setValue(85)
        self.battery_label = QLabel("85%")
        battery_layout = QHBoxLayout()
        battery_layout.addWidget(self.battery_slider)
        battery_layout.addWidget(self.battery_label)
        self.battery_slider.valueChanged.connect(self.on_battery_changed)
        health_layout.addRow("Battery:", battery_layout)
        
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(20, 80)
        self.temperature_slider.setValue(38)
        self.temp_label = QLabel("38°C")
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temp_label)
        self.temperature_slider.valueChanged.connect(self.on_temperature_changed)
        health_layout.addRow("Temperature:", temp_layout)
        
        self.storage_spin = QSpinBox()
        self.storage_spin.setRange(100, 32000)
        self.storage_spin.setValue(2048)
        self.storage_spin.setSuffix(" MB")
        self.storage_spin.valueChanged.connect(self.on_storage_changed)
        health_layout.addRow("Free Storage:", self.storage_spin)
        
        layout.addWidget(health_group)
        
        # Network Simulation
        network_group = QGroupBox("Network Simulation")
        network_layout = QFormLayout(network_group)
        
        self.connection_combo = QComboBox()
        self.connection_combo.addItems(["wifi", "mobile", "ethernet"])
        network_layout.addRow("Connection:", self.connection_combo)
        
        self.signal_slider = QSlider(Qt.Orientation.Horizontal)
        self.signal_slider.setRange(-120, -30)
        self.signal_slider.setValue(-45)
        self.signal_label = QLabel("-45 dBm")
        signal_layout = QHBoxLayout()
        signal_layout.addWidget(self.signal_slider)
        signal_layout.addWidget(self.signal_label)
        self.signal_slider.valueChanged.connect(self.on_signal_changed)
        network_layout.addRow("Signal Strength:", signal_layout)
        
        self.offline_checkbox = QCheckBox("Simulate Offline Mode")
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
            
    def load_preset(self, preset_name):
        """Load device preset configuration"""
        if preset_name in DEVICE_PRESETS:
            preset = DEVICE_PRESETS[preset_name]
            self.resolution_combo.setCurrentText(preset['resolution'])
            # Update other fields based on preset
        
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


class MediaDisplayWidget(QWidget):
    """Widget for displaying media content (videos, images)"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_media_player()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(640, 480)
        layout.addWidget(self.video_widget)
        
        # Media controls (hidden in fullscreen)
        controls_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶")
        self.play_btn.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_btn)
        
        self.progress_bar = QProgressBar()
        controls_layout.addWidget(self.progress_bar)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        controls_layout.addWidget(self.volume_slider)
        
        layout.addLayout(controls_layout)
        
        # Status label
        self.status_label = QLabel("Ready to play media")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("QLabel { background-color: rgba(0,0,0,0.7); color: white; padding: 10px; }")
        layout.addWidget(self.status_label)
        
    def setup_media_player(self):
        """Setup Qt media player"""
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)
        
        # Connect signals
        self.media_player.positionChanged.connect(self.update_progress)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        
        # Set initial volume
        self.audio_output.setVolume(0.7)
        
    def play_media(self, file_path):
        """Play media file"""
        from PyQt6.QtCore import QUrl
        
        if os.path.exists(file_path):
            url = QUrl.fromLocalFile(file_path)
            self.media_player.setSource(url)
            self.media_player.play()
            self.status_label.setText(f"Playing: {os.path.basename(file_path)}")
            self.play_btn.setText("⏸")
        else:
            self.status_label.setText(f"File not found: {file_path}")
            
    def stop_media(self):
        """Stop media playback"""
        self.media_player.stop()
        self.status_label.setText("Stopped")
        self.play_btn.setText("▶")
        
    def toggle_playback(self):
        """Toggle play/pause"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_btn.setText("▶")
        else:
            self.media_player.play()
            self.play_btn.setText("⏸")
            
    def set_volume(self, value):
        """Set audio volume"""
        self.audio_output.setVolume(value / 100.0)
        
    def update_progress(self, position):
        """Update progress bar"""
        if self.media_player.duration() > 0:
            progress = int((position / self.media_player.duration()) * 100)
            self.progress_bar.setValue(progress)
            
    def update_duration(self, duration):
        """Update progress bar maximum"""
        self.progress_bar.setMaximum(duration)
        
    def handle_media_status(self, status):
        """Handle media status changes"""
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.status_label.setText("Media loaded, ready to play")
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.status_label.setText("Playback finished")
            self.play_btn.setText("▶")


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
    """Main window for PiSignage device simulator"""
    
    def __init__(self):
        super().__init__()
        self.device_simulator = None
        self.fullscreen_window = None
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        self.setWindowTitle("PiSignage Device Simulator")
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
        
        # Media display tab
        self.media_display = MediaDisplayWidget()
        tab_widget.addTab(self.media_display, "📺 Media Display")
        
        # Logs tab
        self.log_display = LogDisplayWidget()
        tab_widget.addTab(self.log_display, "📝 Device Logs")
        
        layout.addWidget(tab_widget, 1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
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
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        config_action = QAction('Device Configuration', self)
        tools_menu.addAction(config_action)
        
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
                self.log_display.add_log("INFO", "SIMULATOR", "Device simulation started")
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
        print(f"📺 Media file received: {file_path}")
        self.log_display.add_log("INFO", "MEDIA", f"Playing media file: {os.path.basename(file_path)}")
        
        # Play the media file
        self.media_display.play_media(file_path)
        
    def on_sync_completed(self, sync_data):
        """Handle when sync is completed"""
        playlists = sync_data.get('playlists', [])
        assets = sync_data.get('assets', [])
        
        self.log_display.add_log("INFO", "SYNC", f"Sync completed: {len(playlists)} playlists, {len(assets)} assets")
        
        # If we have a playlist, process it for media display
        if playlists:
            playlist = playlists[0]  # Use first playlist
            self.process_playlist_for_display(playlist, sync_data.get('assets', []))
            
    def process_playlist_for_display(self, playlist, assets):
        """Process playlist and start media playback"""
        playlist_name = playlist.get('name', 'Unknown')
        items = playlist.get('items', [])
        layout = playlist.get('layout', '1')
        
        self.log_display.add_log("INFO", "PLAYLIST", f"Processing playlist '{playlist_name}' with layout '{layout}'")
        
        # Create asset lookup
        asset_lookup = {asset['id']: asset for asset in assets}
        
        # Find the first media item to play
        for item in items:
            asset_id = item.get('asset_id')
            if asset_id in asset_lookup:
                asset = asset_lookup[asset_id]
                if asset['type'] in ['video', 'image']:
                    # Signal to download and play this asset
                    self.log_display.add_log("INFO", "MEDIA", f"Queuing media: {asset['name']} ({asset['type']})")
                    break
            
    def stop_simulation(self):
        """Stop device simulation"""
        if self.device_simulator:
            self.device_simulator.stop()
            self.device_simulator = None
            
        # Clear reference in control panel
        self.control_panel.set_device_simulator(None)
            
        self.control_panel.set_simulation_running(False)
        self.status_bar.showMessage("Simulation stopped")
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
        self.fullscreen_window.setWindowTitle("PiSignage Player - Fullscreen")
        
        # Create new media widget for fullscreen
        fullscreen_media = MediaDisplayWidget()
        self.fullscreen_window.setCentralWidget(fullscreen_media)
        
        # Copy current media state
        if hasattr(self.media_display, 'current_file'):
            fullscreen_media.play_media(self.media_display.current_file)
            
        self.fullscreen_window.showFullScreen()
        
        # Connect close event
        self.fullscreen_window.closeEvent = lambda e: self.close_fullscreen_window()
        
    def close_fullscreen_window(self):
        """Close fullscreen window"""
        if self.fullscreen_window:
            self.fullscreen_window.close()
            self.fullscreen_window = None
            
    def update_status(self, message):
        """Update status bar message"""
        self.status_bar.showMessage(message)
        
    def create_new_window(self):
        """Create new simulator window"""
        new_window = PiSignageSimulatorMainWindow()
        new_window.show()
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About PiSignage Simulator", 
                         "PiSignage Device Simulator\n\n"
                         "A PyQt6-based simulator for testing PiSignage Django server.\n"
                         "Simulates Android device behavior with media playback capabilities.")
        
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
    
    # Set application icon (if available)
    # app.setWindowIcon(QIcon("icon.png"))
    
    window = PiSignageSimulatorMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()