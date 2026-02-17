"""
Language Detection and Multilingual Support Module
Detects user language and provides multilingual responses
"""

import logging
from langdetect import detect, DetectorFactory
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

# Fix seed for consistent results
DetectorFactory.seed = 0

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supported languages mapping
SUPPORTED_LANGUAGES = {
    'en': 'English',
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
    'bn': 'Bengali',
    'pa': 'Punjabi',
    'te': 'Telugu',
    'mr': 'Marathi',
    'ta': 'Tamil',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'or': 'Odia',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'id': 'Indonesian',
    'ms': 'Malay',
    'tl': 'Filipino',
    'uk': 'Ukrainian',
    'pl': 'Polish',
    'ro': 'Romanian',
    'cs': 'Czech',
    'sk': 'Slovak',
    'hu': 'Hungarian',
    'sv': 'Swedish',
    'da': 'Danish',
    'no': 'Norwegian',
    'fi': 'Finnish',
    'tr': 'Turkish',
    'el': 'Greek',
    'he': 'Hebrew',
}

def detect_language(text):
    """
    Detect the language of the given text.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        tuple: (language_code, language_name, confidence)
    """
    try:
        if not text or len(text.strip()) < 2:
            return 'en', 'English', 1.0
        
        # Detect language
        lang_code = detect(text)
        
        # Map to standard codes (langdetect uses specific format)
        if lang_code == 'zh-cn':
            lang_code = 'zh-cn'
        elif lang_code == 'zh-tw':
            lang_code = 'zh-tw'
        elif lang_code.startswith('zh'):
            lang_code = 'zh-cn'  # Default to Simplified Chinese
        
        lang_name = SUPPORTED_LANGUAGES.get(lang_code, 'English')
        
        logger.info(f"Detected language: {lang_code} ({lang_name}) for text: {text[:50]}")
        
        return lang_code, lang_name, 1.0
        
    except Exception as e:
        logger.warning(f"Language detection failed: {e}. Defaulting to English.")
        return 'en', 'English', 0.0


def translate_to_english(text, source_language=None):
    """
    Translate text to English if not already in English.
    
    Args:
        text (str): The text to translate
        source_language (str, optional): Source language code
        
    Returns:
        tuple: (translated_text, original_language, was_translated)
    """
    try:
        if not text or len(text.strip()) < 2:
            return text, 'en', False
        
        # Detect language if not provided
        if source_language is None:
            source_language, _, _ = detect_language(text)
        
        # If already in English, return as is
        if source_language == 'en':
            return text, 'en', False
        
        # Translate to English
        translator = GoogleTranslator(source_auto=True, target='en')
        translated = translator.translate(text)
        
        logger.info(f"Translated from {source_language} to English")
        
        return translated, source_language, True
        
    except Exception as e:
        logger.warning(f"Translation to English failed: {e}. Using original text.")
        return text, source_language or 'unknown', False


def translate_to_language(text, target_language='en'):
    """
    Translate text to target language.
    
    Args:
        text (str): The text to translate
        target_language (str): Target language code
        
    Returns:
        tuple: (translated_text, success)
    """
    try:
        if not text or len(text.strip()) < 2:
            return text, True
        
        # If target is English and text seems to be English, skip
        if target_language == 'en':
            return text, True
        
        # Translate
        translator = GoogleTranslator(source_auto=True, target=target_language)
        translated = translator.translate(text)
        
        logger.info(f"Translated to {target_language}")
        
        return translated, True
        
    except Exception as e:
        logger.warning(f"Translation to {target_language} failed: {e}. Using original text.")
        return text, False


