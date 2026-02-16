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

# Global Groq client
groq_client = None

# Helper to get Groq client with proper environment loading
def get_groq_client():
    global groq_client
    if groq_client:
        return groq_client
    
    # Try to load .env from root if it's not already loaded
    if not os.getenv('GROQ_API_KEY'):
        root_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(root_env):
            load_dotenv(root_env)
    
    api_key = os.getenv('GROQ_API_KEY')
    if api_key:
        try:
            groq_client = Groq(api_key=api_key)
            return groq_client
        except Exception as e:
            logging.error(f"Failed to initialize Groq client: {e}")
    return None

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
    client = get_groq_client()
    if client:
        try:
            logging.info(f"Attempting Groq detection for text: {text[:50]}...")
            return detect_emotion_with_groq(text, client)
        except Exception as e:
            logging.warning(f"Groq API error: {e}. Using local model instead.")
    else:
        logging.info("Groq client not initialized. Using local model.")
    
    # Fallback to local model
    return detect_emotion_with_local_model(text)


def detect_emotion_with_groq(text, client):
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
        
        chat_completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
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
            emotion_data["model_used"] = "groq-llama-3.1-8b-instant"
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


def generate_emotion_aware_response(user_message, emotion_label, emotion_score):
    """
    Generate an AI response that is empathetic and tailored to the user's detected emotion.
    Uses Groq API to create dynamic, context-aware responses.
    """
    client = get_groq_client()
    
    # Define emotion-specific prompts for better context
    emotion_prompts = {
        "joy": "The user is expressing happiness/joy",
        "sadness": "The user is expressing sadness or melancholy",
        "anger": "The user is expressing anger or frustration",
        "fear": "The user is expressing fear or anxiety",
        "disgust": "The user is expressing disgust or disapproval",
        "surprise": "The user is expressing surprise or shock",
        "happy": "The user is expressing happiness/joy",
        "neutral": "The user is expressing neutral emotions"
    }
    
    emotion_context = emotion_prompts.get(emotion_label.lower(), f"The user is expressing {emotion_label} emotions")
    emotion_label_lower = emotion_label.lower()
    
    if client:
        try:
            prompt = f"""You are an empathetic, warm, and supportive AI companion. The user has shared their thoughts.

Emotion Detected: {emotion_label} ({emotion_score*100:.1f}% confidence)
Context: {emotion_context}

User's Message: "{user_message}"

Provide a warm, genuine response that:
1. Acknowledges their emotional state with sincerity
2. Shows deep understanding and empathy
3. Offers helpful perspective or support based on their emotion
4. Keeps it conversational (2-3 sentences maximum)
5. Feels like a real friend supporting them

Be genuine, warm, and supportive."""

            chat_completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an empathetic, deeply caring AI companion. You truly understand emotions and respond with genuine warmth, wisdom, and helpful guidance. Your responses feel natural, human, and supportive."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=300,
                top_p=0.9
            )
            
            response = chat_completion.choices[0].message.content.strip()
            if response and len(response) > 0:
                return response
        except Exception as e:
            logging.warning(f"Groq API error, using fallback: {str(e)}")
    
    # Comprehensive fallback responses based on emotion
    fallback_responses = {
        "joy": "🌟 That's amazing! Your happiness is wonderful to hear. What's bringing you all this joy today? I'd love to know more!",
        "happy": "🎉 That sounds fantastic! I'm genuinely happy for you. Tell me more about what's making you smile!",
        "sadness": "💙 I hear you, and I want you to know it's completely okay to feel this way. I'm here to listen and support you through this. What's on your mind?",
        "sad": "💙 It sounds like you're going through something difficult. Your feelings are valid, and I'm here for you. Do you want to talk about it?",
        "anger": "⚡ I can feel the intensity here, and that's completely valid. Sometimes frustration is necessary. What's at the core of this for you?",
        "angry": "⚡ Your feelings of frustration are completely understandable. I'm here to listen without judgment. What's really bothering you?",
        "fear": "🤝 I understand that something is causing you concern. Fear is natural, and reaching out shows real courage. I'm here to support you. What worries you?",
        "fear": "💭 It sounds like anxiety is present. That's okay - we all have moments of worry. I'm here to help. What's concerning you most?",
        "disgust": "😔 I sense something has disappointed or bothered you deeply. Your reaction makes sense. Do you want to talk about what's troubling you?",
        "surprise": "😲 Wow! That sounds like quite the unexpected turn! Tell me everything - I'd love to hear what surprised you so!",
        "neutral": "😊 I appreciate you sharing that perspective with me. I'm curious - how are you really feeling about all of this? I'm here to listen.",
        "love": "💕 That's beautiful! Love is one of life's greatest gifts. I'm happy you're experiencing that. What does this mean to you?",
        "trust": "🤝 It's wonderful to hear trust in your words. Trust is so important. Keep building those strong connections!",
        "uncertainty": "🤔 I can sense there's some uncertainty here, and that's natural when facing the unknown. Take your time - what questions are on your mind?"
    }
    
    response = fallback_responses.get(emotion_label_lower, fallback_responses.get(emotion_label, "I appreciate you sharing that with me. I'm here to listen and support you. What else is on your mind?"))
    return response


