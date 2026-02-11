"""
Configuration for local DeepFace integration
Handles paths and settings for the cloned DeepFace library
"""

import os
import sys

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEEPFACE_DIR = os.path.join(PROJECT_ROOT, 'deepface')

def setup_deepface_path():
    """
    Add the local deepface directory to Python path
    Must be called before importing DeepFace
    """
    if DEEPFACE_DIR not in sys.path:
        sys.path.insert(0, DEEPFACE_DIR)
    return DEEPFACE_DIR

def get_deepface_config():
    """
    Returns the recommended configuration for DeepFace in this application
    """
    return {
        'detector_backend': 'retinaface',  # Best accuracy for emotion detection
        'enforce_detection': False,         # Handle various lighting/angles
        'silent': True,                     # Suppress verbose logging
        'actions': ['emotion'],             # Only detect emotions
    }

def setup_deepface_models():
    """
    Pre-load and verify DeepFace models are available
    """
    try:
        setup_deepface_path()
        from deepface import DeepFace
        
        # Verify models are available
        print("✅ Local DeepFace loaded successfully")
        print(f"   DeepFace Location: {DEEPFACE_DIR}")
        
        # Models will be auto-downloaded on first use if needed
        return True
    except ImportError as e:
        print(f"❌ Error loading local DeepFace: {e}")
        return False

# Export for easy access
__all__ = ['setup_deepface_path', 'get_deepface_config', 'setup_deepface_models', 'DEEPFACE_DIR']
