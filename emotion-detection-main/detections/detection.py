import re
import os
import json
import logging
from transformers import pipeline
from nltk.corpus import words
from textblob import TextBlob
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client
groq_api_key = os.getenv('GROQ_API_KEY')
groq_client = None

def validate_groq_api_key(api_key):
    """Validate Groq API key format"""
    if not api_key:
        return False, "API key not found in .env"
    if len(api_key) < 20:
        return False, "API key appears too short"
    return True, "Valid format"

if groq_api_key:
    is_valid, msg = validate_groq_api_key(groq_api_key)
    if is_valid:
        try:
            groq_client = Groq(api_key=groq_api_key)
            logging.info(f"✓ Groq client initialized successfully with key: {groq_api_key[:20]}...")
        except Exception as e:
            logging.error(f"Failed to initialize Groq client: {e}")
    else:
        logging.warning(f"Groq API key validation failed: {msg}")
else:
    logging.warning("GROQ_API_KEY not found in environment variables")

# Fallback emotion pipeline
emotion_pipeline = pipeline("text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None)
valid_words=set(words.words())

def is_gibberish(text):
    if len(set(text))<=2:
        return True
    
    if re.match(r"^[^a-zA-Z\s]+$", text):  
        return True
    
    vowels = "aeiouAEIOU"
    vowel_count = sum(1 for char in text if char in vowels)
    if vowel_count < max(1, len(text) * 0.2):  
        return True  

    return False 

def is_meaningful(text):
    """Check if text has meaningful emotional content"""
    # Skip empty text
    if len(text.strip()) < 2:
        return False
    
    # Skip gibberish
    if is_gibberish(text):
        return False
    
    # If we get here, text seems meaningful
    return True


def detect_text_emotion(text):

    if not text.strip():
        return {"error": "Please enter a statement."}, 400  
    
    # Simplified meaningful check - just check for gibberish
    if is_gibberish(text):
        return {"error":"No Emotion Detected. Please enter a valid statement."},400
    
    # Try Groq first if available
    if groq_client:
        try:
            logging.info(f"Attempting Groq detection for text: {text[:50]}...")
            return detect_emotion_with_groq(text)
        except Exception as e:
            logging.warning(f"Groq API error: {e}. Using local model instead.")
    else:
        logging.info("Groq client not initialized. Using local model.")
    
    # Fallback to local model
    return detect_emotion_with_local_model(text)


def detect_emotion_with_groq(text):
    """
    Detect emotion using Groq API with detailed paragraph analysis
    """
    try:
        prompt = f"""Analyze the emotion in the following text and provide both structured data and detailed analysis.
Text: "{text}"

Respond with ONLY a valid JSON object (no markdown, no extra text) with this exact structure:
{{
    "Dominant_emotion": {{
        "label": "emotion_name",
        "score": confidence_score_0_to_1,
        "percentage": percentage_0_to_100
    }},
    "Emotion Analysis": [
        {{"label": "emotion1", "score": score1, "percentage": percent1}},
        {{"label": "emotion2", "score": score2, "percentage": percent2}},
        {{"label": "emotion3", "score": score3, "percentage": percent3}}
    ],
    "analysis_report": "Write a comprehensive 2-3 paragraph analysis that includes: (1) Identification of the dominant emotion and why it's present, (2) Explanation of secondary emotions and their contribution to overall sentiment, (3) Key phrases or words that trigger these emotions, (4) Overall sentiment summary and emotional intensity.",
    "key_indicators": ["List of 3-5 specific words or phrases that strongly indicate the dominant emotion"],
    "emotional_intensity": "Scale from 1-10 and brief explanation"
}}

Emotions can be: joy, sadness, anger, fear, disgust, surprise, neutral
"""
        
        chat_completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert emotion psychologist and text analyst. Provide detailed, insightful analysis. Respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1000
        )
        
        # Parse the response
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        try:
            emotion_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            import re as regex_module
            json_match = regex_module.search(r'\{.*\}', response_text, regex_module.DOTALL)
            if json_match:
                emotion_data = json.loads(json_match.group())
            else:
                raise ValueError("Invalid JSON response from Groq")
        
        # Validate response structure
        if "Dominant_emotion" in emotion_data and "Emotion Analysis" in emotion_data:
            # Check for neutral emotion threshold
            if emotion_data["Dominant_emotion"].get("label") == "neutral" and emotion_data["Dominant_emotion"].get("score", 0) > 0.95:
                return {"error": "No Emotion Detected."}, 400
            emotion_data["model_used"] = "groq-llama-3.3-70b-versatile"
            return emotion_data, 200
        else:
            raise ValueError("Invalid response structure from Groq")
            
    except Exception as e:
        logging.error(f"Groq detection error: {str(e)}")
        logging.error(f"Groq client status: {groq_client}")
        logging.error(f"API Key available: {bool(groq_api_key)}")
        # Re-raise to trigger fallback
        raise


