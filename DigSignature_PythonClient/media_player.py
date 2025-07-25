#!/usr/bin/env python3
"""
Media Player Module - Dynamic Zone System for Simulator
ASYNC CLEANUP VERSION: Non-blocking zone management
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QPushButton, QStackedWidget, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

# Try to import WebEngine, fall back gracefully
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
    print("✅ WebEngine available")
except ImportError:
    WEBENGINE_AVAILABLE = False
    print("⚠️ WebEngine not available")


class MediaZoneWidget(QFrame):
    """Individual media zone widget with async cleanup"""
    
    def __init__(self, zone_name, zone_info=None):
        super().__init__()
        self.zone_name = zone_name
        self.zone_info = zone_info or {}
        self.current_media = None
        self.current_type = None
        self.is_stopping = False
        self.is_destroyed = False  # Track destruction state
        
        self.init_ui()
        self.setup_media_components()
        
    def init_ui(self):
        """Initialize zone UI with visible frame"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setStyleSheet(f"""
            QFrame {{
                border: 2px solid #00aaff;
                background-color: #1a1a1a;
                border-radius: 5px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Zone header with info
        self.header = QLabel(f"Zone: {self.zone_name}")
        self.header.setStyleSheet("""
            QLabel {
                color: #00aaff;
                font-weight: bold;
                font-size: 12px;
                background-color: rgba(0, 170, 255, 0.2);
                padding: 3px;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.header)
        
        # Content stack for different media types
        self.content_stack = QStackedWidget()
        layout.addWidget(self.content_stack)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 10px;
                padding: 2px;
            }
        """)
        layout.addWidget(self.status_label)
        
    def setup_media_components(self):
        """Setup different media components"""
        # 1. Video Widget
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.content_stack.addWidget(self.video_widget)
        
        # 2. Image Widget
        self.image_widget = QLabel()
        self.image_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_widget.setStyleSheet("background-color: black; color: white;")
        self.image_widget.setText("Image Zone")
        self.content_stack.addWidget(self.image_widget)
        
        # 3. HTML Widget
        if WEBENGINE_AVAILABLE:
            try:
                self.html_widget = QWebEngineView()
                self.html_widget.setHtml("<h3 style='color: white; text-align: center;'>HTML Zone</h3>")
                self.content_stack.addWidget(self.html_widget)
            except Exception as e:
                print(f"⚠️ WebEngine creation failed: {e}")
                self.create_fallback_html_widget()
        else:
            self.create_fallback_html_widget()
        
        # 4. Placeholder Widget
        self.placeholder_widget = QLabel(f"Zone: {self.zone_name}\n(No content)")
        self.placeholder_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_widget.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: #888;
                font-size: 14px;
                border: 2px dashed #555;
                padding: 10px;
            }
        """)
        self.content_stack.addWidget(self.placeholder_widget)
        
        # Set placeholder as default
        self.content_stack.setCurrentWidget(self.placeholder_widget)
        
        # Setup media player for videos
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)
        
        # Connect signals
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        self.media_player.errorOccurred.connect(self.handle_media_error)
        
        # Timer for image display duration
        self.display_timer = QTimer()
        self.display_timer.setSingleShot(True)
        self.display_timer.timeout.connect(self.handle_display_finished)
        
    def create_fallback_html_widget(self):
        """Create fallback HTML widget when WebEngine not available"""
        self.html_widget = QLabel()
        self.html_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.html_widget.setStyleSheet("""
            QLabel {
                background-color: #333; 
                color: white;
                padding: 10px;
                font-size: 14px;
                border-radius: 3px;
            }
        """)
        self.html_widget.setText("HTML Zone\n(WebEngine fallback)")
        self.html_widget.setWordWrap(True)
        self.content_stack.addWidget(self.html_widget)
        
    def play_media(self, asset_info):
        """Play media based on asset type"""
        if self.is_stopping or self.is_destroyed:
            return
            
        # Stop any current media first
        self.stop_media_internal(switching=True)
        
        self.current_media = asset_info
        
        asset_type = asset_info.get('asset_type', 'unknown')
        file_path = asset_info.get('file_path', '')
        duration = asset_info.get('duration', 10)
        
        print(f"🎬 Zone '{self.zone_name}' loading: {os.path.basename(file_path)} ({asset_type})")
        
        self.current_type = asset_type
        self.update_header(f"Zone: {self.zone_name} - {asset_type.title()}")
        
        try:
            if asset_type == 'video':
                self.play_video(file_path)
            elif asset_type == 'image':
                self.play_image(file_path, duration)
            elif asset_type == 'html':
                self.play_html(file_path)
            else:
                self.show_error(f"Unsupported type: {asset_type}")
        except Exception as e:
            print(f"❌ Error playing media in zone '{self.zone_name}': {e}")
            self.show_error(f"Playback error: {e}")
            
    def play_video(self, file_path):
        """Play video file"""
        if not os.path.exists(file_path):
            self.show_error(f"Video not found: {os.path.basename(file_path)}")
            return
            
        try:
            # Stop and clear first
            self.media_player.stop()
            
            # Load and play with delay for stability
            QTimer.singleShot(50, lambda: self.load_and_play_video(file_path))
            
        except Exception as e:
            self.show_error(f"Video setup error: {e}")
            
    def load_and_play_video(self, file_path):
        """Delayed video loading"""
        if self.is_stopping or self.is_destroyed:
            return
            
        try:
            url = QUrl.fromLocalFile(file_path)
            self.media_player.setSource(url)
            self.content_stack.setCurrentWidget(self.video_widget)
            self.media_player.play()
            
            self.status_label.setText(f"Playing: {os.path.basename(file_path)}")
            print(f"▶️ Zone '{self.zone_name}' playing video: {os.path.basename(file_path)}")
            
        except Exception as e:
            if not self.is_destroyed:
                self.show_error(f"Video load error: {e}")
            
    def play_image(self, file_path, duration):
        """Display image for specified duration"""
        if not os.path.exists(file_path):
            self.show_error(f"Image not found: {os.path.basename(file_path)}")
            return
            
        try:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                self.show_error("Invalid image file")
                return
                
            # Get widget size with fallbacks
            widget_size = self.image_widget.size()
            if widget_size.width() < 100:
                widget_size = self.size()
            if widget_size.width() < 100:
                widget_size = QSize(320, 240)
                
            scaled_pixmap = pixmap.scaled(
                widget_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.image_widget.setPixmap(scaled_pixmap)
            self.content_stack.setCurrentWidget(self.image_widget)
            
            # Start duration timer
            self.display_timer.start(duration * 1000)
            
            self.status_label.setText(f"Image: {os.path.basename(file_path)} ({duration}s)")
            print(f"🖼️ Zone '{self.zone_name}' showing image: {os.path.basename(file_path)} for {duration}s")
            
        except Exception as e:
            if not self.is_destroyed:
                self.show_error(f"Image error: {e}")
            
    def play_html(self, file_path):
        """Display HTML content"""
        try:
            if WEBENGINE_AVAILABLE and hasattr(self.html_widget, 'load'):
                if file_path.startswith('http'):
                    self.html_widget.load(QUrl(file_path))
                else:
                    if os.path.exists(file_path):
                        file_url = QUrl.fromLocalFile(file_path)
                        self.html_widget.load(file_url)
                    else:
                        self.show_error(f"HTML file not found: {os.path.basename(file_path)}")
                        return
            else:
                content_preview = self.get_html_preview(file_path)
                self.html_widget.setText(content_preview)
            
            self.content_stack.setCurrentWidget(self.html_widget)
            self.status_label.setText(f"HTML: {os.path.basename(file_path)}")
            print(f"🌐 Zone '{self.zone_name}' showing HTML: {os.path.basename(file_path)}")
            
        except Exception as e:
            if not self.is_destroyed:
                self.show_error(f"HTML error: {e}")
            
    def get_html_preview(self, file_path):
        """Get HTML preview text for fallback display"""
        if file_path.startswith('http'):
            return f"🌐 Web URL:\n{file_path}"
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                if '<title>' in html_content.lower():
                    import re
                    title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
                    if title_match:
                        return f"📄 HTML File:\n{title_match.group(1)}\n\n{os.path.basename(file_path)}"
                
                return f"📄 HTML File:\n{os.path.basename(file_path)}\n\nSize: {len(html_content)} chars"
            except Exception as e:
                return f"📄 HTML File:\n{os.path.basename(file_path)}\n\nError: {e}"
        else:
            return f"📄 HTML File:\n{os.path.basename(file_path)}\n\nFile not found"
            
    def show_error(self, message):
        """Show error message"""
        if self.is_destroyed:
            return
            
        error_text = f"Zone: {self.zone_name}\nError: {message}"
        self.placeholder_widget.setText(error_text)
        self.placeholder_widget.setStyleSheet("""
            QLabel {
                background-color: #8B0000;
                color: white;
                font-size: 12px;
                border: 2px solid #FF0000;
                padding: 10px;
            }
        """)
        self.content_stack.setCurrentWidget(self.placeholder_widget)
        self.status_label.setText(f"Error: {message}")
        self.update_header(f"Zone: {self.zone_name} - ERROR", "#ff4444")
        
    def show_placeholder(self):
        """Show placeholder content"""
        if self.is_destroyed:
            return
            
        self.placeholder_widget.setText(f"Zone: {self.zone_name}\n(No content)")
        self.placeholder_widget.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: #888;
                font-size: 14px;
                border: 2px dashed #555;
                padding: 10px;
            }
        """)
        self.content_stack.setCurrentWidget(self.placeholder_widget)
        self.status_label.setText("Ready")
        self.update_header(f"Zone: {self.zone_name}")
        
    def update_header(self, text, color="#00aaff"):
        """Update header text and color"""
        if self.is_destroyed:
            return
            
        self.header.setText(text)
        self.header.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-weight: bold;
                font-size: 12px;
                background-color: rgba(0, 170, 255, 0.2);
                padding: 3px;
                border-radius: 3px;
            }}
        """)
        
    def stop_media(self):
        """Public stop method"""
        self.stop_media_internal(switching=False)
        
    def stop_media_internal(self, switching=False):
        """Internal stop method - IMMEDIATE, non-blocking"""
        if self.is_destroyed:
            return
            
        self.is_stopping = True
        
        try:
            # Stop media player IMMEDIATELY
            if self.media_player and not self.is_destroyed:
                self.media_player.stop()
                # Force clear source
                self.media_player.setSource(QUrl())
                
            # Stop timer IMMEDIATELY
            if self.display_timer and not self.is_destroyed:
                self.display_timer.stop()
                
            # Clear image pixmap IMMEDIATELY
            if hasattr(self.image_widget, 'clear') and not self.is_destroyed:
                self.image_widget.clear()
                
        except Exception as e:
            print(f"⚠️ Error stopping media in zone '{self.zone_name}': {e}")
        
        self.current_media = None
        self.current_type = None
        
        if not switching and not self.is_destroyed:
            self.show_placeholder()
            
        self.is_stopping = False
        
    def destroy_async(self):
        """Async destruction - mark as destroyed and schedule cleanup"""
        print(f"💥 Destroying zone '{self.zone_name}'")
        
        self.is_destroyed = True
        self.is_stopping = True
        
        # Immediate cleanup
        try:
            if self.media_player:
                self.media_player.stop()
                self.media_player.setSource(QUrl())
                # Disconnect all signals
                self.media_player.mediaStatusChanged.disconnect()
                self.media_player.errorOccurred.disconnect()
                
            if self.display_timer:
                self.display_timer.stop()
                
            if hasattr(self.image_widget, 'clear'):
                self.image_widget.clear()
                
        except Exception as e:
            print(f"⚠️ Error in immediate cleanup for zone '{self.zone_name}': {e}")
        
        # Schedule deletion
        self.deleteLater()
        
    def handle_media_status(self, status):
        """Handle media player status changes"""
        if self.is_stopping or self.is_destroyed:
            return
            
        try:
            if status == QMediaPlayer.MediaStatus.LoadedMedia:
                self.status_label.setText("Video loaded")
            elif status == QMediaPlayer.MediaStatus.BufferingMedia:
                self.status_label.setText("Buffering...")
            elif status == QMediaPlayer.MediaStatus.BufferedMedia:
                self.status_label.setText("Playing video")
            elif status == QMediaPlayer.MediaStatus.EndOfMedia:
                self.status_label.setText("Video finished")
                print(f"🏁 Zone '{self.zone_name}' video finished")
            elif status == QMediaPlayer.MediaStatus.InvalidMedia:
                self.show_error("Invalid video file")
        except Exception as e:
            print(f"⚠️ Error handling media status in zone '{self.zone_name}': {e}")
            
    def handle_media_error(self, error, error_string):
        """Handle media player errors"""
        if not self.is_stopping and not self.is_destroyed:
            print(f"❌ Media error in zone '{self.zone_name}': {error_string}")
            self.show_error(f"Video error: {error_string}")
        
    def handle_display_finished(self):
        """Handle when image display duration finishes"""
        if not self.is_stopping and not self.is_destroyed:
            print(f"🏁 Zone '{self.zone_name}' image display finished")


class DynamicMediaPlayerWidget(QWidget):
    """Dynamic media player with synchronized layout management"""
    
    # Signals
    layout_changed = pyqtSignal(str)  # layout_code
    zones_created = pyqtSignal(list)  # zone_names
    
    def __init__(self):
        super().__init__()
        self.current_layout = None
        self.zones = {}  # zone_name -> MediaZoneWidget
        self.current_playlist = None
        self.is_layout_ready = True  # Track if ready for new layout
        self.pending_layout = None   # Store pending layout code
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize dynamic media player UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Info header
        self.info_label = QLabel("Dynamic Media Player - Ready")
        self.info_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
                background-color: #333;
                border-radius: 5px;
            }
        """)
        self.main_layout.addWidget(self.info_label)
        
        # Container for dynamic zones
        self.zones_container = QWidget()
        self.zones_container.setStyleSheet("background-color: black;")
        self.main_layout.addWidget(self.zones_container)
        
        # Set default layout
        self.create_layout("1")
        
    def create_layout(self, layout_code):
        """Create zones dynamically with proper synchronization"""
        print(f"🎪 Creating dynamic layout: {layout_code}")
        
        # If currently processing, queue the request
        if not self.is_layout_ready:
            print(f"📋 Layout busy, queuing layout '{layout_code}'")
            self.pending_layout = layout_code
            return
        
        # Mark as busy
        self.is_layout_ready = False
        self.pending_layout = None
        
        # Start the layout change process
        self.start_layout_change(layout_code)
        
    def start_layout_change(self, layout_code):
        """Start the layout change process"""
        # Step 1: Clear existing zones and layout
        self.clear_zones_immediate()
        
        # Step 2: Schedule layout creation after clearing
        QTimer.singleShot(50, lambda: self.create_zones_immediate(layout_code))
        
    def clear_zones_immediate(self):
        """IMMEDIATE zone clearing with proper layout handling"""
        if not self.zones:
            print("🧹 No zones to clear")
            return
            
        zone_count = len(self.zones)
        print(f"🧹 Clearing {zone_count} zones IMMEDIATELY")
        
        # Step 1: Destroy all zone widgets
        zones_to_destroy = list(self.zones.values())
        self.zones.clear()
        
        for zone_widget in zones_to_destroy:
            try:
                zone_widget.destroy_async()
            except Exception as e:
                print(f"⚠️ Error destroying zone: {e}")
        
        # Step 2: Clear the layout properly
        self.clear_container_layout_safe()
        
        print(f"✅ Cleared {zone_count} zones immediately")
        
    def clear_container_layout_safe(self):
        """Safe layout clearing that avoids Qt warnings"""
        try:
            layout = self.zones_container.layout()
            if layout:
                print(f"🧹 Safely clearing layout with {layout.count()} items")
                
                # Remove all widgets first
                while layout.count():
                    item = layout.takeAt(0)
                    if item:
                        widget = item.widget()
                        if widget:
                            widget.setParent(None)
                            widget.deleteLater()
                
                # Instead of setting a temp layout, we'll keep the existing one
                # and just clear it completely
                print("✅ Layout items cleared, keeping layout structure")
        except Exception as e:
            print(f"⚠️ Error clearing container layout: {e}")
            
    def create_zones_immediate(self, layout_code):
        """Create zones with proper layout handling"""
        try:
            print(f"🏗️ Creating zones for layout '{layout_code}'")
            
            # Get current layout and reuse it if it's a QGridLayout, or replace it
            current_layout = self.zones_container.layout()
            
            # Create new grid layout
            grid_layout = QGridLayout()
            grid_layout.setSpacing(3)
            
            # Layout definitions
            layout_definitions = {
                '1': {
                    'zones': ['main'],
                    'positions': {'main': (0, 0, 1, 1)}
                },
                '2a': {
                    'zones': ['main', 'side'],
                    'positions': {
                        'main': (0, 0, 1, 3),
                        'side': (0, 3, 1, 1)
                    }
                },
                '2b': {
                    'zones': ['main', 'bottom'],
                    'positions': {
                        'main': (0, 0, 3, 1),
                        'bottom': (3, 0, 1, 1)
                    }
                },
                '3a': {
                    'zones': ['side1', 'main', 'side2'],
                    'positions': {
                        'side1': (0, 0, 1, 1),
                        'main': (0, 1, 1, 2),
                        'side2': (0, 3, 1, 1)
                    }
                },
                '3b': {
                    'zones': ['main', 'side', 'bottom'],
                    'positions': {
                        'main': (0, 0, 3, 3),
                        'side': (0, 3, 3, 1),
                        'bottom': (3, 0, 1, 4)
                    }
                },
                '4': {
                    'zones': ['zone1', 'zone2', 'zone3', 'zone4'],
                    'positions': {
                        'zone1': (0, 0, 1, 1),
                        'zone2': (0, 1, 1, 1),
                        'zone3': (1, 0, 1, 1),
                        'zone4': (1, 1, 1, 1)
                    }
                },
                '4b': {
                    'zones': ['main', 'zone2', 'zone3', 'zone4'],
                    'positions': {
                        'main': (0, 0, 2, 2),
                        'zone2': (0, 2, 1, 1),
                        'zone3': (1, 2, 1, 1),
                        'zone4': (2, 0, 1, 3)
                    }
                },
                '2ab': {
                    'zones': ['main', 'side', 'bottom'],
                    'positions': {
                        'main': (0, 0, 3, 3),
                        'side': (0, 3, 3, 1),
                        'bottom': (3, 0, 1, 4)
                    }
                }
            }
            
            if layout_code not in layout_definitions:
                layout_code = '1'
                
            layout_def = layout_definitions[layout_code]
            zones = layout_def['zones']
            positions = layout_def['positions']
            
            # Create zone widgets and add to new layout
            created_zones = []
            for zone_name in zones:
                try:
                    zone_widget = MediaZoneWidget(zone_name)
                    
                    # Get position
                    row, col, rowspan, colspan = positions[zone_name]
                    grid_layout.addWidget(zone_widget, row, col, rowspan, colspan)
                    
                    self.zones[zone_name] = zone_widget
                    created_zones.append(zone_name)
                    
                except Exception as e:
                    print(f"❌ Error creating zone '{zone_name}': {e}")
            
            # Replace the layout ONLY if we have a different type or need to
            if current_layout:
                # Delete old layout
                current_layout.setParent(None)
                current_layout.deleteLater()
            
            # Set the new layout
            self.zones_container.setLayout(grid_layout)
            
            self.current_layout = layout_code
            
            # Update info
            self.info_label.setText(f"Layout: {layout_code} | Zones: {', '.join(created_zones)}")
            
            # Mark as ready and process pending requests
            self.is_layout_ready = True
            
            # Process any pending layout request
            if self.pending_layout:
                pending = self.pending_layout
                self.pending_layout = None
                print(f"🔄 Processing pending layout: {pending}")
                QTimer.singleShot(10, lambda: self.create_layout(pending))
            
            # Emit signals
            self.layout_changed.emit(layout_code)
            self.zones_created.emit(created_zones)
            
            print(f"✅ Created {len(created_zones)} zones: {created_zones}")
            
        except Exception as e:
            print(f"❌ Error creating layout '{layout_code}': {e}")
            
            # Mark as ready even on error
            self.is_layout_ready = True
            
            # Fallback to simple layout if this is not already layout '1'
            if layout_code != '1':
                print("🔄 Falling back to layout '1'")
                QTimer.singleShot(200, lambda: self.create_layout('1'))
        
    def load_playlist(self, playlist_data):
        """Load playlist with proper synchronization"""
        self.current_playlist = playlist_data
        
        playlist_name = playlist_data.get('name', 'Unknown')
        layout_code = playlist_data.get('layout', '1')
        items = playlist_data.get('items', [])
        
        print(f"🎬 Loading playlist '{playlist_name}' with layout '{layout_code}' ({len(items)} items)")
        
        try:
            # Create layout and wait for completion
            self.create_layout(layout_code)
            
            # Schedule item loading with a proper delay
            QTimer.singleShot(200, lambda: self.load_items_into_zones(items, playlist_name, layout_code))
            
        except Exception as e:
            print(f"❌ Error loading playlist: {e}")
            
    def load_items_into_zones(self, items, playlist_name, layout_code):
        """Load items into zones after layout is completely ready"""
        try:
            # Wait until layout is ready
            if not self.is_layout_ready:
                print("⏳ Waiting for layout to be ready...")
                QTimer.singleShot(100, lambda: self.load_items_into_zones(items, playlist_name, layout_code))
                return
                
            loaded_count = 0
            for item in items:
                zone_name = item.get('zone', 'main')
                
                if zone_name in self.zones:
                    try:
                        zone_widget = self.zones[zone_name]
                        if not zone_widget.is_destroyed:
                            zone_widget.play_media(item)
                            loaded_count += 1
                            print(f"   ✅ Loaded into zone '{zone_name}': {os.path.basename(item.get('file_path', 'unknown'))}")
                    except Exception as e:
                        print(f"   ❌ Error loading into zone '{zone_name}': {e}")
                else:
                    print(f"   ❌ Zone '{zone_name}' not found in layout '{layout_code}'")
                    
            # Update info
            self.info_label.setText(f"Playing: {playlist_name} | Layout: {layout_code} | {loaded_count}/{len(items)} items")
            
        except Exception as e:
            print(f"❌ Error loading items into zones: {e}")
        
    def stop_playlist(self):
        """Stop all media playback"""
        print("⏹️ Stopping all zones")
        
        try:
            for zone_widget in list(self.zones.values()):
                try:
                    if not zone_widget.is_destroyed:
                        zone_widget.stop_media()
                except Exception as e:
                    print(f"⚠️ Error stopping zone: {e}")
                    
            self.info_label.setText("Dynamic Media Player - Stopped")
            
        except Exception as e:
            print(f"❌ Error stopping playlist: {e}")
        
    def get_playback_status(self):
        """Get current playback status"""
        try:
            playlist_name = self.current_playlist.get('name', 'None') if self.current_playlist else 'None'
            
            return {
                'layout': self.current_layout,
                'playlist_name': playlist_name,
                'zones_active': len(self.zones),
                'zones': list(self.zones.keys())
            }
        except Exception as e:
            print(f"⚠️ Error getting playback status: {e}")
            return {
                'layout': 'error',
                'playlist_name': 'Error',
                'zones_active': 0,
                'zones': []
            }


# Alias for compatibility
MediaPlayerWidget = DynamicMediaPlayerWidget
                