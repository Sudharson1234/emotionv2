#!/usr/bin/env python
"""
EMOTI - Emotion Detection AI Chat Launcher
Python version for cross-platform compatibility
"""

import sys
import os
import subprocess
import time

def main():
    print("\n" + "="*60)
    print("     EMOTI - Emotion Detection AI Chat")
    print("="*60 + "\n")
    
    # Define paths
    python_path = r"c:\project backup code\.venv\Scripts\python.exe"
    app_dir = r"c:\project backup code\emotion-detection-main"
    
    # Verify Python exists
    if not os.path.exists(python_path):
        print(f"❌ ERROR: Python not found at:\n   {python_path}")
        print("\nPlease ensure the virtual environment is set up correctly.")
        input("Press Enter to exit...")
        return 1
    
    print(f"✓ Python: {python_path}")
    
    # Verify app.py exists
    app_file = os.path.join(app_dir, "app.py")
    if not os.path.exists(app_file):
        print(f"❌ ERROR: app.py not found at:\n   {app_file}")
        input("Press Enter to exit...")
        return 1
    
    print(f"✓ App: {app_file}")
    
    # Change to app directory
    os.chdir(app_dir)
    print(f"✓ Directory: {os.getcwd()}")
    print()
    
    # Verify langdetect
    print("Checking dependencies...")
    try:
        subprocess.run(
            [python_path, "-c", "import langdetect"],
            capture_output=True,
            timeout=5,
            check=True
        )
        print("  ✓ All dependencies ready")
    except subprocess.CalledProcessError:
        print("  Installing langdetect...")
        subprocess.run(
            [python_path, "-m", "pip", "install", "langdetect", "-q"],
            capture_output=True,
            timeout=30
        )
    
    print("\n" + "="*60)
    print("Starting Flask Server...")
    print("="*60)
    print("\nServer running on: http://127.0.0.1:5000")
    print("\nTo STOP the server, press: CTRL + C\n")
    print("="*60 + "\n")
    
    # Start the app
    try:
        subprocess.run([python_path, "app.py"])
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Fatal error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