def generate_analysis_report(text, emotions_data):
    """
    Generate detailed paragraph analysis report from emotion data
    """
    try:
        sorted_emotions = sorted(emotions_data, key=lambda x: x.get("score", 0), reverse=True)
        dominant = sorted_emotions[0] if sorted_emotions else {}
        secondary = sorted_emotions[1:3] if len(sorted_emotions) > 1 else []
        
        # Extract key words that might trigger emotions
        words = text.lower().split()
        key_indicators = [word for word in words if len(word) > 3][:5]
        
        # Determine emotional intensity
        dominant_score = dominant.get("score", 0)
        if dominant_score >= 0.75:
            intensity = "Very High (8-10/10)"
            intensity_num = 9
        elif dominant_score >= 0.5:
            intensity = "High (6-8/10)"
            intensity_num = 7
        elif dominant_score >= 0.3:
            intensity = "Moderate (4-6/10)"
            intensity_num = 5
        else:
            intensity = "Low (1-4/10)"
            intensity_num = 3
        
        # Build comprehensive analysis paragraph
        emotion_name = dominant.get("label", "unknown").capitalize()
        dominant_pct = round(dominant.get("score", 0) * 100, 2)
        
        paragraph1 = f"""The text exhibits a dominant emotion of {emotion_name} ({dominant_pct}%), which is evident throughout the linguistic choices and tone of the message. This emotion forms the primary emotional foundation of the utterance and reflects the speaker's core sentiment regarding their subject matter. The presence of {emotion_name} suggests specific psychological and emotional states that are conveyed through word choice, sentence structure, and overall narrative tone."""
        
        # Build secondary emotions paragraph
        if secondary:
            secondary_text = ", ".join([f"{s.get('label', 'unknown').capitalize()} ({round(s.get('score', 0) * 100, 2)}%)" for s in secondary])
            paragraph2 = f"""Contributing to the overall emotional landscape are secondary emotions including {secondary_text}. These emotions add nuance and complexity to the primary sentiment, suggesting a multi-layered emotional response. The interplay between the dominant {emotion_name} emotion and these secondary emotions creates a richer emotional narrative, indicating that the speaker's feelings are not monolithic but rather comprise several intertwined emotional dimensions that together form their complete emotional response."""
        else:
            paragraph2 = f"""The emotional expression is primarily focused on {emotion_name}, with minimal secondary emotional components. This suggests a concentrated, singular emotional focus where the speaker's sentiment is clearly aligned toward one dominant emotional state."""
        
        # Build key phrases paragraph
        phrase_list = ", ".join([f"'{word}'" for word in key_indicators[:4]])
        paragraph3 = f"""Key phrases and word choices such as {phrase_list} serve as linguistic indicators of the underlying emotional state. These specific terms trigger the emotional recognition and contribute significantly to the overall classification. The emotional intensity of this text is rated as {intensity}, reflecting the strength and clarity of the emotional expression conveyed through the message."""
        
        full_report = f"{paragraph1}\n\n{paragraph2}\n\n{paragraph3}"
        
        return {
            "analysis_report": full_report,
            "key_indicators": key_indicators[:5],
            "emotional_intensity": intensity,
            "intensity_score": intensity_num
        }
    except Exception as e:
        logging.warning(f"Error generating analysis report: {e}")
        return {
            "analysis_report": "Analysis report generation failed",
            "key_indicators": [],
            "emotional_intensity": "Unknown",
            "intensity_score": 0
        }


def detect_emotion_with_local_model(text):
    """
    Fallback: Detect emotion using local transformer model with detailed paragraph analysis
    """
    try:
        result = emotion_pipeline(text)  

        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
            result = result[0]  

        if isinstance(result, list) and all(isinstance(item, dict) for item in result):
            sorted_emotions = sorted(result, key=lambda x: x["score"], reverse=True)

            top_emotion = sorted_emotions[0]
            if top_emotion["label"] == "neutral" and top_emotion["score"] > 0.95:
                return {"error": "No Emotion Detected."}, 400

            # Detailed analysis with all emotions and percentages
            emotion_analysis = [
                {
                    "label": em["label"], 
                    "score": round(em["score"], 4),
                    "percentage": round(em["score"] * 100, 2)
                }
                for em in sorted_emotions  # Show all emotions in detail
            ]

            # Generate detailed paragraph analysis
            analysis_details = generate_analysis_report(text, emotion_analysis)

            response = {
                "Dominant_emotion": {
                    "label": top_emotion["label"],  
                    "score": round(top_emotion["score"], 4),
                    "percentage": round(top_emotion["score"] * 100, 2)
                },
                "Emotion Analysis": emotion_analysis,
                "analysis_report": analysis_details["analysis_report"],
                "key_indicators": analysis_details["key_indicators"],
                "emotional_intensity": analysis_details["emotional_intensity"],
                "model_used": "local_roberta_base_go_emotions"
            }
            return response, 200
        
        else:
            return {"error": "Unexpected model output format."}, 500

    except Exception as e:
        return {"error": f"Model error: {str(e)}"}, 500