def get_multilingual_emotion_response(emotion_label, user_language='en'):
    """
    Get emotion-aware responses in multiple languages.
    
    Args:
        emotion_label (str): The detected emotion
        user_language (str): Target language code
        
    Returns:
        dict: Language-specific responses
    """
    
    responses = {
        'en': {
            'joy': "That's wonderful! I can feel your joy! What's bringing you this happiness?",
            'sadness': "I hear the sadness in your words. I'm here for you. What's troubling you?",
            'anger': "I sense your frustration. What's really bothering you right now?",
            'fear': "I feel your concern. Don't worry, I'm here to listen. What's worrying you?",
            'disgust': "Something clearly doesn't sit right with you. What specifically upsets you?",
            'surprise': "Wow! What an unexpected turn! Tell me what surprised you?",
            'neutral': "I appreciate you sharing. What's on your mind?",
        },
        'es': {
            'joy': "¡Eso es maravilloso! ¡Puedo sentir tu alegría! ¿Qué te trae tanta felicidad?",
            'sadness': "Siento la tristeza en tus palabras. Estoy aquí para ti. ¿Qué te preocupa?",
            'anger': "Siento tu frustración. ¿Qué te molesta en este momento?",
            'fear': "Siento tu preocupación. No te preocupes, estoy aquí para escucharte. ¿Qué te asusta?",
            'disgust': "Algo claramente no te parece bien. ¿Qué te molesta específicamente?",
            'surprise': "¡Vaya! ¡Qué giro inesperado! Cuéntame qué te sorprendió?",
            'neutral': "Aprecio tu sinceridad. ¿Qué hay en tu mente?",
        },
        'fr': {
            'joy': "C'est magnifique! Je peux sentir votre joie! Qu'est-ce qui vous apporte ce bonheur?",
            'sadness': "J'entends la tristesse dans vos paroles. Je suis là pour vous. Qu'est-ce qui vous préoccupe?",
            'anger': "Je sens votre frustration. Qu'est-ce qui vous ennuie vraiment en ce moment?",
            'fear': "Je sens votre inquiétude. Ne vous inquiétez pas, je suis là pour vous écouter. Qu'est-ce qui vous fait peur?",
            'disgust': "Quelque chose ne vous plaît clairement pas. Qu'est-ce qui vous dérange spécifiquement?",
            'surprise': "Wow! Quel revirement inattendu! Dites-moi ce qui vous a surpris?",
            'neutral': "J'apprécie votre sincérité. À quoi pensez-vous?",
        },
        'de': {
            'joy': "Das ist wunderbar! Ich kann deine Freude spüren! Was bringt dir dieses Glück?",
            'sadness': "Ich höre die Traurigkeit in deinen Worten. Ich bin für dich da. Was beunruhigt dich?",
            'anger': "Ich spüre deine Frustration. Was ärgert dich wirklich im Moment?",
            'fear': "Ich spüre deine Besorgnis. Keine Sorge, ich bin hier, um zuzuhören. Was macht dir Angst?",
            'disgust': "Etwas gefällt dir offensichtlich nicht. Was stört dich konkret?",
            'surprise': "Wow! Was für eine unerwartete Wendung! Sag mir, was dich überrascht hat?",
            'neutral': "Ich schätze deine Offenheit. Was beschäftigt dich?",
        },
        'it': {
            'joy': "È meraviglioso! Posso sentire la tua gioia! Cosa ti porta tanta felicità?",
            'sadness': "Sento la tristezza nelle tue parole. Sono qui per te. Cosa ti preoccupa?",
            'anger': "Sento la tua frustrazione. Cosa ti sta davvero infastidiendo?",
            'fear': "Sento la tua preoccupazione. Non preoccuparti, sono qui per ascoltarti. Cosa ti fa paura?",
            'disgust': "Qualcosa chiaramente non ti piace. Cosa ti infastidisce nello specifico?",
            'surprise': "Wow! Che colpo di scena inaspettato! Dimmi cosa ti ha sorpreso?",
            'neutral': "Apprezzo la tua sincerità. Cosa ti occupa?",
        },
        'pt': {
            'joy': "Isso é maravilhoso! Posso sentir sua alegria! O que traz tanta felicidade?",
            'sadness': "Sinto a tristeza nas suas palavras. Estou aqui para você. O que o preocupa?",
            'anger': "Sinto sua frustração. O que realmente está te incomodando?",
            'fear': "Sinto sua preocupação. Não se preocupe, estou aqui para ouvir. O que o assusta?",
            'disgust': "Algo claramente não agrada a você. O que especificamente o incomoda?",
            'surprise': "Uau! Que volta inesperada! Diga-me o que o surpreendeu?",
            'neutral': "Aprecio sua sinceridade. O que ocupa sua mente?",
        },
        'ru': {
            'joy': "Это прекрасно! Я чувствую твою радость! Что приносит тебе такое счастье?",
            'sadness': "Я слышу грусть в твоих словах. Я здесь для тебя. Что тебя беспокоит?",
            'anger': "Я чувствую твое разочарование. Что тебя на самом деле раздражает?",
            'fear': "Я чувствую твою тревогу. Не волнуйся, я здесь, чтобы слушать. Что тебя пугает?",
            'disgust': "Что-то явно тебе не нравится. Что конкретно тебя раздражает?",
            'surprise': "Вау! Какой неожиданный поворот! Расскажи, что тебя удивило?",
            'neutral': "Я ценю твою откровенность. О чем ты думаешь?",
        },
        'ja': {
            'joy': "素晴らしい!あなたの喜びが感じられます!何があなたにこんな幸せをもたらしていますか?",
            'sadness': "あなたの言葉から悲しみを感じます。私があなたのためにここにいます。何があなたを悩ませていますか?",
            'anger': "あなたの欲求不満を感じます。何が本当にあなたを困らせていますか?",
            'fear': "あなたの懸念を感じます。心配しないでください。私はここにいてあなたの話を聞きます。何があなたを怖がらせていますか?",
            'disgust': "明らかに何かあなたを不快にさせています。具体的に何があなたを不快にしていますか?",
            'surprise': "わあ!何か予期しない展開です!何があなたを驚かせましたか?",
            'neutral': "あなたの誠実さを感謝します。何があなたの心を占めていますか?",
        },
        'ko': {
            'joy': "정말 멋져요! 당신의 기쁨이 느껴져요! 무엇이 당신에게 이런 행복을 주나요?",
            'sadness': "당신의 말에서 슬픔을 느껩니다. 저는 당신을 위해 여기 있습니다. 무엇이 당신을 걱정하게 하나요?",
            'anger': "당신의 좌절감이 느껴집니다. 무엇이 정말로 당신을 짜증나게 하나요?",
            'fear': "당신의 우려가 느껴집니다. 걱정하지 마세요. 저는 여기서 당신의 말을 들을 준비가 되어 있습니다. 무엇이 당신을 두렵게 하나요?",
            'disgust': "분명히 뭔가 당신을 불편하게 합니다. 구체적으로 무엇이 당신을 불편하게 하나요?",
            'surprise': "와! 정말 예상치 못한 일입니다! 무엇이 당신을 놀라게 했나요?",
            'neutral': "당신의 진정성을 감사합니다. 무엇이 당신의 마음을 차지하고 있나요?",
        },
        'zh-cn': {
            'joy': "太棒了! 我能感受到你的喜悦! 是什么给你带来了这样的幸福?",
            'sadness': "我能感受到你言语中的悲伤。我在这里陪伴你。什么让你感到烦恼?",
            'anger': "我能感受到你的沮丧。什么真正让你感到恼火?",
            'fear': "我能感受到你的担忧。别担心，我在这里倾听。什么让你感到害怕?",
            'disgust': "显然有什么让你感到不适。具体是什么让你感到厌恶?",
            'surprise': "哇! 多么意外的转折! 告诉我什么让你感到惊讶?",
            'neutral': "我感谢你的坦诚。什么在占据你的思想?",
        },
        'ar': {
            'joy': "هذا رائع! أستطيع أن أشعر بفرحك! ما الذي يجلب لك كل هذا السعادة?",
            'sadness': "أشعر بالحزن في كلماتك. أنا هنا لك. ما الذي يقلقك?",
            'anger': "أشعر بإحباطك. ما الذي يزعجك حقًا?",
            'fear': "أشعر بقلقك. لا تقلق، أنا هنا لأستمع. ما الذي يخيفك?",
            'disgust': "من الواضح أن هناك شيئًا لا يعجبك. ما الذي يزعجك تحديدًا?",
            'surprise': "واو! حقاً من الضحايا غير المتوقعة! أخبرني ما الذي فاجأك?",
            'neutral': "أقدر صراحتك. ما الذي يشغل بالك?",
        },
        'hi': {
            'joy': "बहुत अच्छा! मैं आपकी खुशी को महसूस कर सकता हूँ! क्या आपको ऐसी खुशी दे रहा है?",
            'sadness': "मैं आपकी बातों में उदासी को महसूस करता हूँ। मैं आपके लिए यहाँ हूँ। आपको क्या परेशान कर रहा है?",
            'anger': "मैं आपकी निराशा को महसूस करता हूँ। आपको वास्तव में क्या परेशान कर रहा है?",
            'fear': "मैं आपकी चिंता को महसूस करता हूँ। चिंता मत करो, मैं सुनने के लिए यहाँ हूँ। आपको क्या डर लगता है?",
            'disgust': "कुछ स्पष्ट रूप से आपको पसंद नहीं है। विशेष रूप से क्या आपको नापसंद है?",
            'surprise': "वाह! कितना अप्रत्याशित मोड़! बताइए आपको क्या आश्चर्य हुआ?",
            'neutral': "मैं आपकी ईमानदारी की सराहना करता हूँ। आपके मन में क्या है?",
        },
    }
    
    # Get language responses, default to English if not available
    lang_responses = responses.get(user_language, responses['en'])
    
    # Get emotion response
    response = lang_responses.get(emotion_label.lower(), lang_responses.get('neutral'))
    
    return response


def get_language_code_from_name(language_name):
    """
    Get language code from language name.
    
    Args:
        language_name (str): The language name
        
    Returns:
        str: Language code
    """
    for code, name in SUPPORTED_LANGUAGES.items():
        if name.lower() == language_name.lower():
            return code
    return 'en'


def is_language_supported(language_code):
    """Check if language is supported."""
    return language_code in SUPPORTED_LANGUAGES


if __name__ == "__main__":
    # Test the module
    test_texts = [
        "I am very happy today!",
        "Estoy muy feliz hoy!",
        "Je suis très heureux aujourd'hui!",
        "我很高兴有你!",
        "مرحبا، كيف حالك؟",
    ]
    
    for text in test_texts:
        lang_code, lang_name, confidence = detect_language(text)
        print(f"Text: {text}")
        print(f"Language: {lang_name} ({lang_code}), Confidence: {confidence}\n")
