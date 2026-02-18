import base64
import numpy as np
import os
import sys
from io import BytesIO
from PIL import Image
from flask import request
from groq import Groq
import logging
from dotenv import load_dotenv

# Setup local DeepFace path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from deepface_config import setup_deepface_path, get_deepface_config
setup_deepface_path()

from deepface import DeepFace

# Load environment variables
load_dotenv()

# Global Groq client
groq_client = None

# Emotion confidence threshold - if below this, mark as uncertain
CONFIDENCE_THRESHOLD = 0.35

def get_groq_client():
    global groq_client
    if groq_client:
        return groq_client
    
    api_key = os.getenv('GROQ_API_KEY')
    if api_key:
        try:
            groq_client = Groq(api_key=api_key)
            return groq_client
        except Exception as e:
            logging.error(f"Failed to initialize Groq client: {e}")
    return None

def generate_face_analysis(emotion, confidence_score, emotion_dict=None, is_ambiguous=False):
    """Generate AI-powered insights for detected face emotion using Groq"""
    client = get_groq_client()
    if not client:
        return None
    
    try:
        # Build emotion context
        emotion_context = f"Detected Emotion: {emotion}\nConfidence Score: {confidence_score*100:.1f}%"
        
        if emotion_dict and is_ambiguous:
            # List other similar emotions
            sorted_emotions = sorted(emotion_dict.items(), key=lambda x: x[1], reverse=True)
            emotion_context += "\n\nOther detected emotions (may be ambiguous):"
            for i, (emo, score) in enumerate(sorted_emotions[1:4], 1):  # Top 3 alternatives
                emotion_context += f"\n{i}. {emo}: {score:.1f}%"
        
        ambiguity_note = "\n⚠️ Note: The detection shows signs of ambiguity between multiple emotions. Consider the context and other cues." if is_ambiguous else ""
        
        prompt = f"""Analyze the following detected face emotion and provide comprehensive insights.

{emotion_context}
{ambiguity_note}

Provide a detailed analysis including:
1. What this emotion indicates about the person's emotional state
2. Potential triggers or causes for this emotion
3. Recommended responses or support that could help
4. Any notable patterns or characteristics of this emotion

Keep the response concise but insightful (2-3 paragraphs)."""

        chat_completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert in emotional psychology and facial expression analysis. Provide insightful, empathetic analysis of detected emotions. If the detection shows ambiguity, acknowledge it."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error generating face analysis: {e}")
        return None

def process_image(file=None):
    try:
        if file:  # If file is uploaded
            image = Image.open(file)
        else:  # If Base64 image is sent (from Camera)
            data = request.json["image_base64"]
            image_data = base64.b64decode(data.split(",")[1])
            image = Image.open(BytesIO(image_data))

        # Convert image to NumPy array for DeepFace
        image_np = np.array(image)

        # Encode image properly for frontend
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Perform Emotion Detection with better model parameters
        # Using enforce_detection=False to handle various lighting/angles
        try:
            result = DeepFace.analyze(
                image_np, 
                actions=['emotion'], 
                enforce_detection=False,
                silent=True  # Suppress verbose logging
            )
        except Exception as detection_error:
            logging.warning(f"DeepFace detection error: {detection_error}")
            result = None

        # Check if any faces were detected
        if not result or len(result) == 0:
            logging.warning("No faces detected in the image")
            return {
                "error": "No faces detected",
                "message": "No faces detected in the image. Please try with a clearer photo showing a face.",
                "image_base64": f"data:image/jpeg;base64,{img_str}",
                "faces_detected": 0,
                "success": False
            }

        # Process detected faces
        faces_data = []
        for face_result in result:
            # Convert numpy float32 values to native Python floats for JSON serialization
            emotion_dict = {k: float(v) for k, v in face_result['emotion'].items()}
            detected_emotion = face_result['dominant_emotion']
            confidence = emotion_dict.get(detected_emotion, 0) / 100  # Normalize to 0-1

            # Sort emotions by confidence
            sorted_emotions = sorted(emotion_dict.items(), key=lambda x: x[1], reverse=True)
            
            # Check for ambiguity
            is_ambiguous = False
            ambiguity_note = ""
            if len(sorted_emotions) >= 2:
                top_score = sorted_emotions[0][1]
                second_score = sorted_emotions[1][1]
                if (top_score - second_score) < 15:
                    is_ambiguous = True
                    ambiguity_note = f" (also shows {sorted_emotions[1][0]})"

            face_data = {
                "emotion": detected_emotion,
                "dominant_emotion": detected_emotion,  # For frontend compatibility
                "confidence": round(confidence, 4),
                "confidence_percentage": round(confidence * 100, 2),
                "emotion_scores": emotion_dict,
                "all_emotions": [
                    {
                        "label": emotion,
                        "score": round(score / 100, 4),
                        "percentage": round(score, 2)
                    }
                    for emotion, score in emotion_dict.items()
                ],
                "is_ambiguous": is_ambiguous,
                "ambiguity_note": ambiguity_note
            }
            faces_data.append(face_data)

        # Get primary emotion (from first detected face)
        primary_face = faces_data[0]

        # Prepare response
        response = {
            "success": True,
            "emotion": primary_face["emotion"],
            "confidence": primary_face["confidence"],
            "confidence_percentage": primary_face["confidence_percentage"],
            "image_base64": f"data:image/jpeg;base64,{img_str}",
            "faces": faces_data,
            "faces_detected": len(faces_data),
            "emotion_scores": primary_face["emotion_scores"],
            "all_emotions": primary_face["all_emotions"],
            "is_ambiguous": primary_face["is_ambiguous"],
            "ambiguity_note": primary_face["ambiguity_note"]
        }

        # Generate AI-powered analysis
        analysis = generate_face_analysis(
            primary_face["emotion"], 
            primary_face["confidence"], 
            primary_face["emotion_scores"], 
            primary_face["is_ambiguous"]
        )
        if analysis:
            response["analysis_report"] = analysis
            response["model_used"] = "groq-llama-3.1-8b-instant + deepface-vggface2"
        else:
            response["model_used"] = "deepface-vggface2"

        # Generate intensity description
        confidence = primary_face["confidence"]
        if confidence >= 0.8:
            intensity = f"Very Strong - {(confidence*100):.1f}% confidence"
        elif confidence >= 0.6:
            intensity = f"Strong - {(confidence*100):.1f}% confidence"
        elif confidence >= 0.4:
            intensity = f"Moderate - {(confidence*100):.1f}% confidence"
        else:
            intensity = f"Weak/Ambiguous - {(confidence*100):.1f}% confidence"
        
        if primary_face["is_ambiguous"]:
            intensity += " (⚠️ Multiple emotions detected)"
        
        response["emotional_intensity"] = intensity

        logging.info(f"Emotion detected: {primary_face['emotion']} with confidence {(primary_face['confidence']*100):.1f}% in {len(faces_data)} face(s)")
        return response
    
    except Exception as e:
        logging.error(f"Image processing error: {str(e)}")
        return {
            "error": str(e),
            "message": "Failed to process image. Please try again with a different image.",
            "success": False
        }

