#!/usr/bin/env python3
"""
AI-System-DocAI - Model Download Script
Downloads and caches embedding models for offline use
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
    """Download embedding model"""
    try:
        from embeddings import download_model

        print("🔄 AI-System-DocAI - Model Download")
        print("=" * 40)

        success = download_model()

        if success:
            print("\n🎉 Model downloaded successfully!")
            print("You can now index documents without network issues.")
            return 0
        else:
            print("\n❌ Failed to download model.")
            print("Please check your internet connection and try again.")
            return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

