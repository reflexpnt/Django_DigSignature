#!/usr/bin/env python3
"""
Media Player Module for PiSignage Simulator
Handles video/image playback with layout support
"""

import os
import json
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QStackedWidget, QGraphicsView, 
                             QGraphicsScene, QGraphicsPixmapItem, 
                             QGraphicsVideoItem)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl, QRectF, QSizeF
from PyQt6.QtGui import QPixmap, QFont, QPainter, QBrush, QColor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


class LayoutZone(QWidget):
    """Individual zone within a layout"""
    
    def __init__(self, zone_name, zone_config):
        super().__init__()
        self.zone_name = zone_name
        self.zone_config = zone_config
        self.current_media = None
        
        self.init_ui()
        self.setup_media_player()
        
    def init_ui(self):
        """Initialize zone UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Zone content stack
        self.content_stack = QStackedWidget()
        
        # Video widget
        self.video_widget = QVideoWidget()
        self.content_stack.addWidget(self.video_widget)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("QLabel { background-color: black; }")
        self.content_stack.addWidget(self.image_label)
        
        # Placeholder label
        self.placeholder_label = QLabel(f"Zone: {self.zone_name}")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet("""
            QLabel { 
                background-color: #2d2d2d; 
                color: white; 
                font-size: 14px;
                border: 2px dashed #555;
            }
        """)
        self.content_stack.addWidget(self.placeholder_label)
        
        # Set placeholder as default
        self.content_stack.setCurrentWidget(self.placeholder_label)
        
        layout.addWidget(self.content_stack)
        
        # Zone border
        self.setStyleSheet(f"""
            LayoutZone {{
                border: 1px solid #444;
                background-color: black;
            }}
        """)
        
    def setup_media_player(self):
        """Setup media player for this zone"""
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)
        
        # Connect signals
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        self.media_player.positionChanged.connect(self.handle_position_changed)
        
        # Playback timer for duration-based content
        self.playback_timer = QTimer()
        self.playback_timer.setSingleShot(True)
        self.playback_timer.timeout.connect(self.handle_playback_finished)
        
    def play_media(self, asset_info):
        """Play media in this zone"""
        self.current_media = asset_info
        
        asset_type = asset_info.get('type', 'unknown')
        file_path = asset_info.get('file_path', '')
        duration = asset_info.get('duration', 10)
        
        if asset_type == 'video':
            self.play_video(file_path)
        elif asset_type == 'image':
            self.play_image(file_path, duration)
        else:
            self.show_placeholder()
            
    def play_video(self, file_path):
        """Play video file"""
        if os.path.exists(file_path):
            url = QUrl.fromLocalFile(file_path)
            self.media_player.setSource(url)
            self.content_stack.setCurrentWidget(self.video_widget)
            self.media_player.play()
        else:
            self.show_error(f"Video not found: {os.path.basename(file_path)}")
            
    def play_image(self, file_path, duration):
        """Display image for specified duration"""
        if os.path.exists(file_path):
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Scale pixmap to fit label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.content_stack.setCurrentWidget(self.image_label)
                
                # Start timer for duration
                self.playback_timer.start(duration * 1000)
            else:
                self.show_error("Invalid image file")
        else:
            self.show_error(f"Image not found: {os.path.basename(file_path)}")
            
    def show_placeholder(self):
        """Show placeholder content"""
        self.content_stack.setCurrentWidget(self.placeholder_label)
        
    def show_error(self, message):
        """Show error message"""
        self.placeholder_label.setText(f"Error: {message}")
        self.content_stack.setCurrentWidget(self.placeholder_label)
        
    def stop_media(self):
        """Stop current media playback"""
        self.media_player.stop()
        self.playback_timer.stop()
        self.current_media = None
        
    def handle_media_status(self, status):
        """Handle media player status changes"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.handle_playback_finished()
            
    def handle_position_changed(self, position):
        """Handle playback position changes"""
        pass  # Can be used for progress tracking
        
    def handle_playback_finished(self):
        """Handle when media playback finishes"""
        # Can emit signal to parent for playlist management
        pass


