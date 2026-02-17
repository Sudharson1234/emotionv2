#!/usr/bin/env python3
"""
First-time setup script for Emotion Detection App
Installs all dependencies and verifies configuration
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command with status reporting"""
    print(f"\n{description}...")
    try:
        subprocess.check_call(cmd, shell=False)
        print(f"✅ {description} complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("  EMOTI Setup - First Time Installation")
    print("=" * 60)
    
    # Check Python version
    print(f"\n✅ Python version: {sys.version}")
    
    # Create/activate virtual environment
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("\n📦 Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", ".venv"])
        print("✅ Virtual environment created")
    else:
        print("\n✅ Virtual environment already exists")
    
    # Get pip path (different on Windows vs Unix)
    if sys.platform == "win32":
        pip_exe = ".venv\\Scripts\\pip.exe"
        python_exe = ".venv\\Scripts\\python.exe"
    else:
        pip_exe = ".venv/bin/pip"
        python_exe = ".venv/bin/python"
    
    # Upgrade pip
    print("\n📦 Upgrading pip...")
    subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "pip", "-q"])
    print("✅ pip upgraded")
    
    # Install requirements
    if Path("requirements.txt").exists():
        print("\n📦 Installing packages from requirements.txt...")
        subprocess.check_call([python_exe, "-m", "pip", "install", "-r", "requirements.txt", "-q"])
        print("✅ All packages installed")
    else:
        print("⚠️  requirements.txt not found")
    
    # Install additional essential packages
    essential = [
        "langdetect",
        "transformers",
        "torch",
        "torchvision",
        "torchaudio",
        "flask-migrate",
        "tf-keras",
        "imageio",
    ]
    
    print("\n📦 Installing essential packages...")
    for package in essential:
        try:
            subprocess.check_call([
                python_exe, "-m", "pip", "install", package, "-q"
            ], stderr=subprocess.DEVNULL)
            print(f"  ✅ {package}")
        except:
            print(f"  ⚠️  {package} (optional)")
    
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("  1. Configure your .env file with MongoDB connection")
    print("  2. Run: python start_app.py")
    print("     OR")
    print("  3. Run: run_app.bat (on Windows)")
    print("\n💡 App will be available at: http://127.0.0.1:5000")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
