# DeepFace Local Integration Setup

## Overview
This project now uses a locally-cloned version of the DeepFace library from the official repository: https://github.com/serengil/deepface.git

## Features of Local DeepFace
✅ Latest face detection algorithms
✅ Multiple detection backends: RetinaFace, MTCNN, MediaPipe, YuloV8
✅ Comprehensive emotion detection
✅ Better model accuracy and performance
✅ Custom modifications support

## Project Structure
```
emotion-detection-main/
├── deepface/                 # Local cloned DeepFace repository
│   ├── deepface/            # Main package
│   ├── requirements.txt      # DeepFace dependencies
│   ├── setup.py
│   └── ... (other files)
├── detections/
│   ├── image_detection.py   # Uses local deepface
│   ├── video_detection.py   # Uses local deepface
│   └── detection.py
└── app.py                    # Flask app with local deepface path
```

## Installation & Setup

### 1. Install DeepFace Dependencies
```bash
# First, install the base requirements
pip install -r requirements.txt

# Then install additional optional models/backends
pip install -r deepface/requirements_additional.txt
```

### 2. Important Dependencies for Local DeepFace
The following are critical for the cloned DeepFace to work:
- **opencv-python** >= 4.5.5.64 ✓
- **tensorflow** >= 1.9.0 ✓
- **keras** >= 2.2.0 ✓
- **torch** >= 2.1.2 (optional but recommended)
- **mediapipe** >= 0.8.7.3 (for alternative detection)
- **retina-face** >= 0.0.14 ✓
- **mtcnn** >= 0.1.0 ✓
- **pillow** >= 5.2.0 ✓
- **numpy** >= 1.14.0 ✓

### 3. Verify Installation
```python
# Test if local deepface is properly imported
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deepface'))
from deepface import DeepFace

# Try a simple analyze
from PIL import Image
import numpy as np
img = np.zeros((224, 224, 3), dtype=np.uint8)
result = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)
print("✅ DeepFace working locally!")
```

## How It Works in the Application

### Image Detection Flow
```
User Upload/Camera Capture
    ↓
Frontend sends to /image_upload
    ↓
image_detection.py (uses local DeepFace)
    ↓
DeepFace.analyze() with:
    - detector_backend='retinaface' (or auto-selected)
    - actions=['emotion']
    - enforce_detection=False (handles various angles/lighting)
    ↓
Returns emotion scores + Groq AI analysis
    ↓
Frontend displays results with confidence scores
```

### Supported Detector Backends (from local DeepFace)
1. **retinaface** (default) - Most accurate, recommended
2. **mtcnn** - Good balance of speed/accuracy  
3. **mediapipe** - Lightweight, faster
4. **yolov8** - Latest object detection
5. **yolov5** - Fast and reliable
6. **dlib** - Classic approach

## Emotion Detection Models
The local DeepFace provides:
- **VGGFace2** - High accuracy face embeddings
- **Facenet** - State-of-the-art face verification
- **OpenFace** - Open-source alternative
- **DeepID** - Alternative embedding

## Configuration in Application

### app.py
```python
# Local deepface is automatically in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deepface'))
from deepface import DeepFace
```

### image_detection.py & video_detection.py
```python
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'deepface'))
from deepface import DeepFace

# Usage
result = DeepFace.analyze(
    image, 
    actions=['emotion'], 
    detector_backend='retinaface',
    enforce_detection=False,
    silent=True
)
```

## Performance Tips

1. **GPU Support**: If you have CUDA-enabled GPU, ensure tensorflow/torch use it
   ```python
   import tensorflow as tf
   print(tf.config.list_physical_devices('GPU'))
   ```

2. **Batch Processing**: For multiple images, use batch operations
3. **Model Caching**: Models are cached after first load
4. **Detector Selection**: 
   - Use `retinaface` for best accuracy
   - Use `mediapipe` for faster processing

## Troubleshooting

### Issue: ModuleNotFoundError: No module named 'deepface'
**Solution**: Ensure sys.path is correctly set in the import section
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deepface'))
```

### Issue: Model download fails
**Solution**: Models are auto-downloaded on first use. Check internet connection and ensure write permissions in temp directory

### Issue: Low accuracy emotion detection
**Solution**: 
- Use `enforce_detection=False` for better coverage
- Check image quality and lighting
- Use `detector_backend='retinaface'` for best results

### Issue: Performance is slow
**Solution**:
- Use MediaPipe detector: `detector_backend='mediapipe'`
- Enable GPU acceleration
- Process in batches

## Updating DeepFace

To update to the latest DeepFace versions:
```bash
cd deepface
git pull origin master
```

## Repository Info
- **GitHub**: https://github.com/serengil/deepface
- **Documentation**: https://github.com/serengil/deepface/wiki
- **License**: MIT
- **Author**: Sefik Ilkin Serengil

## Next Steps
1. ✅ Run `pip install -r requirements.txt` if not done
2. ✅ Test emotion detection in browser
3. Optional: Install additional models from `requirements_additional.txt`
4. Optional: Configure specific detector backend in app config
