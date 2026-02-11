
import os
import sys
import cv2
import imageio
import numpy as np
from collections import Counter
from werkzeug.utils import secure_filename

# Setup local DeepFace path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from deepface_config import setup_deepface_path, get_deepface_config
setup_deepface_path()

from deepface import DeepFace

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER,exist_ok=True) #Ensure the Up;loadfolder exists

def analyze_frame(frame):
    try:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = DeepFace.analyze(frame_rgb, actions=['emotion'], detector_backend='retinaface', enforce_detection=False)
        
        if results and isinstance(results, list) and "dominant_emotion" in results[0]:
            return results[0]["dominant_emotion"]
    except Exception as e:
        print(f"⚠️ Error analyzing frame: {e}")
    
    return None


def process_video(file, is_live_recording=False, frame_skip=20):
    try:
        filename = "recorded_video.webm" if is_live_recording else secure_filename(file.filename)
        video_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(video_path)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": "Failed to open video file"}

        emotions_detected = []
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_skip == 0:
                detected_emotion = analyze_frame(frame)
                print(f"Frame {frame_count}: Detected Emotion -> {detected_emotion}")  # 🛑 Debugging line
                if detected_emotion:
                    emotions_detected.append(detected_emotion)

            frame_count += 1

        cap.release()

        if not emotions_detected:
            return {"error": "No faces detected in the video"}

        most_common_emotion = Counter(emotions_detected).most_common(1)[0][0]
        emotion_counts = dict(sorted(Counter(emotions_detected).items(), key=lambda x: x[1], reverse=True))
        return {
            "most_common_emotion": most_common_emotion,
            "emotion_counts": emotion_counts
        }

    except Exception as e:
        return {"error": f"Error processing video: {e}"}
