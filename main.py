#!/usr/bin/env python3
"""
AI-System-DocAI V5I - Enterprise Edition
Main application entry point
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Force CPU-only mode globally
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

def main():
    """Main entry point"""
    try:
        # Import UI after path setup
        from ui import main as ui_main
        
        # Run the application
        return ui_main()
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("\nPlease ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

