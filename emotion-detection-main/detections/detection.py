import re
import os
import json
import logging
from transformers import pipeline
from nltk.corpus import words
from textblob import TextBlob
from groq import Groq
from dotenv import load_dotenv
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from language_utils import detect_language, translate_to_english, translate_to_language, get_multilingual_emotion_response

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


def detect_text_emotion(text, user_language=None):
    """
    Detect emotion from text with multilingual support
    
    Args:
        text (str): The text to analyze
        user_language (str): User's language code (optional, will be detected if not provided)
        
    Returns:
        tuple: (emotion_data, status_code)
    """

    if not text.strip():
        return {"error": "Please enter a statement."}, 400  
    
    # Simplified meaningful check - just check for gibberish
    if is_gibberish(text):
        return {"error":"No Emotion Detected. Please enter a valid statement."},400
    
    # Detect language if not provided
    if user_language is None:
        try:
            user_language, lang_name, _ = detect_language(text)
            logging.info(f"Detected language: {lang_name} ({user_language})")
        except Exception as e:
            logging.warning(f"Language detection failed: {e}. Defaulting to English.")
            user_language = 'en'
            lang_name = 'English'
    else:
        lang_name = user_language
    
    # Translate to English for emotion detection if not in English
    text_for_analysis = text
    was_translated = False
    
    if user_language != 'en':
        try:
            text_for_analysis, _, was_translated = translate_to_english(text, user_language)
            logging.info(f"Translated text for emotion analysis from {user_language}")
        except Exception as e:
            logging.warning(f"Translation failed: {e}. Using original text for emotion detection.")
            text_for_analysis = text
            was_translated = False
    
    # Try Groq first if available
    client = get_groq_client()
    if client:
        try:
            logging.info(f"Attempting Groq detection for text: {text_for_analysis[:50]}...")
            emotion_result, status_code = detect_emotion_with_groq(text_for_analysis, client)
            
            if status_code == 200:
                # Add language information
                emotion_result['detected_language'] = user_language
                emotion_result['language_name'] = lang_name
                emotion_result['was_translated'] = was_translated
                emotion_result['original_text'] = text
                emotion_result['analysis_text'] = text_for_analysis if was_translated else text
                
            return emotion_result, status_code
        except Exception as e:
            logging.warning(f"Groq API error: {e}. Using local model instead.")
    else:
        logging.info("Groq client not initialized. Using local model.")
    
    # Fallback to local model
    emotion_result, status_code = detect_emotion_with_local_model(text_for_analysis)
    
    if status_code == 200:
        # Add language information
        emotion_result['detected_language'] = user_language
        emotion_result['language_name'] = lang_name
        emotion_result['was_translated'] = was_translated
        emotion_result['original_text'] = text
        emotion_result['analysis_text'] = text_for_analysis if was_translated else text
    
    return emotion_result, status_code


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
        logging.error(f"API Key available: {bool(os.getenv('GROQ_API_KEY'))}")
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


