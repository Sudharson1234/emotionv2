from flask import Flask, request, jsonify,Response,json, render_template,flash,redirect,url_for,session,send_from_directory
import tensorflow as tf
import logging
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Setup local DeepFace path
from deepface_config import setup_deepface_path
setup_deepface_path()
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_migrate import Migrate
from flask_cors import CORS
from detections.detection import detect_text_emotion, generate_emotion_aware_response, generate_face_emotion_response
from models import db, User, Chat, GlobalChat  # Import db, User, Chat & GlobalChat from models.py
from deep_translator import GoogleTranslator

from detections.image_detection import process_image

from detections.video_detection import process_video
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

app = Flask(__name__) 
 
# Configurations
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your_jwt_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER']= UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH']= 100 * 1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize Extensions
db.init_app(app)  # Fix: Initialize db
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)  # Fix: Corrected variable name
CORS(app)

tf.get_logger().setLevel('ERROR')
logging.getLogger("tensorflow").setLevel(logging.ERROR)

def get_date_filter(period):
    """Get date filter based on period (day/week/month/all)"""
    now = datetime.utcnow()
    if period == 'day':
        start_date = now - timedelta(days=1)
    elif period == 'week':
        start_date = now - timedelta(weeks=1)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    else:  # 'all' or invalid
        return None
    return start_date

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login_page")
def login_page():
    return render_template("login.html")

@app.route("/signup_page")
def signup_page():
    return render_template("signup.html")

@app.route("/text_detection")
def text_detection():
    return render_template("text_detection.html")

@app.route("/image_detection")
def image_detection():
    return render_template("image_detection.html")

@app.route("/image_detection", methods=['POST'])
def image_detection_api():
    """API endpoint for image emotion detection via DeepFace"""
    try:
        if "file" in request.files:
            file = request.files["file"]
            response = process_image(file)
            return jsonify(response), 200
        elif request.is_json and "image_base64" in request.json:
            response = process_image()
            return jsonify(response), 200
        return jsonify({"error": "No valid image provided"}), 400
    except Exception as e:
        logging.error(f"Image detection error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/video_detection")
def video_detection():
    return render_template("video_detection.html")

@app.route("/video_detection", methods=['POST'])
def video_detection_api():
    """API endpoint for video emotion detection via DeepFace"""
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file provided"}), 400
        
        result = process_video(file)
        
        # Add success indicator
        if "error" in result:
            return jsonify(result), 400
        
        result["success"] = True
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Video detection error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/multi_language")
def multi_language():
    return render_template("multi_language.html")

@app.route("/analytics")
def analytics():
    """Display analytics dashboard"""
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    user = User.query.get(session["user_id"])
    return render_template("analytics.html", user=user)

@app.route("/logout")
def logout():
    session.clear()  # Completely clear session
    return redirect(url_for("login_page"))

