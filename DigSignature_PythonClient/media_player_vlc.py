import os
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                            QFrame, QApplication, QStackedLayout)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QPixmap
import vlc


class VLCZone(QWidget):
    def __init__(self, zone_name, mute=False):
        super().__init__()
        self.zone_name = zone_name
        self.media = None
        self.instance = vlc.Instance('--no-xlib', '--no-video-title-show', '--avcodec-hw=none')
        self.player = self.instance.media_player_new()
        self.mute = mute
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.stack = QStackedLayout()

        self.video_label = QLabel()
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.setMinimumSize(320, 240)
        self.stack.addWidget(self.video_label)

        self.overlay_label = QLabel()
        self.overlay_label.setStyleSheet(
            "background-color: rgba(0, 0, 0, 100); color: white; padding: 2px;"
        )
        self.overlay_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.overlay_label.setMargin(5)
        layout.addLayout(self.stack)
        layout.addWidget(self.overlay_label)

    def play_media(self, file_path, media_type):
        self.stop()

        if media_type == 'video':
            self._play_video(file_path)
        elif media_type == 'image':
            self._show_image(file_path)
        elif media_type == 'html':
            self._show_html_placeholder(file_path)
        else:
            self.overlay_label.setText("Unsupported type")

    def _play_video(self, file_path):
        if os.path.exists(file_path):
            self.video_label.setText("")
            self.video_label.show()
            
            if self.video_label.width() > 0 and self.video_label.height() > 0:
                win_id = int(self.video_label.winId())
                if os.name == "nt":
                    self.player.set_hwnd(win_id)
                else:
                    self.player.set_xwindow(win_id)

                media = self.instance.media_new(file_path)
                self.player.set_media(media)

                if self.mute:
                    self.player.audio_set_mute(True)
                else:
                    self.player.audio_set_mute(False)

                self.overlay_label.setText(f"{self.zone_name}: {os.path.basename(file_path)}")
                self.player.play()
            else:
                self.overlay_label.setText(f"{self.zone_name}: Invalid widget size")
        else:
            self.overlay_label.setText(f"{self.zone_name}: File not found")

    def _show_image(self, file_path):
        if os.path.exists(file_path):
            pixmap = QPixmap(file_path)
            self.video_label.setPixmap(pixmap.scaled(
                self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation))
            self.overlay_label.setText(f"{self.zone_name}: {os.path.basename(file_path)}")
        else:
            self.overlay_label.setText(f"{self.zone_name}: Image not found")

    def _show_html_placeholder(self, file_path):
        self.overlay_label.setText(f"{self.zone_name}: [HTML] {os.path.basename(file_path)}")

    def stop(self):
        if self.player:
            self.player.stop()


class VLCMediaPlayerWidget(QWidget):
    def __init__(self, mute=False):
        super().__init__()
        self.zones = {}
        self.mute = mute
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.layout.addWidget(self.content_widget)
        self.current_layout_code = None

    def _get_zones_for_layout(self, layout_code):
        layout_map = {
            '1': ['main'],
            '2a': ['main', 'side'],
            '2b': ['main', 'bottom'],
            '3a': ['main', 'side1', 'side2'],
            '3b': ['main', 'side', 'bottom'],
            '4': ['zone1', 'zone2', 'zone3', 'zone4'],
            '4b': ['main', 'zone2', 'zone3', 'zone4'],
            '2ab': ['main', 'side', 'bottom']
        }
        return layout_map.get(layout_code, ['main'])

    def setup_layout(self, layout_code):
        """Setup the layout with specified zones"""
        # Clear existing zones
        for zone in self.zones.values():
            zone.stop()
            zone.setParent(None)
        self.zones.clear()

        # Create new layout
        zones = self._get_zones_for_layout(layout_code)
        container = QHBoxLayout() if len(zones) <= 2 else QVBoxLayout()

        for zname in zones:
            zone = VLCZone(zname, mute=self.mute)
            self.zones[zname] = zone
            container.addWidget(zone)

        # Clear existing layout and add new one
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        self.content_layout.addLayout(container)
        self.current_layout_code = layout_code

    def load_playlist(self, playlist_data):
        """Load playlist with zone-specific content"""
        layout = playlist_data.get('layout', '1')
        self.setup_layout(layout)

        for item in playlist_data.get('items', []):
            zone = item.get('zone', 'main')
            media_type = item.get('asset_type', 'video')
            path = item.get('file_path', '')

            if zone in self.zones:
                # Mute non-main zones if global mute is enabled
                if zone != 'main' and self.mute:
                    self.zones[zone].player.audio_set_mute(True)
                self.zones[zone].play_media(path, media_type)
            else:
                print(f"[⚠] Zone '{zone}' not found in layout")

    def stop_all(self):
        """Stop all media playback in all zones"""
        for zone in self.zones.values():
            zone.stop()