def generate_emotion_aware_response(user_message, emotion_label, emotion_score, user_language='en'):
    """
    Generate an AI response that is empathetic and tailored to the user's detected emotion.
    Supports multilingual responses using Groq API.
    
    Args:
        user_message (str): The user's message
        emotion_label (str): Detected emotion
        emotion_score (float): Emotion confidence score
        user_language (str): User's language code (default: 'en')
        
    Returns:
        str: AI-generated response in user's language
    """
    client = get_groq_client()
    
    emotion_label_lower = emotion_label.lower()
    
    if client:
        try:
            # Build language instruction based on user language
            language_instruction = ""
            if user_language != 'en':
                lang_names = {
                    'es': 'Spanish',
                    'fr': 'French',
                    'de': 'German',
                    'it': 'Italian',
                    'pt': 'Portuguese',
                    'ru': 'Russian',
                    'ja': 'Japanese',
                    'ko': 'Korean',
                    'zh-cn': 'Chinese (Simplified)',
                    'zh-tw': 'Chinese (Traditional)',
                    'ar': 'Arabic',
                    'hi': 'Hindi',
                    'ta': 'Tamil',
                    'te': 'Telugu',
                    'bn': 'Bengali',
                    'ur': 'Urdu',
                    'th': 'Thai',
                    'vi': 'Vietnamese',
                    'tr': 'Turkish',
                    'nl': 'Dutch',
                    'sv': 'Swedish',
                    'pl': 'Polish',
                    'id': 'Indonesian',
                    'ms': 'Malay',
                    'ml': 'Malayalam',
                    'kn': 'Kannada',
                    'gu': 'Gujarati',
                    'mr': 'Marathi',
                    'pa': 'Punjabi',
                }
                target_lang = lang_names.get(user_language, None)
                if target_lang:
                    language_instruction = f"\nIMPORTANT: The user is writing in {target_lang}. You MUST respond ONLY in {target_lang}. Do not use English at all. Match the user's language exactly."
                else:
                    # Unknown language code but not English — tell AI to detect and match
                    language_instruction = f"\nIMPORTANT: The user is NOT writing in English. Detect the language of their message and respond ENTIRELY in that same language. Do not use English at all. Match the user's language exactly."
            
            # Build emotion-specific guidance for the AI
            emotion_guidance = {
                "joy": "The user is happy — genuinely celebrate with them, appreciate their positivity, and encourage them to keep embracing what brings them joy. Be warm and uplifting.",
                "happy": "The user is feeling good — share in their happiness, compliment their positive outlook, and motivate them to spread this energy. Be enthusiastic and supportive.",
                "sadness": "The user is sad — offer sincere consolation, validate that their pain is real and matters, remind them that tough times are temporary, and gently suggest healthy coping strategies. Be compassionate and tender.",
                "sad": "The user is going through a hard time — listen deeply, acknowledge their struggle without minimizing it, offer words of comfort and hope, and remind them they are not alone. Be caring and patient.",
                "anger": "The user is frustrated or angry — first validate their feelings without judgment, help them see the situation with perspective, and suggest constructive ways to channel their energy. Be calm and understanding.",
                "angry": "The user is upset — acknowledge that their frustration is valid, help them process what happened, and guide them toward a solution or peace of mind. Be respectful and grounding.",
                "fear": "The user is anxious or afraid — reassure them with genuine empathy, help them break down what's scaring them into manageable pieces, and remind them of their strength. Be calming and encouraging.",
                "afraid": "The user is worried — provide comfort and reassurance, normalize their feelings, offer practical perspective, and remind them that courage isn't the absence of fear. Be supportive and gentle.",
                "disgust": "The user is bothered by something — acknowledge their strong reaction, help them understand what's triggering it, and offer a constructive way to think about or handle the situation. Be respectful.",
                "surprise": "The user is surprised — share in their amazement, help them process the unexpected, and encourage them to see opportunities in the surprise. Be excited and curious with them.",
                "neutral": "The user seems reflective — engage meaningfully with their actual words, offer thoughtful perspective, and ask a question that helps them explore their thoughts deeper. Be attentive and insightful.",
                "love": "The user is feeling love or affection — appreciate the beauty in their emotions, encourage them to cherish and express their feelings, and be warm and heartfelt.",
                "confusion": "The user seems confused — help clarify their thoughts with patience, break things down simply, and guide them toward clarity. Be patient and supportive.",
                "approval": "The user is expressing approval — affirm their positive judgment, appreciate their perspective, and encourage them to continue making good assessments."
            }
            
            guidance = emotion_guidance.get(emotion_label_lower, emotion_guidance.get("neutral", "Respond with empathy and genuine care."))
            
            prompt = f"""You are a professional emotional wellness counselor and empathetic AI companion named emoti.

User's Message: "{user_message}"
Detected Emotion: {emotion_label} (Confidence: {emotion_score*100:.1f}%)

Your Approach for this emotion:
{guidance}

Response Guidelines:
1. DIRECTLY address what the user actually said — show you truly understood their specific situation, not just the emotion label
2. Be PROFESSIONAL yet warm — like a trusted counselor who genuinely cares
3. If they're struggling: Console them sincerely, validate their feelings, and offer a hopeful perspective or practical advice
4. If they're happy/positive: Celebrate WITH them, appreciate their achievement or joy, and motivate them to keep going
5. If they're angry/frustrated: Acknowledge their feelings without judgment, help them gain perspective, and suggest positive next steps
6. If they're afraid/anxious: Reassure them, normalize their fear, and empower them with courage and practical strategies
7. Always end with either an encouraging statement OR a thoughtful question that shows you care about them as a person
8. Keep it to 2-4 sentences — impactful and meaningful, not generic
9. NEVER use phrases like "I detect sadness" or "Your emotion score is..." — respond naturally as a human would
10. Be genuine, specific, and make the person feel truly heard and valued{language_instruction}"""

            chat_completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are emoti — a professional, emotionally intelligent AI wellness companion. You combine the warmth of a caring friend with the insight of a professional counselor. You console those in pain, celebrate those in joy, motivate those who are struggling, and guide those who are lost. You speak with genuine empathy, professionalism, and heart. You never give generic responses — every reply is tailored to what the person actually said and what they're truly feeling. You help people feel heard, valued, and empowered. You are fluent in multiple languages and always respond in the user's language."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.75,
                max_tokens=400,
                top_p=0.9
            )
            
            response = chat_completion.choices[0].message.content.strip()
            if response and len(response) > 0:
                logging.info(f"Generated AI response using Groq for emotion: {emotion_label} in language: {user_language}")
                return response
        except Exception as e:
            logging.warning(f"Groq API error, using fallback: {str(e)}")
    
    # Use multilingual predefined responses
    try:
        multilingual_response = get_multilingual_emotion_response(emotion_label, user_language)
        if multilingual_response:
            logging.info(f"Using multilingual fallback response for {user_language}")
            return multilingual_response
    except Exception as e:
        logging.warning(f"Multilingual response generation failed: {e}")
    
    # Final fallback
    emotion_label_lower = emotion_label.lower()
    
    # Smart fallback responses that reference the user's message
    context_responses = {
        "joy": [
            "That's wonderful! What details are making this experience so joyful? I'd love to hear more about why this means so much to you.",
            "I can feel the positivity! What's the best part of this for you right now?",
            "That's fantastic news! How does it feel to be experiencing this joy?"
        ],
        "happy": [
            "You sound genuinely happy about that! What sparked this good feeling?",
            "That's great! Tell me more about what's making you smile.",
            "I'm genuinely happy for you! What's the story here?"
        ],
        "sadness": [
            "I hear the sadness in what you're saying, and that's completely valid. What's weighing on your heart right now?",
            "It sounds like you're going through a difficult time. I'm here to listen - what happened?",
            "Your feelings matter. What's really bothering you about this situation?"
        ],
        "sad": [
            "I'm sorry you're feeling this way. What's going on that's brought you down?",
            "It's okay to feel sad. Sometimes things hurt, and that's valid. Talk to me about it?",
            "I sense real pain behind what you're saying. I'm here for you. What do you need right now?"
        ],
        "anger": [
            "I can sense the frustration here. What's really at the core of this that's upset you?",
            "Your anger is telling you something important. What's the root of this frustration?",
            "I hear the intensity. Take it from here - what specifically made you feel this way?"
        ],
        "angry": [
            "Something clearly upset you. I want to understand - what happened?",
            "Your frustration is justified if something real caused it. What's the story?",
            "I'm listening without judgment. What's really going on here?"
        ],
        "fear": [
            "I sense some anxiety in what you're sharing. What's worrying you about this?",
            "It sounds like something's concerning you deeply. What fears are coming up for you?",
            "Your worry is real and valid. What's the main thing that's scaring you here?"
        ],
        "afraid": [
            "I hear the concern. What's making you feel unsafe or uncertain?",
            "Something's causing you anxiety. What's the core of this fear?",
            "It's natural to feel worried. What specifically are you anxious about?"
        ],
        "disgust": [
            "Something clearly bothers you about this. What specifically is disappointing or upsetting you?",
            "I sense strong disapproval. What's the specific issue here?",
            "Your reaction shows something important. What exactly are you not okay with?"
        ],
        "surprise": [
            "Wow, that caught you off guard! What exactly happened that surprised you?",
            "You sound genuinely shocked. Tell me the full story - I want to hear what surprised you!",
            "That's unexpected! Walk me through what just happened."
        ],
        "neutral": [
            "You seem thoughtful about this. What's your perspective on what you just shared?",
            "I'm curious about your take on this. How do you really feel about it?",
            "That's interesting. What else should I know about your thinking here?"
        ],
    }
    
    responses = context_responses.get(emotion_label_lower, None)
    if responses:
        import random
        return random.choice(responses)
    
    return f"I appreciate you sharing that with me. Can you tell me more about why you feel {emotion_label} about this? I want to understand your perspective better."


