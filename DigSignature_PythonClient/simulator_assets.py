#!/usr/bin/env python3
"""
Simulator Assets Module
Handles asset downloading and management
"""

import os
import hashlib
import requests
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal


class AssetManager(QObject):
    """Handles asset operations for the simulator"""
    
    # Signals
    log_message = pyqtSignal(str, str, str, str)  # level, category, message, tag
    media_ready = pyqtSignal(str)  # file_path
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.session = requests.Session()
        self.downloaded_assets = {}
        
    def download_assets(self, assets, local_dir):
        """Download assets from server"""
        for asset in assets:
            try:
                asset_id = asset['id']
                asset_name = asset['name']
                asset_type = asset.get('type', 'unknown')
                asset_url = asset.get('url')
                asset_checksum = asset.get('checksum', '')
                
                if not asset_url:
                    self.log_message.emit("WARN", "DOWNLOAD", f"No URL provided for asset: {asset_name}", "AssetDownloader")
                    continue
                    
                local_path = local_dir / asset_name
                
                # Check if file exists and is valid
                if self._verify_existing_file(local_path, asset_checksum):
                    file_size = local_path.stat().st_size
                    print(f"📁 Asset already exists and verified: {asset_name} ({file_size} bytes)")
                    self.log_message.emit("DEBUG", "DOWNLOAD", f"Asset already exists and verified: {asset_name} ({file_size} bytes)", "AssetDownloader")
                    
                    self.downloaded_assets[asset_id] = str(local_path)
                    
                    # Signal for media display
                    if asset['type'] in ['video', 'image']:
                        self.media_ready.emit(str(local_path))
                        
            except Exception as e:
                asset_name = asset.get('name', 'unknown')
                print(f"❌ Unexpected error downloading asset {asset_name}: {e}")
                self.log_message.emit("ERROR", "DOWNLOAD", f"Unexpected error downloading asset {asset_name}: {e}", "AssetDownloader")
                
    def _download_single_asset(self, asset, local_path):
        """Download a single asset file"""
        asset_name = asset['name']
        asset_type = asset.get('type', 'unknown')
        asset_url = asset['url']
        
        try:
            # Construct download URL
            download_url = self._build_download_url(asset_url)
            
            print(f"⬇️ Downloading asset: {asset_name}")
            self.log_message.emit("INFO", "DOWNLOAD", f"Starting download: {asset_name} ({asset_type}) from {download_url}", "AssetDownloader")
            
            # Download with appropriate headers
            headers = {
                'User-Agent': 'PiSignage-Simulator/1.0',
                'Accept': '*/*'
            }
            
            response = self.session.get(download_url, timeout=60, stream=True, headers=headers)
            
            if response.status_code == 200:
                return self._save_asset_file(response, local_path, asset_name)
            elif response.status_code == 404:
                self.log_message.emit("ERROR", "DOWNLOAD", f"Asset not found on server: {asset_name} (HTTP 404)", "AssetDownloader")
                return False
            else:
                error_text = response.text[:200] if response.text else "No error details"
                self.log_message.emit("ERROR", "DOWNLOAD", f"Failed to download asset: {asset_name} - HTTP {response.status_code}: {error_text}", "AssetDownloader")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_message.emit("ERROR", "NETWORK", f"Network error downloading asset {asset_name}: {e}", "AssetDownloader")
            return False
            
    def _build_download_url(self, asset_url):
        """Build complete download URL"""
        if asset_url.startswith('http'):
            return asset_url
        elif asset_url.startswith('/'):
            return f"{self.config['server_url']}{asset_url}"
        else:
            return f"{self.config['server_url']}/{asset_url}"
            
    def _save_asset_file(self, response, local_path, asset_name):
        """Save downloaded asset to local file"""
        try:
            # Check expected file size
            content_length = response.headers.get('Content-Length')
            if content_length:
                expected_size = int(content_length)
                self.log_message.emit("DEBUG", "DOWNLOAD", f"Expected file size: {expected_size} bytes", "AssetDownloader")
            
            # Write file
            file_size = 0
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
                        file_size += len(chunk)
            
            # Verify download
            if file_size > 0:
                print(f"✅ Asset downloaded: {asset_name} ({file_size} bytes)")
                self.log_message.emit("INFO", "DOWNLOAD", f"Asset downloaded successfully: {asset_name} ({file_size} bytes)", "AssetDownloader")
                return True
            else:
                print(f"❌ Downloaded file is empty: {asset_name}")
                self.log_message.emit("ERROR", "DOWNLOAD", f"Downloaded file is empty: {asset_name}", "AssetDownloader")
                local_path.unlink(missing_ok=True)  # Remove empty file
                return False
                
        except Exception as e:
            self.log_message.emit("ERROR", "DOWNLOAD", f"Error saving asset {asset_name}: {e}", "AssetDownloader")
            return False
            
    def _verify_existing_file(self, file_path, expected_checksum):
        """Verify existing file is valid"""
        if not file_path.exists():
            return False
            
        try:
            # Check file size first
            file_size = file_path.stat().st_size
            if file_size == 0:
                return False
                
            # If no checksum provided, assume file is good if it exists and has size
            if not expected_checksum:
                return True
                
            # Verify checksum
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            calculated_checksum = sha256_hash.hexdigest()
            return calculated_checksum == expected_checksum
            
        except Exception as e:
            print(f"Error verifying file {file_path}: {e}")
            return False
            
    def get_asset_count(self):
        """Get number of downloaded assets"""
        return len(self.downloaded_assets)
        
    def get_asset_info(self, asset_id):
        """Get info about a downloaded asset"""
        return self.downloaded_assets.get(asset_id)
        
    def update_config(self, new_config):
        """Update configuration"""
        self.config.update(new_config)