def generate_face_emotion_response(face_emotion, text_emotion=None, user_message=None):
    """
    Generate AI response based on detected face emotion during video/live stream.
    Can also combine with text emotion for more comprehensive response.
    
    Args:
        face_emotion (str): The detected emotion from facial expression
        text_emotion (str, optional): The detected emotion from text
        user_message (str, optional): The user's message text
        
    Returns:
        str: AI-generated response tailored to the emotional state
    """
    client = get_groq_client()
    if not client:
        return f"I notice you're expressing {face_emotion}. I'm here to listen and support you. What's on your mind?"
    
    # Prepare emotion context
    emotion_context = f"The user is displaying {face_emotion} facial expression"
    if text_emotion and text_emotion != "neutral":
        emotion_context += f" combined with {text_emotion} sentiment in their message"
    
    try:
        # Build the prompt based on available information
        if user_message:
            prompt = f"""You are an emotionally intelligent AI companion supporting a user in a live chat.

Detected Face Emotion: {face_emotion}
Detected Text Emotion: {text_emotion or 'neutral'}
User's Message: "{user_message}"

Response should:
1. Acknowledge their detected emotional state (face + text if both are strong)
2. Be warm, genuine, and empathetic
3. Provide supportive feedback or guidance
4. Keep it concise (2-3 sentences)
5. Encourage more conversation if appropriate

Respond like a compassionate friend who understands their emotional needs."""
        else:
            prompt = f"""You are an emotionally intelligent AI companion supporting a user in a live video stream.

User's Facial Emotion: {face_emotion}

The user is broadcasting their face emotion in the live stream. Provide a warm, supportive, and empathetic response that:
1. Acknowledges their emotional state based on their facial expression
2. Validates their feelings
3. Offers a supportive comment or question
4. Keep it concise (1-2 sentences) as they're in a live stream

Respond with genuine human-like warmth and understanding."""

        chat_completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an empathetic, perceptive AI that understands facial expressions and emotions. You provide genuine, supportive responses that validate people's feelings and create a safe space for them to express themselves."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        
        response = chat_completion.choices[0].message.content.strip()
        return response
        
    except Exception as e:
        logging.error(f"Error generating face emotion response: {e}")
        # Elaborate fallback responses based on face emotion
        fallback_responses = {
            "happy": "Your happiness is contagious! That smile brightens the stream. Keep sharing that joy with us! 😊",
            "sad": "I can see you're going through something tough. Remember, it's okay to feel sad. We're here for you. 💙",
            "angry": "I sense some strong emotions there. Whatever's frustrating you, know that your feelings are valid. Want to talk about it?",
            "fearful": "It looks like something's worrying you. That's completely normal. You're safe here, and I'm listening. 💙",
            "disgusted": "Something seems off for you right now. Your feelings matter, and I'm here to listen without judgment.",
            "surprised": "Wow, you seem surprised! What just happened? Tell us more! 👀",
            "neutral": f"I see you're in a thoughtful mood. Whatever's on your mind, I'm here to listen and support you.",
        }
        
        return fallback_responses.get(face_emotion.lower(), f"I see you're expressing {face_emotion}. I'm here to support you. What would you like to share?")


