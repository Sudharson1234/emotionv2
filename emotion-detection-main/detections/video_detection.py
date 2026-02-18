import os
import sys
import cv2
import imageio
import numpy as np
from collections import Counter
from werkzeug.utils import secure_filename
import logging

# Setup local DeepFace path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from deepface_config import setup_deepface_path, get_deepface_config
setup_deepface_path()

from deepface import DeepFace

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def analyze_frame(frame, frame_count=0):
    """Analyze a frame for emotion with detailed error logging"""
    try:
        # Ensure frame is in correct format
        if frame is None or frame.size == 0:
            logging.debug(f"Frame {frame_count}: Empty or None frame")
            return None
        
        # Convert to RGB if needed
        if len(frame.shape) == 3:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            frame_rgb = frame
        
        # Log frame info for debugging
        logging.debug(f"Frame {frame_count}: Shape={frame_rgb.shape}, dtype={frame_rgb.dtype}")
        
        # Analyze with DeepFace
        results = DeepFace.analyze(
            frame_rgb, 
            actions=['emotion'], 
            enforce_detection=False,
            silent=True
        )
        
        # Extract emotion from results
        if results and isinstance(results, list):
            if len(results) > 0:
                result = results[0]
                if "dominant_emotion" in result:
                    emotion = result["dominant_emotion"]
                    confidence = float(result.get("emotion", {}).get(emotion, 0)) / 100
                    logging.debug(f"Frame {frame_count}: Detected {emotion} ({confidence:.2%})")
                    return {
                        "emotion": emotion,
                        "confidence": confidence
                    }
                else:
                    logging.debug(f"Frame {frame_count}: Result has no 'dominant_emotion' key. Keys: {result.keys()}")
            else:
                logging.debug(f"Frame {frame_count}: Empty results list from DeepFace")
        else:
            logging.debug(f"Frame {frame_count}: Results is None or not a list: {type(results)}")
    
    except Exception as e:
        logging.debug(f"Frame {frame_count}: Error analyzing - {str(e)}")
    
    return None


def process_video(file, is_live_recording=False, frame_skip=5):
    """
    Process video file and detect emotions frame-by-frame.
    frame_skip=5 means analyze every 5th frame (faster processing)
    """
    try:
        filename = "recorded_video.webm" if is_live_recording else secure_filename(file.filename)
        video_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(video_path)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {
                "error": "Failed to open video file",
                "success": False
            }

        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        duration = total_frames / fps if fps > 0 else 0

        emotions_detected = []
        emotions_with_confidence = []
        frame_count = 0
        analyzed_frames = 0

        logging.info(f"Processing video: {total_frames} frames, {fps:.1f} FPS, {duration:.1f}s duration")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Analyze every Nth frame
            if frame_count % frame_skip == 0:
                analyzed_frames += 1
                detected = analyze_frame(frame, frame_count)
                
                if detected:
                    emotions_detected.append(detected["emotion"])
                    emotions_with_confidence.append({
                        "emotion": detected["emotion"],
                        "confidence": detected["confidence"],
                        "frame": frame_count,
                        "timestamp": frame_count / fps
                    })
                else:
                    if analyzed_frames <= 3:  # Log first few failures for debugging
                        logging.debug(f"No emotion detected in analyzed frame {frame_count}")

            frame_count += 1

        cap.release()

        # Check if any emotions were detected
        if not emotions_detected:
            logging.warning(f"No faces detected in video. Analyzed {analyzed_frames} frames out of {total_frames}")
            return {
                "error": "No faces detected in the video",
                "message": "No faces or emotions could be detected in the video. Try with a clearer video showing faces.",
                "frames_analyzed": analyzed_frames,
                "total_frames": total_frames,
                "success": False
            }

        # Calculate emotion distribution
        emotion_counts = Counter(emotions_detected)
        most_common_emotion = emotion_counts.most_common(1)[0][0]
        
        # Calculate confidence for dominant emotion
        dominant_emotion_data = [e for e in emotions_with_confidence if e["emotion"] == most_common_emotion]
        dominant_confidence = np.mean([e["confidence"] for e in dominant_emotion_data]) if dominant_emotion_data else 0

        # Prepare detailed response
        response = {
            "success": True,
            "dominant_emotion": most_common_emotion,
            "dominant_emotion_confidence": round(float(dominant_confidence), 4),
            "total_emotions_detected": len(emotions_detected),
            "frames_analyzed": analyzed_frames,
            "total_frames": total_frames,
            "video_duration": round(duration, 2),
            "emotion_distribution": dict(emotion_counts),
            "emotion_percentages": {
                emotion: round((count / len(emotions_detected)) * 100, 1)
                for emotion, count in emotion_counts.items()
            },
            "emotions_timeline": emotions_with_confidence[:50],  # Return first 50 detailed emotions
            "emotions": emotions_with_confidence,  # For frontend compatibility with more complete data
            "model_used": "deepface-vggface2 (frame-by-frame analysis)"
        }

        logging.info(f"Video analysis complete: {most_common_emotion} detected in {len(emotions_detected)}/{analyzed_frames} analyzed frames")
        return response

    except Exception as e:
        logging.error(f"Error processing video: {str(e)}")
        return {
            "error": str(e),
            "message": "Failed to process video. Please try again with a different video file.",
            "success": False
        }