@app.route("/signup", methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        name=request.form['name']
        phone=request.form['phone']
        email=request.form['email']
        password=request.form['password']
        confirm_password=request.form['Cpassword']

        # Check if passwords match
        if password != confirm_password:
            flash(" ⚠️ Passwords do not match!", "danger")
            return redirect(url_for('signup_page'))

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("⚠️ Email already registered!", "warning")
            return redirect(url_for('signup_page'))
        
        existing_phone= User.query.filter_by(phone=phone).first()
        if existing_phone:
            flash("⚠️ Phone number is already in use! Use another number.", "warning")
            return redirect(url_for('signup_page'))

        # Hash password and store user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8') 
        new_user = User(name=name, phone=phone, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Signup successful! You can now log in.", "success")
        return redirect(url_for('login_page'))
    
    return render_template('signup.html')

@app.route("/login",methods=['POST'])
def login():
    email=request.form.get("email")
    password=request.form.get("password")

    if not email or not password:
        flash("Missing email or password!", "warning")
        return redirect(url_for("login_page"))
    
    user = User.query.filter_by(email=email).first()
    if user is None:
        flash("No account found with this email. Please sign up!","warning")
        return redirect(url_for("login_page"))
    
    if not bcrypt.check_password_hash(user.password, password):
        flash("Incorrect password. Please try again!", "danger")
        return redirect(url_for("login_page"))
    
    session["user_id"]=user.id
    return redirect(url_for("userpage"))  # Redirect to user page


@app.route("/userpage")
def userpage():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    user = User.query.get(session["user_id"])
    return render_template("userpage.html", user=user)

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    user_id = get_jwt_identity()
    return jsonify({'message': f'Hello User {user_id}'}), 200

@app.route("/detect_test_emotion", methods=['POST'])
def test_emotion():
    data = request.json
    text = data.get("text", "")

    if not text.strip():
        return jsonify({'error': 'No text provided'}), 400

    emotion, status_code = detect_text_emotion(text)  
    return jsonify(emotion), status_code

@app.route("/image_upload",methods=['POST'])
def upload_image():
    try:
        if "file" in request.files:
            file = request.files["file"]
            response = process_image(file)
            return jsonify(response)
        elif request.is_json and "image_base64" in request.json:
            response = process_image()
            return jsonify(response)
        return jsonify({"error":"No valid image provided"}), 400
    except Exception as e:
        logging.error(f"Image upload error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/video_upload", methods=["POST"])
def video_upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    result = process_video(file)
    return result

@app.route("/detect_live_emotion", methods=["POST"])
def detect_live_emotion():
    """
    Detect emotion from live video frame (base64 image)
    Used by live_chat.html for real-time emotion detection
    """
    try:
        # Get base64 image from request
        data = request.json
        image_base64 = data.get("image_base64")
        
        if not image_base64:
            return jsonify({"error": "No image data provided"}), 400
        
        # Process the image using DeepFace
        import base64
        from io import BytesIO
        import numpy as np
        from PIL import Image
        
        # Decode base64 to image
        image_data = base64.b64decode(image_base64.split(",")[1] if "," in image_base64 else image_base64)
        image = Image.open(BytesIO(image_data))
        image_np = np.array(image)
        
        # Use DeepFace for emotion detection
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deepface'))
        from deepface import DeepFace
        
        result = DeepFace.analyze(
            image_np,
            actions=['emotion'],
            enforce_detection=False,
            silent=True
        )
        
        if result and len(result) > 0:
            emotion_dict = result[0]['emotion']
            detected_emotion = result[0]['dominant_emotion']
            confidence = emotion_dict.get(detected_emotion, 0) / 100
            
            return jsonify({
                "emotion": detected_emotion,
                "confidence": round(confidence, 4),
                "confidence_percentage": round(confidence * 100, 2),
                "emotion_scores": emotion_dict,
                "success": True
            }), 200
        else:
            return jsonify({
                "error": "No face detected",
                "success": False
            }), 400
            
    except Exception as e:
        logging.error(f"Live emotion detection error: {str(e)}")
        return jsonify({"error": str(e), "success": False}), 500

@app.route("/multilang_text", methods=['POST'])
def multilang_text():
    try:
        input_text = request.json.get('text')
        if not input_text:
            return jsonify({"error": "No text provided."}), 400
        
        translated_text = GoogleTranslator(source='auto', target='en').translate(input_text)
        emotion_response, status_code = detect_text_emotion(translated_text)

        if status_code != 200:
            return jsonify({"error": emotion_response.get("error", "Emotion detection failed.")}), status_code

        return jsonify({
            'original_text': input_text,
            'translated_text': translated_text,
            'top_emotion': emotion_response['Dominant_emotion']['label'],
            'Dominant_emotion': emotion_response['Dominant_emotion'],
            'emotion_analysis': emotion_response.get('Emotion Analysis', []),
            'analysis_report': emotion_response.get('analysis_report'),
            'key_indicators': emotion_response.get('key_indicators'),
            'emotional_intensity': emotion_response.get('emotional_intensity'),
            'model_used': emotion_response.get('model_used')
        }), 200

    except Exception as e:
        logging.error(f"Multilang detection error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==================== AI CHAT ROUTES ====================

@app.route("/chat")
def chat():
    """Display the AI chat page"""
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    user = User.query.get(session["user_id"])
    return render_template("chat.html", user=user)


@app.route("/api/chat", methods=['POST'])
def ai_chat():
    """Handle chat messages and emotion-based responses"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    try:
        # Detect emotion in user's message
        emotion_response, status_code = detect_text_emotion(user_message)
        
        if status_code != 200:
            # If emotion detection fails, use neutral response
            emotion_label = "neutral"
            emotion_score = 0.5
            ai_response = "Thank you for sharing. I'm here to listen. Tell me more about what you're thinking."
        else:
            emotion_label = emotion_response.get('Dominant_emotion', {}).get('label', 'neutral')
            emotion_score = emotion_response.get('Dominant_emotion', {}).get('score', 0.5)
            
            # Generate emotion-aware response
            ai_response = generate_emotion_aware_response(user_message, emotion_label, emotion_score)
        
        # Save chat to database
        chat_entry = Chat(
            user_id=session["user_id"],
            user_message=user_message,
            ai_response=ai_response,
            detected_emotion=emotion_label,
            emotion_score=float(emotion_score)
        )
        db.session.add(chat_entry)
        db.session.commit()
        
        return jsonify({
            'user_message': user_message,
            'ai_response': ai_response,
            'emotion': emotion_label,
            'emotion_score': float(emotion_score),
            'timestamp': chat_entry.timestamp.isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        return jsonify({'error': 'Failed to process message'}), 500


@app.route("/api/chat-history", methods=['GET'])
def get_chat_history():
    """Get user's chat history"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        chats = Chat.query.filter_by(user_id=session["user_id"]).order_by(Chat.timestamp).all()
        return jsonify([chat.to_dict() for chat in chats]), 200
    except Exception as e:
        logging.error(f"Error fetching chat history: {str(e)}")
        return jsonify({'error': 'Failed to fetch chat history'}), 500


@app.route("/api/chat-stats", methods=['GET'])
def get_chat_stats():
    """Get emotion statistics from chat history"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        period = request.args.get('period', 'all')
        start_date = get_date_filter(period)

        query = Chat.query.filter_by(user_id=session["user_id"])
        if start_date:
            query = query.filter(Chat.timestamp >= start_date)

        chats = query.all()
        emotion_counts = {}

        for chat in chats:
            emotion = chat.detected_emotion or 'unknown'
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        total_chats = len(chats)
        return jsonify({
            'total_chats': total_chats,
            'emotion_distribution': emotion_counts
        }), 200
    except Exception as e:
        logging.error(f"Error calculating chat stats: {str(e)}")
        return jsonify({'error': 'Failed to calculate statistics'}), 500


# ==================== GLOBAL CHAT WITH LIVE STREAM ROUTES ====================

@app.route("/live-chat")
def live_chat():
    """Display the global live chat page with video stream"""
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    user = User.query.get(session["user_id"])
    return render_template("live_chat.html", user=user)

@app.route("/api/global-chat", methods=['POST'])
def post_global_chat():
    """Post a message to global chat with emotion detection from text and/or face"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    user_message = data.get('message', '').strip()
    face_emotion = data.get('face_emotion')  # Emotion detected from live video feed
    
    if not user_message and not face_emotion:
        return jsonify({'error': 'Message or face emotion must be provided'}), 400
    
    try:
        user = User.query.get(session["user_id"])
        text_emotion = None
        ai_response = None
        emotion_score = None
        
        # Detect emotion from text if message provided
        if user_message:
            emotion_response, status_code = detect_text_emotion(user_message)
            if status_code == 200:
                text_emotion = emotion_response.get('Dominant_emotion', {}).get('label', 'neutral')
                emotion_score = emotion_response.get('Dominant_emotion', {}).get('score', 0.5)
        
        # Generate AI response based on emotions (face + text combined)
        primary_emotion = face_emotion or text_emotion or 'neutral'
        if user_message and (face_emotion or text_emotion):
            ai_response = generate_face_emotion_response(
                face_emotion=face_emotion or text_emotion,
                text_emotion=text_emotion,
                user_message=user_message
            )
        elif user_message and not face_emotion:
            ai_response = generate_emotion_aware_response(user_message, text_emotion or 'neutral', emotion_score or 0.5)
        elif face_emotion:
            ai_response = generate_face_emotion_response(face_emotion)
        
        # Save user message to global chat
        global_chat = GlobalChat(
            user_id=session["user_id"],
            username=user.name,
            user_message=user_message or f"[Detected face emotion: {face_emotion}]",
            ai_response=None,
            detected_text_emotion=text_emotion,
            detected_face_emotion=face_emotion,
            face_emotion_confidence=data.get('face_confidence'),
            emotion_score=emotion_score,
            is_ai_response=False
        )
        db.session.add(global_chat)
        db.session.commit()
        
        # Save AI response if generated
        ai_chat_entry = None
        if ai_response:
            ai_chat_entry = GlobalChat(
                user_id=1,  # Use a system user ID or create AI user
                username='AI Assistant',
                user_message=ai_response,
                ai_response=None,
                detected_text_emotion=None,
                detected_face_emotion=None,
                emotion_score=None,
                is_ai_response=True
            )
            db.session.add(ai_chat_entry)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message_id': global_chat.id,
            'user_message': global_chat.to_dict(),
            'ai_response': ai_chat_entry.to_dict() if ai_chat_entry else None,
            'ai_response_text': ai_response
        }), 200
        
    except Exception as e:
        logging.error(f"Global chat error: {str(e)}")
        return jsonify({'error': f'Failed to post message: {str(e)}'}), 500


@app.route("/api/global-chat-history", methods=['GET'])
def get_global_chat_history():
    """Get global chat history with all messages"""
    try:
        # Get limit parameter (default 50, max 200)
        limit = min(int(request.args.get('limit', 50)), 200)
        
        # Fetch most recent messages
        chats = GlobalChat.query.order_by(GlobalChat.timestamp.desc()).limit(limit).all()
        
        # Reverse to get chronological order (oldest first)
        chats.reverse()
        
        return jsonify({
            'total_messages': len(chats),
            'messages': [chat.to_dict() for chat in chats]
        }), 200
    except Exception as e:
        logging.error(f"Error fetching global chat history: {str(e)}")
        return jsonify({'error': 'Failed to fetch chat history'}), 500


@app.route("/api/global-chat-stats", methods=['GET'])
def get_global_chat_stats():
    """Get statistics about global chat emotions and participants"""
    try:
        period = request.args.get('period', 'all')
        start_date = get_date_filter(period)

        query = GlobalChat.query
        if start_date:
            query = query.filter(GlobalChat.timestamp >= start_date)

        all_chats = query.all()

        # Count emotions
        text_emotions = {}
        face_emotions = {}

        for chat in all_chats:
            if chat.detected_text_emotion:
                text_emotions[chat.detected_text_emotion] = text_emotions.get(chat.detected_text_emotion, 0) + 1
            if chat.detected_face_emotion:
                face_emotions[chat.detected_face_emotion] = face_emotions.get(chat.detected_face_emotion, 0) + 1

        # Count unique participants
        unique_users_query = GlobalChat.query.filter_by(is_ai_response=False)
        if start_date:
            unique_users_query = unique_users_query.filter(GlobalChat.timestamp >= start_date)
        unique_users = unique_users_query.distinct(GlobalChat.user_id).count()

        return jsonify({
            'total_messages': len(all_chats),
            'unique_participants': unique_users,
            'text_emotion_distribution': text_emotions,
            'face_emotion_distribution': face_emotions
        }), 200
    except Exception as e:
        logging.error(f"Error calculating global chat stats: {str(e)}")
        return jsonify({'error': 'Failed to calculate statistics'}), 500


@app.route("/api/face-emotion-response", methods=['POST'])
def face_emotion_response():
    """Generate AI response for detected face emotion in real-time"""
    data = request.json
    face_emotion = data.get('face_emotion')
    face_confidence = data.get('confidence', 0.8)

    if not face_emotion:
        return jsonify({'error': 'Face emotion required'}), 400

    try:
        response = generate_face_emotion_response(face_emotion)
        return jsonify({
            'success': True,
            'face_emotion': face_emotion,
            'confidence': face_confidence,
            'ai_response': response
        }), 200
    except Exception as e:
        logging.error(f"Face emotion response error: {str(e)}")
        return jsonify({'error': 'Failed to generate response'}), 500


@app.route("/api/analytics-report", methods=['GET'])
def analytics_report():
    """Generate analytics report for download"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        period = request.args.get('period', 'all')
        start_date = get_date_filter(period)

        # Get filtered data
        chat_query = Chat.query.filter_by(user_id=session["user_id"])
        if start_date:
            chat_query = chat_query.filter(Chat.timestamp >= start_date)
        chats = chat_query.all()

        global_query = GlobalChat.query
        if start_date:
            global_query = global_query.filter(GlobalChat.timestamp >= start_date)
        global_chats = global_query.all()

        # Calculate stats
        emotion_counts = {}
        for chat in chats:
            emotion = chat.detected_emotion or 'unknown'
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        global_text_emotions = {}
        global_face_emotions = {}
        for chat in global_chats:
            if chat.detected_text_emotion:
                global_text_emotions[chat.detected_text_emotion] = global_text_emotions.get(chat.detected_text_emotion, 0) + 1
            if chat.detected_face_emotion:
                global_face_emotions[chat.detected_face_emotion] = global_face_emotions.get(chat.detected_face_emotion, 0) + 1

        unique_users = len(set(chat.user_id for chat in global_chats if not chat.is_ai_response))

        # Create report data
        report_data = {
            'generated_at': datetime.utcnow().isoformat(),
            'period': period,
            'user_analytics': {
                'total_chats': len(chats),
                'emotion_distribution': emotion_counts,
                'chat_history': [chat.to_dict() for chat in chats[-50:]]  # Last 50 chats
            },
            'global_analytics': {
                'total_messages': len(global_chats),
                'unique_participants': unique_users,
                'text_emotion_distribution': global_text_emotions,
                'face_emotion_distribution': global_face_emotions
            }
        }

        return jsonify(report_data), 200
    except Exception as e:
        logging.error(f"Analytics report error: {str(e)}")
        return jsonify({'error': 'Failed to generate report'}), 500


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
