#!/usr/bin/env python3
import urllib.request
import os

models_dir = r'c:\project backup code\emotion-detection-main\static\models'

# Binary files to download from jsdelivr CDN
files_to_download = [
    ('tiny_face_detector_model.bin', 'https://cdn.jsdelivr.net/gh/vladmandic/face-api/model/tiny_face_detector_model.bin'),
    ('face_expression_model.bin', 'https://cdn.jsdelivr.net/gh/vladmandic/face-api/model/face_expression_model.bin'),
]

print('Downloading Face-API model weights...')

for filename, url in files_to_download:
    try:
        filepath = os.path.join(models_dir, filename)
        print(f'Downloading {filename}...', end=' ', flush=True)
        urllib.request.urlretrieve(url, filepath)
        size = os.path.getsize(filepath)
        print(f'✅ OK ({size} bytes)')
    except Exception as e:
        print(f'❌ ERROR: {e}')

# List all downloaded files
print('\nLocal models directory contents:')
if os.path.exists(models_dir):
    for f in os.listdir(models_dir):
        fpath = os.path.join(models_dir, f)
        size = os.path.getsize(fpath)
        print(f'  {f} ({size} bytes)')
