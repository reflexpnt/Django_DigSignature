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
        self.log_message.emit("INFO", "DOWNLOAD", f"Starting download of {len(assets)} assets", "AssetDownloader")
        
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
                
                # Preservar extensión del archivo original
                file_extension = self._get_file_extension(asset)
                if file_extension and not asset_name.endswith(file_extension):
                    local_filename = f"{asset_name}{file_extension}"
                else:
                    local_filename = asset_name
                    
                local_path = local_dir / local_filename
                
                # Check if file exists and is valid
                if self._verify_existing_file(local_path, asset_checksum):
                    file_size = local_path.stat().st_size
                    print(f"📁 Asset already exists and verified: {local_filename} ({file_size} bytes)")
                    self.log_message.emit("DEBUG", "DOWNLOAD", f"Asset already exists and verified: {local_filename} ({file_size} bytes)", "AssetDownloader")
                    
                    self.downloaded_assets[asset_id] = str(local_path)
                    
                    # Signal for media display
                    if asset['type'] in ['video', 'image']:
                        self.media_ready.emit(str(local_path))
                else:
                    # File doesn't exist or is invalid - download it
                    print(f"⬇️  Downloading asset: {asset_name} -> {local_filename}")
                    self.log_message.emit("INFO", "DOWNLOAD", f"Starting download: {asset_name} -> {local_filename}", "AssetDownloader")
                    
                    if self._download_single_asset(asset, local_path):
                        self.downloaded_assets[asset_id] = str(local_path)
                        
                        # Signal for media display
                        if asset['type'] in ['video', 'image']:
                            self.media_ready.emit(str(local_path))
                    else:
                        self.log_message.emit("ERROR", "DOWNLOAD", f"Failed to download asset: {asset_name}", "AssetDownloader")
                        
            except Exception as e:
                asset_name = asset.get('name', 'unknown')
                print(f"❌ Unexpected error downloading asset {asset_name}: {e}")
                self.log_message.emit("ERROR", "DOWNLOAD", f"Unexpected error downloading asset {asset_name}: {e}", "AssetDownloader")
                
    def _get_file_extension(self, asset):
        """Extract file extension from asset metadata"""
        # Try to get extension from metadata
        metadata = asset.get('metadata', {})
        original_name = metadata.get('original_name', '')
        
        if original_name and '.' in original_name:
            return os.path.splitext(original_name)[1]
        
        # Fallback based on asset type
        type_extensions = {
            'video': '.mp4',
            'image': '.jpg',
            'audio': '.mp3',
            'pdf': '.pdf',
            'html': '.html',
            'zip': '.zip'
        }
        
        asset_type = asset.get('type', '')
        return type_extensions.get(asset_type, '')
                
    def _download_single_asset(self, asset, local_path):
        """Download a single asset file"""
        asset_name = asset['name']
        asset_type = asset.get('type', 'unknown')
        asset_url = asset['url']
        
        try:
            # Construct download URL
            download_url = self._build_download_url(asset_url)
            
            print(f"🌐 Download URL: {download_url}")
            self.log_message.emit("DEBUG", "DOWNLOAD", f"Download URL: {download_url}", "AssetDownloader")
            
            # Download with appropriate headers
            headers = {
                'User-Agent': 'PiSignage-Simulator/1.0',
                'Accept': '*/*'
            }
            
            self.log_message.emit("INFO", "DOWNLOAD", f"Requesting asset from server: {asset_name}", "AssetDownloader")
            response = self.session.get(download_url, timeout=60, stream=True, headers=headers)
            
            print(f"📡 Server response: HTTP {response.status_code}")
            self.log_message.emit("DEBUG", "DOWNLOAD", f"Server response: HTTP {response.status_code}", "AssetDownloader")
            
            if response.status_code == 200:
                return self._save_asset_file(response, local_path, asset_name)
            elif response.status_code == 404:
                self.log_message.emit("ERROR", "DOWNLOAD", f"Asset not found on server: {asset_name} (HTTP 404)", "AssetDownloader")
                print(f"❌ Asset not found: {asset_name}")
                return False
            else:
                error_text = response.text[:200] if response.text else "No error details"
                self.log_message.emit("ERROR", "DOWNLOAD", f"Failed to download asset: {asset_name} - HTTP {response.status_code}: {error_text}", "AssetDownloader")
                print(f"❌ Download failed: HTTP {response.status_code} - {error_text}")
                return False
                
        except requests.exceptions.Timeout:
            self.log_message.emit("ERROR", "NETWORK", f"Download timeout for asset {asset_name}", "AssetDownloader")
            print(f"⏰ Download timeout: {asset_name}")
            return False
        except requests.exceptions.ConnectionError:
            self.log_message.emit("ERROR", "NETWORK", f"Connection error downloading asset {asset_name}", "AssetDownloader")
            print(f"📡 Connection error: {asset_name}")
            return False
        except requests.exceptions.RequestException as e:
            self.log_message.emit("ERROR", "NETWORK", f"Network error downloading asset {asset_name}: {e}", "AssetDownloader")
            print(f"🌐 Network error: {asset_name} - {e}")
            return False
            
    def _build_download_url(self, asset_url):
        """Build complete download URL"""
        server_url = self.config['server_url'].rstrip('/')
        
        if asset_url.startswith('http'):
            # Already a complete URL
            return asset_url
        elif asset_url.startswith('/'):
            # Absolute path - prepend server URL
            return f"{server_url}{asset_url}"
        else:
            # Relative path - prepend server URL with slash
            return f"{server_url}/{asset_url}"
            
    def _save_asset_file(self, response, local_path, asset_name):
        """Save downloaded asset to local file"""
        try:
            # Check expected file size
            content_length = response.headers.get('Content-Length')
            expected_size = None
            if content_length:
                expected_size = int(content_length)
                self.log_message.emit("DEBUG", "DOWNLOAD", f"Expected file size: {expected_size} bytes", "AssetDownloader")
                print(f"📏 Expected size: {expected_size} bytes")
            
            # Create parent directory if it doesn't exist
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            file_size = 0
            chunk_count = 0
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
                        file_size += len(chunk)
                        chunk_count += 1
                        
                        # Log progress every 100 chunks (~800KB)
                        if chunk_count % 100 == 0:
                            self.log_message.emit("DEBUG", "DOWNLOAD", f"Downloaded {file_size} bytes so far...", "AssetDownloader")
            
            # Verify download
            if file_size > 0:
                print(f"✅ Asset downloaded successfully: {asset_name} ({file_size} bytes)")
                self.log_message.emit("INFO", "DOWNLOAD", f"Asset downloaded successfully: {asset_name} ({file_size} bytes)", "AssetDownloader")
                
                # Verify size if expected
                if expected_size and file_size != expected_size:
                    self.log_message.emit("WARN", "DOWNLOAD", f"File size mismatch: expected {expected_size}, got {file_size}", "AssetDownloader")
                    print(f"⚠️  Size mismatch: expected {expected_size}, got {file_size}")
                
                return True
            else:
                print(f"❌ Downloaded file is empty: {asset_name}")
                self.log_message.emit("ERROR", "DOWNLOAD", f"Downloaded file is empty: {asset_name}", "AssetDownloader")
                local_path.unlink(missing_ok=True)  # Remove empty file
                return False
                
        except PermissionError:
            self.log_message.emit("ERROR", "DOWNLOAD", f"Permission denied saving asset {asset_name}", "AssetDownloader")
            print(f"🔒 Permission denied: {asset_name}")
            return False
        except OSError as e:
            self.log_message.emit("ERROR", "DOWNLOAD", f"OS error saving asset {asset_name}: {e}", "AssetDownloader")
            print(f"💾 OS error: {asset_name} - {e}")
            return False
        except Exception as e:
            self.log_message.emit("ERROR", "DOWNLOAD", f"Error saving asset {asset_name}: {e}", "AssetDownloader")
            print(f"❌ Save error: {asset_name} - {e}")
            return False
            
    def _verify_existing_file(self, file_path, expected_checksum):
        """Verify existing file is valid"""
        if not file_path.exists():
            return False
            
        try:
            # Check file size first
            file_size = file_path.stat().st_size
            if file_size == 0:
                print(f"🗑️  Removing empty file: {file_path.name}")
                file_path.unlink()
                return False
                
            # If no checksum provided, assume file is good if it exists and has size > 1KB
            if not expected_checksum:
                is_valid = file_size > 1024  # Must be larger than 1KB
                if not is_valid:
                    print(f"📏 File too small ({file_size} bytes), will re-download: {file_path.name}")
                return is_valid
                
            # Verify checksum if provided
            print(f"🔍 Verifying checksum for: {file_path.name}")
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            calculated_checksum = sha256_hash.hexdigest()
            is_valid = calculated_checksum == expected_checksum
            
            if not is_valid:
                print(f"❌ Checksum mismatch for {file_path.name}")
                print(f"   Expected: {expected_checksum[:16]}...")
                print(f"   Got:      {calculated_checksum[:16]}...")
            else:
                print(f"✅ Checksum verified for {file_path.name}")
                
            return is_valid
            
        except Exception as e:
            print(f"❌ Error verifying file {file_path}: {e}")
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