class TickerWidget(QLabel):
    """Scrolling ticker widget"""
    
    def __init__(self, text="", speed=5, position="bottom"):
        super().__init__()
        self.ticker_text = text
        self.scroll_speed = max(1, min(10, speed))  # 1-10 range
        self.ticker_position = position
        
        self.init_ui()
        self.setup_animation()
        
    def init_ui(self):
        """Initialize ticker UI"""
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.8);
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        
        self.setText(self.ticker_text)
        self.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
    def setup_animation(self):
        """Setup ticker animation"""
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.scroll_text)
        
        # Adjust timer interval based on speed (higher speed = faster scroll)
        interval = max(50, 500 - (self.scroll_speed * 45))
        self.scroll_timer.start(interval)
        
        self.scroll_position = 0
        
    def scroll_text(self):
        """Animate ticker text scrolling"""
        if not self.ticker_text:
            return
            
        # Simple horizontal scrolling animation
        text_width = self.fontMetrics().horizontalAdvance(self.ticker_text)
        widget_width = self.width()
        
        if text_width > widget_width:
            # Text is longer than widget, scroll it
            self.scroll_position += 2
            if self.scroll_position > text_width + widget_width:
                self.scroll_position = -widget_width
                
            # Update text position (simplified)
            spaces = " " * (self.scroll_position // 10)
            display_text = spaces + self.ticker_text
            self.setText(display_text)
        
    def update_ticker(self, text, speed=None):
        """Update ticker text and speed"""
        self.ticker_text = text
        if speed is not None:
            self.scroll_speed = max(1, min(10, speed))
            interval = max(50, 500 - (self.scroll_speed * 45))
            self.scroll_timer.setInterval(interval)
            
        self.scroll_position = 0
        
    def start_ticker(self):
        """Start ticker animation"""
        self.scroll_timer.start()
        
    def stop_ticker(self):
        """Stop ticker animation"""
        self.scroll_timer.stop()


class MediaPlayerWidget(QWidget):
    """Main media player widget with layout support"""
    
    # Signals
    playback_finished = pyqtSignal(str)  # zone_name
    layout_changed = pyqtSignal(str)  # layout_code
    
    def __init__(self):
        super().__init__()
        self.current_layout = None
        self.zones = {}
        self.ticker = None
        self.current_playlist = None
        self.current_item_index = 0
        
        self.init_ui()
        self.setup_playlist_timer()
        
    def init_ui(self):
        """Initialize media player UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main content area
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("QWidget { background-color: black; }")
        self.main_layout.addWidget(self.content_widget)
        
        # Default single zone layout
        self.setup_layout("1")
        
    def setup_playlist_timer(self):
        """Setup timer for playlist progression"""
        self.playlist_timer = QTimer()
        self.playlist_timer.setSingleShot(True)
        self.playlist_timer.timeout.connect(self.play_next_item)
        
    def setup_layout(self, layout_code):
        """Setup layout zones based on layout code"""
        if self.current_layout == layout_code:
            return
            
        # Clear existing layout
        self.clear_layout()
        
        # Layout configurations - matching Django models
        layout_configs = {
            '1': {  # Full screen
                'main': {'x': 0, 'y': 0, 'width': 100, 'height': 100}
            },
            '2a': {  # Main + Side
                'main': {'x': 0, 'y': 0, 'width': 75, 'height': 100},
                'side': {'x': 75, 'y': 0, 'width': 25, 'height': 100}
            },
            '2b': {  # Main + Bottom
                'main': {'x': 0, 'y': 0, 'width': 100, 'height': 75},
                'bottom': {'x': 0, 'y': 75, 'width': 100, 'height': 25}
            },
            '3a': {  # Main + 2 Sides
                'main': {'x': 25, 'y': 0, 'width': 50, 'height': 100},
                'side1': {'x': 0, 'y': 0, 'width': 25, 'height': 100},
                'side2': {'x': 75, 'y': 0, 'width': 25, 'height': 100}
            },
            '3b': {  # Main + Side + Bottom
                'main': {'x': 0, 'y': 0, 'width': 75, 'height': 75},
                'side': {'x': 75, 'y': 0, 'width': 25, 'height': 75},
                'bottom': {'x': 0, 'y': 75, 'width': 100, 'height': 25}
            },
            '4': {  # 4 Quadrants
                'zone1': {'x': 0, 'y': 0, 'width': 50, 'height': 50},
                'zone2': {'x': 50, 'y': 0, 'width': 50, 'height': 50},
                'zone3': {'x': 0, 'y': 50, 'width': 50, 'height': 50},
                'zone4': {'x': 50, 'y': 50, 'width': 50, 'height': 50}
            },
            '4b': {  # Main + 3 Zones
                'main': {'x': 0, 'y': 0, 'width': 67, 'height': 67},
                'zone2': {'x': 67, 'y': 0, 'width': 33, 'height': 33},
                'zone3': {'x': 67, 'y': 33, 'width': 33, 'height': 34},
                'zone4': {'x': 0, 'y': 67, 'width': 67, 'height': 33}
            },
            '2ab': {  # Main + Side + Bottom
                'main': {'x': 0, 'y': 0, 'width': 75, 'height': 75},
                'side': {'x': 75, 'y': 0, 'width': 25, 'height': 75},
                'bottom': {'x': 0, 'y': 75, 'width': 100, 'height': 25}
            }
        }
        
        if layout_code not in layout_configs:
            layout_code = '1'  # Fallback to single zone
            
        config = layout_configs[layout_code]
        
        # Create new layout
        if len(config) == 1:
            # Single zone - simple layout
            layout = QVBoxLayout(self.content_widget)
            zone_name = list(config.keys())[0]
            zone = LayoutZone(zone_name, config[zone_name])
            layout.addWidget(zone)
            self.zones[zone_name] = zone
        else:
            # Multi-zone - grid layout with percentage-based positioning
            # For simplicity, using nested layouts
            self.setup_multi_zone_layout(config)
            
        self.current_layout = layout_code
        self.layout_changed.emit(layout_code)
        
    def setup_multi_zone_layout(self, config):
        """Setup multi-zone layout using percentage positioning"""
        # Create a frame for absolute positioning
        frame = QFrame(self.content_widget)
        frame.setStyleSheet("QFrame { background-color: black; }")
        
        layout = QVBoxLayout(self.content_widget)
        layout.addWidget(frame)
        
        # Create zones with absolute positioning
        for zone_name, zone_config in config.items():
            zone = LayoutZone(zone_name, zone_config)
            zone.setParent(frame)
            self.zones[zone_name] = zone
            
        # Resize zones when frame is resized
        def resize_zones():
            frame_rect = frame.rect()
            for zone_name, zone in self.zones.items():
                zone_config = config[zone_name]
                x = int(frame_rect.width() * zone_config['x'] / 100)
                y = int(frame_rect.height() * zone_config['y'] / 100)
                w = int(frame_rect.width() * zone_config['width'] / 100)
                h = int(frame_rect.height() * zone_config['height'] / 100)
                zone.setGeometry(x, y, w, h)
                
        frame.resizeEvent = lambda e: resize_zones()
        
    def clear_layout(self):
        """Clear current layout"""
        # Stop all media playback
        for zone in self.zones.values():
            zone.stop_media()
            zone.deleteLater()
            
        self.zones.clear()
        
        # Clear layout
        layout = self.content_widget.layout()
        if layout:
            for i in reversed(range(layout.count())):
                layout.itemAt(i).widget().deleteLater()
            layout.deleteLater()
            
        # Remove ticker if exists
        if self.ticker:
            self.ticker.deleteLater()
            self.ticker = None
            
    def load_playlist(self, playlist_data):
        """Load and start playing playlist"""
        self.current_playlist = playlist_data
        self.current_item_index = 0
        
        # Setup layout
        layout_code = playlist_data.get('layout', '1')
        self.setup_layout(layout_code)
        
        # Setup ticker if enabled
        if playlist_data.get('ticker', {}).get('enabled', False):
            self.setup_ticker(playlist_data['ticker'])
            
        # Start playing first item
        self.play_current_item()
        
    def setup_ticker(self, ticker_config):
        """Setup ticker widget"""
        if self.ticker:
            self.ticker.deleteLater()
            
        text = ticker_config.get('text', '')
        speed = ticker_config.get('speed', 5)
        position = ticker_config.get('position', 'bottom')
        
        self.ticker = TickerWidget(text, speed, position)
        
        # Add ticker to layout
        if position == 'bottom':
            self.main_layout.addWidget(self.ticker)
        else:  # top
            self.main_layout.insertWidget(0, self.ticker)
            
    def play_current_item(self):
        """Play current playlist item"""
        if not self.current_playlist or not self.current_playlist.get('items'):
            return
            
        items = self.current_playlist['items']
        if self.current_item_index >= len(items):
            # Playlist finished - repeat if enabled
            if self.current_playlist.get('repeat', True):
                self.current_item_index = 0
            else:
                return
                
        item = items[self.current_item_index]
        zone_name = item.get('zone', 'main')
        duration = item.get('duration', 10)
        
        # Get zone
        if zone_name in self.zones:
            zone = self.zones[zone_name]
            
            # Create asset info for zone
            asset_info = {
                'type': item.get('asset_type', 'image'),
                'file_path': item.get('file_path', ''),
                'duration': duration
            }
            
            zone.play_media(asset_info)
            
            # Set timer for next item
            self.playlist_timer.start(duration * 1000)
            
    def play_next_item(self):
        """Play next playlist item"""
        self.current_item_index += 1
        self.play_current_item()
        
    def stop_playlist(self):
        """Stop current playlist"""
        self.playlist_timer.stop()
        
        for zone in self.zones.values():
            zone.stop_media()
            
        if self.ticker:
            self.ticker.stop_ticker()
            
    def set_fullscreen_mode(self, fullscreen=True):
        """Set fullscreen mode"""
        if fullscreen:
            self.showFullScreen()
        else:
            self.showNormal()
            
    def get_playback_status(self):
        """Get current playback status"""
        return {
            'layout': self.current_layout,
            'playlist_name': self.current_playlist.get('name', 'None') if self.current_playlist else 'None',
            'current_item': self.current_item_index + 1 if self.current_playlist else 0,
            'total_items': len(self.current_playlist.get('items', [])) if self.current_playlist else 0,
            'zones_active': len(self.zones),
            'ticker_active': self.ticker is not None and self.ticker.isVisible()
        }
        