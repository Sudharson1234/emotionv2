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
        result = DeepFace.analyze(
            image_np, 
            actions=['emotion'], 
            enforce_detection=False,
            silent=True  # Suppress verbose logging
        )
        
        # Extract emotion data
        emotion_dict = result[0]['emotion']
        detected_emotion = result[0]['dominant_emotion']
        confidence = emotion_dict.get(detected_emotion, 0) / 100  # Normalize to 0-1

        # Sort emotions by confidence to check for ambiguity
        sorted_emotions = sorted(emotion_dict.items(), key=lambda x: x[1], reverse=True)
        
        # Check if detection is ambiguous (top 2 emotions are close)
        is_ambiguous = False
        ambiguity_note = ""
        if len(sorted_emotions) >= 2:
            top_score = sorted_emotions[0][1]
            second_score = sorted_emotions[1][1]
            # If top 2 emotions differ by less than 15%, it's ambiguous
            if (top_score - second_score) < 15:
                is_ambiguous = True
                ambiguity_note = f" (closely resembles {sorted_emotions[1][0]})"

        # Prepare response with enhanced data
        response = {
            "emotion": detected_emotion,
            "image_base64": f"data:image/jpeg;base64,{img_str}",
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

        # Generate AI-powered analysis with improved prompt
        analysis = generate_face_analysis(detected_emotion, confidence, emotion_dict, is_ambiguous)
        if analysis:
            response["analysis_report"] = analysis
            response["model_used"] = "groq-llama-3.1-8b-instant + deepface-vggface2"
        else:
            response["model_used"] = "deepface-vggface2"

        # Generate emotional intensity description with quality indicator
        if confidence >= 0.8:
            intensity = f"Very Strong - {(confidence*100):.1f}% confidence"
        elif confidence >= 0.6:
            intensity = f"Strong - {(confidence*100):.1f}% confidence"
        elif confidence >= 0.4:
            intensity = f"Moderate - {(confidence*100):.1f}% confidence"
        else:
            intensity = f"Weak/Ambiguous - {(confidence*100):.1f}% confidence"
        
        # Add quality indicator if ambiguous
        if is_ambiguous:
            intensity += " (⚠️ Multiple emotions detected)"
        
        response["emotional_intensity"] = intensity

        logging.info(f"Emotion detected: {detected_emotion} with confidence {confidence*100:.1f}%. Ambiguous: {is_ambiguous}")
        return response
    
    except Exception as e:
        logging.error(f"Image processing error: {str(e)}")
        return {"error": str(e)}

