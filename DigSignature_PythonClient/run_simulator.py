#!/usr/bin/env python3
"""
Launch script for PiSignage Device Simulator
Handles dependencies and provides easy startup
"""

import sys
import os
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        ('PyQt6', 'PyQt6'),
        ('requests', 'requests'),
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name} is installed")
        except ImportError:
            print(f"❌ {package_name} is not installed")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n📦 Missing packages: {', '.join(missing_packages)}")
        print("   Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True


def install_dependencies():
    """Install required dependencies"""
    print("🔧 Installing dependencies...")
    
    packages = ["PyQt6", "requests"]
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ])
        
        subprocess.check_call([
            sys.executable, "-m", "pip", "install"
        ] + packages)
        
        print("✅ Dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_sample_assets():
    """Create sample assets for testing"""
    assets_dir = Path("sample_assets")
    assets_dir.mkdir(exist_ok=True)
    
    # Create a sample text file that can be used as placeholder
    readme_file = assets_dir / "README.txt"
    if not readme_file.exists():
        with open(readme_file, 'w') as f:
            f.write("""
PiSignage Simulator Sample Assets

This directory is for sample media files for testing.

Supported formats:
- Videos: MP4, AVI, MOV, MKV
- Images: JPG, PNG, GIF, BMP
- Audio: MP3, WAV, AAC

To test the simulator:
1. Add some sample video/image files to this directory
2. Upload them to your Django server via admin
3. Create playlists in the Django admin
4. The simulator will automatically download and play them

Note: The simulator creates its own download directories:
- simulator_assets_[device_id]/
- These are automatically managed by the simulator
""")
    
    print(f"📁 Sample assets directory: {assets_dir.absolute()}")


def print_banner():
    """Print application banner"""
    banner = """
██████╗ ██╗███████╗██╗ ██████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗
██╔══██╗██║██╔════╝██║██╔════╝ ████╗  ██║██╔══██╗██╔════╝ ██╔════╝
██████╔╝██║███████╗██║██║  ███╗██╔██╗ ██║███████║██║  ███╗█████╗  
██╔═══╝ ██║╚════██║██║██║   ██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  
██║     ██║███████║██║╚██████╔╝██║ ╚████║██║  ██║╚██████╔╝███████╗
╚═╝     ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝

PyQt6 Device Simulator - Django Port Testing Tool
    """
    print(banner)


def print_usage_info():
    """Print usage information"""
    info = """
🚀 PiSignage Device Simulator

This simulator mimics Android device behavior for testing your Django server.

📋 Features:
  • Device registration and sync simulation
  • Video/image playback with layout support
  • Real-time log sending to server
  • Multiple device simulation
  • Network condition simulation
  • Health monitoring simulation

🎮 Controls:
  • Configure device settings in the control panel
  • Start/stop simulation
  • Manual sync and log sending
  • Fullscreen media display
  • Multiple simulator windows

🔧 Setup:
  1. Make sure your Django server is running on http://localhost:8000
  2. Upload some assets (videos/images) via Django admin
  3. Create playlists and assign them to groups
  4. Start the simulator and watch it sync!

📁 Directories:
  • simulator_assets_[device_id]/  - Downloaded assets
  • simulator_configs/             - Saved device configurations
  • sample_assets/                 - Sample media for upload

🌐 Server URLs:
  • Django Admin: http://localhost:8000/admin/
  • Player Logs: http://localhost:8000/players/[device_id]/logs/
  • API Docs: http://localhost:8000/api/docs/ (if available)
"""
    print(info)


def main():
    """Main entry point"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    print("\n🔍 Checking dependencies...")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❓ Would you like to install missing dependencies? (y/n): ", end="")
        
        try:
            response = input().lower().strip()
            if response in ['y', 'yes']:
                if not install_dependencies():
                    sys.exit(1)
            else:
                print("❌ Cannot run without required dependencies")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n❌ Installation cancelled")
            sys.exit(1)
    
    # Create sample assets directory
    create_sample_assets()
    
    # Import and run the application
    print("\n🚀 Starting PiSignage Device Simulator...")
    
    try:
        # Add current directory to Python path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        # Import the main application
        from main import main as run_app
        
        print_usage_info()
        
        # Run the application
        run_app()
        
    except ImportError as e:
        print(f"❌ Failed to import application modules: {e}")
        print("   Make sure all simulator files are in the same directory")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n👋 Simulator stopped by user")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
