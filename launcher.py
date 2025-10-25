#!/usr/bin/env python3
"""
Cross-platform launcher for AI-System-DocAI V5I
Handles venv setup, dependency installation, and application launch
"""
import sys
import os
import subprocess
import platform
from pathlib import Path
import time

APP_NAME = "AI-System-DocAI"
APP_VERSION = "5I.2025"
MIN_PYTHON_VERSION = (3, 8)

def check_python_version():
    """Check if Python version meets requirements"""
    if sys.version_info < MIN_PYTHON_VERSION:
        print(f"❌ Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ required")
        print(f"   Current version: {sys.version}")
        return False
    return True

def get_venv_path():
    """Get virtual environment path"""
    return Path(__file__).parent / ".venv"

def get_venv_python():
    """Get path to Python executable in venv"""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def check_venv_exists():
    """Check if virtual environment exists"""
    python_path = get_venv_python()
    return python_path.exists()

def create_venv():
    """Create virtual environment"""
    print(f"📦 Creating virtual environment...")
    venv_path = get_venv_path()
    
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True
        )
        print("✅ Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_dependencies():
    """Install dependencies from requirements.txt"""
    print(f"📥 Installing dependencies...")
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"⚠️ requirements.txt not found")
        return False
    
    python_path = get_venv_python()
    
    try:
        subprocess.run(
            [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True
        )
        
        subprocess.run(
            [str(python_path), "-m", "pip", "install", "-r", str(requirements_file)],
            check=True
        )
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_disk_space():
    """Check available disk space"""
    try:
        import psutil
        disk = psutil.disk_usage(Path(__file__).parent)
        free_gb = disk.free / (1024**3)
        if free_gb < 2:
            print(f"⚠️ Low disk space: {free_gb:.1f} GB available")
            return False
        return True
    except Exception:
        return True  # Continue even if check fails

def setup_logging():
    """Setup logging directory"""
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    startup_log = logs_dir / f"{APP_NAME}_Startup.log"
    with open(startup_log, 'a', encoding='utf-8') as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n{'='*80}\n")
        f.write(f"{APP_NAME} V{APP_VERSION} - Launcher Started\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Platform: {platform.system()} {platform.version()}\n")
        f.write(f"Python: {sys.version}\n")
        f.write(f"{'='*80}\n\n")

def launch_application():
    """Launch the main application"""
    print(f"🚀 Launching {APP_NAME}...")
    
    python_path = get_venv_python()
    main_script = Path(__file__).parent / "main.py"
    
    if not main_script.exists():
        print(f"❌ main.py not found")
        return False
    
    try:
        # Run the application
        result = subprocess.run(
            [str(python_path), str(main_script)],
            check=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to launch application: {e}")
        return False

def main():
    """Main launcher function"""
    print(f"{'='*60}")
    print(f"{APP_NAME} V{APP_VERSION} - Launcher")
    print(f"{'='*60}\n")
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        return 1
    
    # Setup logging
    setup_logging()
    
    # Check disk space
    check_disk_space()
    
    # Check or create virtual environment
    if not check_venv_exists():
        print(f"Virtual environment not found")
        if not create_venv():
            input("Press Enter to exit...")
            return 1
        
        # Install dependencies
        if not install_dependencies():
            input("Press Enter to exit...")
            return 1
    else:
        print(f"✅ Virtual environment found")
    
    # Launch application
    if not launch_application():
        input("Press Enter to exit...")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

