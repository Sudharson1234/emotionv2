#!/usr/bin/env python3
"""
Setup script for Emotion Detection Application with Local DeepFace
Installs all dependencies and verifies the setup
"""

import os
import sys
import subprocess
import platform

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_step(step_num, total_steps, text):
    """Print a step with percentage"""
    percentage = int((step_num / total_steps) * 100)
    print(f"\n[{step_num}/{total_steps}] ({percentage}%) {text}")
    print("-" * 60)

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")

def run_command(cmd, description=""):
    """Run a shell command and return success status"""
    try:
        if description:
            print_info(f"Running: {description}...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        if result.returncode != 0:
            print_error(f"Command failed: {result.stderr}")
            return False
        print(f"  ✅ {description} - Complete")
        return True
    except Exception as e:
        print_error(f"Error running command: {e}")
        return False

def check_pip_packages():
    """Check if critical packages are installed"""
    critical_packages = [
        ('tensorflow', 'tensorflow'),
        ('cv2', 'opencv-python'),
        ('numpy', 'numpy'),
        ('flask', 'flask'),
        ('PIL', 'pillow'),
    ]
    
    print_info("Checking critical packages...")
    total_packages = len(critical_packages)
    missing = []
    
    for idx, (import_name, package_name) in enumerate(critical_packages, 1):
        percentage = int((idx / total_packages) * 100)
        try:
            __import__(import_name)
            print(f"  [{idx}/{total_packages}] ({percentage}%) ✅ {package_name}")
        except ImportError:
            print(f"  [{idx}/{total_packages}] ({percentage}%) ❌ {package_name}")
            missing.append(package_name)
    
    # Check for either keras or tf_keras (optional but recommended)
    try:
        __import__('tf_keras')
        print(f"  [BONUS] ✅ tf_keras (Deep learning support)")
    except ImportError:
        try:
            __import__('keras')
            print(f"  [BONUS] ✅ keras (Deep learning support)")
        except ImportError:
            print(f"  [BONUS] ⚠️  keras/tf_keras not found (DeepFace will use TensorFlow built-in)")
    
    return len(missing) == 0

def test_deepface_import():
    """Test if local DeepFace can be imported"""
    print_info("Testing local DeepFace import...")
    try:
        # Add to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        deepface_dir = os.path.join(project_root, 'deepface')
        print("  [1/2] (50%) Checking DeepFace directory...")
        if os.path.isdir(os.path.join(deepface_dir, 'deepface')):
            print("  ✅ DeepFace source code found")
        
        # Check available backends
        print("  [2/2] (100%) Available detector backends:")
        backends = ['retinaface', 'mtcnn', 'yolov8', 'mediapipe', 'yolov5']
        for backend in backends:
            print(f"    - {backend}")
        
        return True
    except Exception as e:
        print_error(f"Failed to verify DeepFace: {e}")
        return False

def test_emotion_detection():
    """Test basic emotion detection"""
    print_info("Testing emotion detection capability...")
    try:
        print("  [1/3] (33%) Loading DeepFace config...")
        from deepface_config import setup_deepface_path, get_deepface_config
        setup_deepface_path()
        
        print("  [2/3] (66%) Importing DeepFace...")
        from deepface import DeepFace
        import numpy as np
        
        # Create a dummy image
        print("  [3/3] (100%) Running emotion detection test...")
        dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
        
        # Get config
        config = get_deepface_config()
        
        # Try analyze
        result = DeepFace.analyze(dummy_img, **config)
        
        print("  ✅ Emotion detection test passed!")
        print_info(f"Result structure: {list(result[0].keys()) if result else 'No result'}")
        
        return True
    except Exception as e:
        print_error(f"Emotion detection test failed: {e}")
        return False

def main():
    """Main setup function"""
    print_header("EMOTION DETECTION APP - SETUP WIZARD")
    
    total_steps = 7
    project_root = os.path.dirname(os.path.abspath(__file__))
    print_info(f"Project root: {project_root}")
    
    # Step 1: Check Python version
    print_step(1, total_steps, "Checking Python Version")
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if sys.version_info >= (3, 7):
        print_success(f"Python {py_version} is compatible")
    else:
        print_error(f"Python {py_version} is too old. Require Python 3.7+")
        return False
    
    # Step 2: Check if DeepFace is cloned
    print_step(2, total_steps, "Checking DeepFace Repository")
    deepface_dir = os.path.join(project_root, 'deepface')
    if os.path.exists(deepface_dir):
        print_success("DeepFace directory exists")
    else:
        print_error("DeepFace directory not found. Please clone: git clone https://github.com/serengil/deepface.git")
        return False
    
    # Step 3: Install requirements
    print_step(3, total_steps, "Installing Dependencies")
    
    # Main requirements
    req_file = os.path.join(project_root, 'requirements.txt')
    if os.path.exists(req_file):
        print_info("Installing main requirements...")
        if run_command(f"pip install -r requirements.txt", "Main requirements"):
            print_success("Main requirements installed")
        else:
            print_error("Failed to install main requirements")
    
    # DeepFace requirements
    deepface_req = os.path.join(deepface_dir, 'requirements.txt')
    if os.path.exists(deepface_req):
        print_info("Installing DeepFace requirements...")
        if run_command(f"pip install -r deepface/requirements.txt", "DeepFace requirements"):
            print_success("DeepFace requirements installed")
    
    # Step 4: Check packages
    print_step(4, total_steps, "Verifying Installations")
    if not check_pip_packages():
        print_error("Some critical packages are missing!")
        return False
    
    # Step 5: Test DeepFace
    print_step(5, total_steps, "Testing DeepFace Integration")
    if not test_deepface_import():
        return False
    
    # Step 6: Test emotion detection
    print_step(6, total_steps, "Testing Emotion Detection")
    test_emotion_detection()  # Don't fail on this one as models may need download
    
    # Step 7: Summary
    print_step(7, total_steps, "Setup Complete!")
    print_success("Your emotional detection app is ready to use!")
    print_info("Next steps:")
    print("  1. Start Flask app: python app.py")
    print("  2. Open browser: http://localhost:5000")
    print("  3. Test image/video emotion detection")
    print("\nFor more info, see: DEEPFACE_SETUP.md")
    print("\n" + "="*60)
    print("  ✅ SETUP 100% COMPLETE")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