def generate_face_emotion_response(face_emotion, text_emotion=None, user_message=None):
    """
    Generate AI response based on detected face emotion during video/live stream.
    ChatGPT-style responses that are contextual and engaging.
    
    Args:
        face_emotion (str): The detected emotion from facial expression
        text_emotion (str, optional): The detected emotion from text
        user_message (str, optional): The user's message text
        
    Returns:
        str: AI-generated response tailored to the emotional state
    """
    client = get_groq_client()
    
    # Build emotional context
    emotion_context = f"The user is displaying {face_emotion} facial expression"
    if text_emotion and text_emotion.lower() != "neutral":
        emotion_context += f" combined with {text_emotion} sentiment in their message"
    
    if client:
        try:
            # Build the prompt based on available information
            if user_message:
                prompt = f"""You are an exceptionally empathetic and emotionally intelligent AI companion.
The user is chatting with you in real-time and we've detected their emotional state through their face and message.

Detected Face Emotion: {face_emotion}
Detected Text Emotion: {text_emotion or 'neutral'}
User's Message: "{user_message}"

Generate a response that:
1. Acknowledges their emotional state naturally (face + text combined)
2. Directly addresses what they said - show you understand their message specifically
3. Validates their feelings
4. Offer perspective, support, or helpful insight
5. Ask a thoughtful follow-up that demonstrates you care
6. Sound like a real, caring friend - warm and genuine
7. Keep it conversational (2-3 sentences)

Be specific and personal. Reference details from their message. Show you really understood what they said, not just that they said something."""
            else:
                prompt = f"""You are an exceptionally empathetic AI companion in a live stream.

User's Facial Emotion: {face_emotion}

The user is sharing their facial emotion with us. Respond with:
1. A warm acknowledgment of their emotional state
2. Validation of their feelings
3. A supportive comment that shows genuine understanding
4. Encourage them to share more if they want to
5. Keep it brief but heartfelt (2-3 sentences)

Feel like you genuinely care about what they're experiencing."""

            chat_completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an exceptionally perceptive and empathetic AI. You understand facial expressions and emotions deeply. You respond with genuine warmth, real understanding, and helpful perspective. You sound like a best friend who truly gets what people are going through. You're conversational, kind, and insightful."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=300,
                top_p=0.9
            )
            
            response = chat_completion.choices[0].message.content.strip()
            if response:
                logging.info(f"Generated face emotion response using Groq for emotion: {face_emotion}")
                return response
            
        except Exception as e:
            logging.error(f"Error generating face emotion response: {e}")
    
    # Elaborate, empathetic fallback responses
    fallback_responses = {
        "happy": "😊 Your joy is truly beautiful right now. Whatever's bringing you this happiness, hold onto it! What's making you feel so good?",
        "joy": "🌟 I can see the genuine joy! That's wonderful. Tell me what's contributing to all this positivity?",
        "sad": "💙 I can see you're having a rough moment, and that's completely okay. Sometimes we need to feel what we feel. I'm here if you want to talk about it.",
        "sadness": "💙 Your sadness is real and valid. Whatever you're going through, know that these feelings will pass. What's on your heart?",
        "angry": "⚡ I sense some real intensity of feeling right now. That frustration or anger is telling you something. What's really bothering you?",
        "anger": "⚡ Your anger matters - it usually means something important needs attention. What's at the core of this for you?",
        "fear": "🤝 I see the worry or concern. That's a natural response to uncertainty. Want to talk through what's worrying you?",
        "fearful": "🤝 Something's causing you concern, and that's understandable. I'm here to listen and help if I can.",
        "disgust": "😔 Something clearly doesn't sit right with you, and your reaction makes total sense. What specifically bothers you?",
        "surprise": "😲 Wow, you've been caught off guard! What just happened? I'd love to hear the story!",
        "confused": "🤔 It looks like something has you thinking. That's okay - complex things deserve reflection. What's confusing about it?",
        "neutral": "😊 You seem thoughtful and measured about this. I respect that. What are your actual thoughts on it?",
    }
    
    response = fallback_responses.get(face_emotion.lower(), f"I notice you're expressing {face_emotion}. I'm genuinely here to listen and support you. What would you like to share with me?")
    return response


