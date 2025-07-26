#!/usr/bin/env python3
"""
Script de testing para las APIs del PiSignage Django Port
Simula el comportamiento de un dispositivo Android
"""

import requests
import json
import time
import sys
from datetime import datetime, timezone

class PiSignageAPITester:
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url.rstrip('/')
        self.device_id = "B2C3D4E5F6G7H8A1"
        self.last_sync_hash = ""
        self.session = requests.Session()
        
    def test_device_registration(self):
        """Test device registration API"""
        print("🔧 Testing device registration...")
        
        url = f"{self.server_url}/players/api/register/"
        data = {
            "device_id": self.device_id,
            "name": "Test Android Device",
            "app_version": "1.0.0",
            "firmware_version": "12"
        }
        
        try:
            response = self.session.post(url, json=data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Device registered: {result['player']['name']}")
                return True
            elif response.status_code == 400 and "already exists" in response.text:
                print("   ℹ️ Device already registered")
                return True
            else:
                print(f"   ❌ Registration failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def test_check_server(self):
        """Test check_server API - core sync functionality"""
        print("🔄 Testing check_server API...")
        
        url = f"{self.server_url}/scheduling/api/v1/device/check_server/"
        data = {
            "action": "check_server",
            "device_id": self.device_id,
            "last_sync_hash": self.last_sync_hash,
            "app_version": "1.0.0",
            "firmware_version": "12",
            "battery_level": 85,
            "storage_free_mb": 2048,
            "connection_type": "wifi",
            "device_health": {
                "temperature_celsius": 38,
                "signal_strength": -45
            }
        }
        
        try:
            response = self.session.post(url, json=data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Server check successful")
                print(f"   📊 Device registered: {result.get('device_registered')}")
                print(f"   🔄 Needs sync: {result.get('needs_sync')}")
                
                if result.get('needs_sync') and 'sync_data' in result:
                    sync_data = result['sync_data']
                    print(f"   📦 Sync data received:")
                    print(f"      - Playlists: {len(sync_data.get('playlists', []))}")
                    print(f"      - Assets: {len(sync_data.get('assets', []))}")
                    
                    # Update local sync hash
                    self.last_sync_hash = result.get('new_sync_hash', '')
                    print(f"      - New sync hash: {self.last_sync_hash[:16]}...")
                
                if 'emergency_messages' in result:
                    print(f"   🚨 Emergency messages: {len(result['emergency_messages'])}")
                
                if 'system_commands' in result:
                    print(f"   ⚙️ System commands: {len(result['system_commands'])}")
                
                return True
            else:
                print(f"   ❌ Check server failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def test_sync_confirmation(self):
        """Test sync confirmation API"""
        print("✅ Testing sync confirmation...")
        
        url = f"{self.server_url}/scheduling/api/v1/device/sync_confirmation/"
        data = {
            "device_id": self.device_id,
            "sync_hash": self.last_sync_hash,
            "sync_stats": {
                "assets_downloaded": 3,
                "bytes_transferred": 15728640,
                "duration_seconds": 45
            }
        }
        
        try:
            response = self.session.post(url, json=data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Sync confirmation sent")
                return True
            else:
                print(f"   ❌ Sync confirmation failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def test_log_sending(self):
        """Test device log sending"""
        print("📝 Testing log sending...")
        
        # Test single log
        url = f"{self.server_url}/players/api/logs/single/"
        data = {
            "device_id": self.device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "category": "SYNC",
            "tag": "APITester",
            "message": "API test log message",
            "app_version": "1.0.0"
        }
        
        try:
            response = self.session.post(url, json=data)
            print(f"   Single log - Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Single log sent successfully")
            else:
                print(f"   ❌ Single log failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Single log error: {e}")
        
        # Test batch logs
        url = f"{self.server_url}/players/api/logs/batch/"
        batch_data = {
            "device_id": self.device_id,
            "app_version": "1.0.0",
            "logs": [
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": "INFO",
                    "category": "APP",
                    "tag": "APITester",
                    "message": "Batch log message 1"
                },
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": "WARN",
                    "category": "NETWORK",
                    "tag": "APITester",
                    "message": "Batch log message 2"
                }
            ],
            "device_context": {
                "battery_level": 85,
                "memory_available_mb": 1024
            }
        }
        
        try:
            response = self.session.post(url, json=batch_data)
            print(f"   Batch logs - Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Batch logs sent: {result.get('created_logs')} logs")
            else:
                print(f"   ❌ Batch logs failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Batch logs error: {e}")
    
    def simulate_device_lifecycle(self):
        """Simulate complete device lifecycle"""
        print("🎭 Simulating complete device lifecycle...\n")
        
        # 1. Register device
        if not self.test_device_registration():
            print("❌ Cannot continue without device registration")
            return False
        
        print()
        
        # 2. Initial sync check
        if not self.test_check_server():
            print("❌ Initial sync check failed")
            return False
        
        print()
        
        # 3. Send sync confirmation
        if self.last_sync_hash:
            self.test_sync_confirmation()
            print()
        
        # 4. Send some logs
        self.test_log_sending()
        print()
        
        # 5. Simulate periodic sync checks
        print("🔁 Simulating periodic sync checks...")
        for i in range(3):
            print(f"   Check #{i+1}...")
            self.test_check_server()
            time.sleep(2)
        
        print("\n✅ Device lifecycle simulation completed!")
        return True
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting PiSignage API Tests")
        print("=" * 50)
        print(f"Server: {self.server_url}")
        print(f"Device ID: {self.device_id}")
        print("=" * 50)
        print()
        
        success = self.simulate_device_lifecycle()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 All tests completed successfully!")
            print("\n💡 Next steps:")
            print("   • Check device logs at: http://localhost:8000/players/A1B2C3D4E5F6G7H8/logs/")
            print("   • View device in admin: http://localhost:8000/admin/players/player/")
            print("   • Upload assets and create playlists")
        else:
            print("❌ Some tests failed. Check server logs.")
        print("=" * 50)


def main():
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    else:
        server_url = "http://localhost:8000"
    
    tester = PiSignageAPITester(server_url)
    tester.run_all_tests()


if __name__ == "__main__":
    main()