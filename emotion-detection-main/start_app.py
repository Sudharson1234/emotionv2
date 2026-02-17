#!/usr/bin/env python3
"""
Comprehensive startup script for Emotion Detection App
Handles environment setup, dependency verification, and app launch
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def check_venv():
    """Check if virtual environment exists"""
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("❌ Virtual environment not found!")
        print("   Please create it with: python -m venv .venv")
        sys.exit(1)
    print("✅ Virtual environment found")
    return venv_path

def check_dependencies():
    """Verify all required packages are installed"""
    print_header("Checking Dependencies")
    
    required_packages = {
        'flask': 'Flask',
        'langdetect': 'langdetect',
        'transformers': 'transformers',
        'torch': 'torch',
        'pymongo': 'pymongo',
        'flask_pymongo': 'flask_pymongo',
        'flask_bcrypt': 'flask_bcrypt',
        'flask_cors': 'flask_cors',
        'flask_jwt_extended': 'flask_jwt_extended',
        'flask_migrate': 'flask_migrate',
        'groq': 'groq',
        'deep_translator': 'deep_translator',
        'textblob': 'textblob',
        'python_dotenv': 'python_dotenv',
    }
    
    missing = []
    for package, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing {len(missing)} packages. Installing...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', 
            '-q', *missing
        ])
        print("✅ All missing packages installed")
    
    return len(missing) == 0

def verify_app_structure():
    """Verify required files exist"""
    print_header("Verifying Project Structure")
    
    required_files = [
        'app.py',
        'models.py',
        'language_utils.py',
        'requirements.txt',
        'detections/detection.py',
        'templates/chat.html',
        'static/modern-theme.css',
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  {len(missing_files)} files missing!")
        return False
    
    return True

def load_environment():
    """Load environment variables from .env file"""
    from dotenv import load_dotenv
    
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file found and loaded")
        load_dotenv('.env')
    else:
        print("⚠️  .env file not found - using defaults")
    
    return True

def start_app():
    """Start the Flask application"""
    print_header("Starting Emotion Detection App")
    
    print("🚀 Launching Flask application...")
    print("📍 Running on: http://127.0.0.1:5000")
    print("🔧 Debug mode enabled (auto-reload on file changes)")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 60)
    
    try:
        # Import and run Flask app
        from app import app
        app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=True)
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("  Server stopped by user")
        print("=" * 60 + "\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting application: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main startup flow"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  💙  EMOTI - Emotion-Aware AI Chat  💙".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    print_header("Environment Setup")
    
    # Step 1: Check virtual environment
    print("1️⃣  Checking virtual environment...")
    check_venv()
    
    # Step 2: Check dependencies
    print("\n2️⃣  Verifying dependencies...")
    if not check_dependencies():
        print("⚠️  Some dependencies are missing")
    
    # Step 3: Verify project structure
    print("\n3️⃣  Verifying project structure...")
    if not verify_app_structure():
        print("❌ Project structure incomplete")
        sys.exit(1)
    
    # Step 4: Load environment
    print("\n4️⃣  Loading environment configuration...")
    load_environment()
    
    # Step 5: Start app
    print("\n5️⃣  Starting application...")
    start_app()

if __name__ == '__main__':
    main()
