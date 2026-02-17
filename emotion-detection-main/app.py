from flask import Flask, request, jsonify,Response,json, render_template,flash,redirect,url_for,session,send_from_directory
import logging
import os
import sys
import uuid
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Lazy load TensorFlow to avoid initialization errors
try:
    import tensorflow as tf
    tf.get_logger().setLevel('ERROR')
except Exception as e:
    tf = None
    logging.warning(f"TensorFlow import failed: {e}")

# Setup local DeepFace path
from deepface_config import setup_deepface_path
setup_deepface_path()
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_migrate import Migrate
from flask_cors import CORS

# Lazy load heavy ML modules - don't load on app startup
ML_AVAILABLE = False
detect_text_emotion = None
generate_emotion_aware_response = None
generate_face_emotion_response = None
process_image = None
process_video = None

def load_ml_modules():
    """Load ML modules only when needed"""
    global ML_AVAILABLE, detect_text_emotion, generate_emotion_aware_response
    global generate_face_emotion_response, process_image, process_video
    
    if not ML_AVAILABLE:
        try:
            from detections.detection import detect_text_emotion, generate_emotion_aware_response, generate_face_emotion_response
            from detections.image_detection import process_image
            from detections.video_detection import process_video
            ML_AVAILABLE = True
            logging.info("ML modules loaded successfully")
        except Exception as e:
            logging.warning(f"ML modules import failed: {e}. Some features will be unavailable.")
            ML_AVAILABLE = False

from models import mongo, create_user, find_user_by_email, find_user_by_phone, find_user_by_id, update_user_last_login, create_chat, get_user_chats, create_global_chat, get_global_chats, create_session, find_session_by_token, update_session_activity, deactivate_session, get_active_sessions, get_chat_stats, get_global_chat_stats  # Import MongoDB functions from models.py
from deep_translator import GoogleTranslator
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configurations
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your_jwt_secret_key')
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb+srv://ksudharson30_db_user:tYRDQ4aAZH3cC6jM@cluster0.kwjrw6t.mongodb.net/')
app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookie over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # JavaScript cannot access the cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Session timeout (24 hours)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER']= UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH']= 100 * 1024 * 1024

# Session timeout in seconds
SESSION_TIMEOUT = 24 * 60 * 60  # 24 hours

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize Extensions
try:
    mongo.init_app(app)  # Initialize MongoDB
except Exception as e:
    logging.warning(f"MongoDB initialization failed: {e}. App will continue with limited functionality.")

# Database connectivity check
@app.before_request
def check_db_connection():
    """Verify database is available before processing requests"""
    try:
        from models import is_db_connected
        if request.endpoint and request.endpoint not in ['static']:
            if not is_db_connected():
                logging.warning("Database connection check failed for request to endpoint: %s", request.endpoint)
    except Exception as e:
        logging.error(f"Error checking database connection: {e}")

bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)

if tf is not None:
    tf.get_logger().setLevel('ERROR')
    logging.getLogger("tensorflow").setLevel(logging.ERROR)
else:
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

@app.route("/api/health", methods=['GET'])
def health_check():
    """Check application and database health status"""
    from models import is_db_connected
    try:
        db_connected = is_db_connected()
        return jsonify({
            'status': 'healthy' if db_connected else 'degraded',
            'database': 'connected' if db_connected else 'disconnected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200 if db_connected else 503
    except Exception as e:
        logging.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

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
    # For MongoDB, user data is handled in templates via session
    return render_template("analytics.html", user={'name': 'User'})

@app.route("/signup", methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        try:
            name=request.form['name']
            phone=request.form['phone']
            email=request.form['email']
            password=request.form['password']
            confirm_password=request.form['Cpassword']

            # Check if passwords match
            if password != confirm_password:
                flash(" ΓÜá∩╕Å Passwords do not match!", "danger")
                return redirect(url_for('signup_page'))

            # Check if user already exists
            existing_user = find_user_by_email(email)
            if existing_user:
                flash("ΓÜá∩╕Å Email already registered!", "warning")
                return redirect(url_for('signup_page'))

            existing_phone = find_user_by_phone(phone)
            if existing_phone:
                flash("ΓÜá∩╕Å Phone number is already in use! Use another number.", "warning")
                return redirect(url_for('signup_page'))

            # Hash password and store user
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            result = create_user(name=name, phone=phone, email=email, password=hashed_password)
            if result is None:
                logging.error(f"Database operation failed during signup for email: {email}")
                flash("Γ¥î Database connection failed. MongoDB may not be running. Please ensure MongoDB is started (run: mongod --dbpath C:\\data\\db)", "danger")
                return redirect(url_for('signup_page'))
            flash("Signup successful! You can now log in.", "success")
            return redirect(url_for('login_page'))
        except KeyError as e:
            logging.error(f"Missing form field during signup: {e}")
            flash(f"Γ¥î Missing required field: {str(e)}", "danger")
            return redirect(url_for('signup_page'))
        except Exception as e:
            logging.error(f"Signup error: {type(e).__name__}: {e}", exc_info=True)
            flash(f"Γ¥î An error occurred during signup: {type(e).__name__}. Check server logs.", "danger")
            return redirect(url_for('signup_page'))

    return render_template('signup.html')

@app.route("/login",methods=['POST'])
def login():
    try:
        email=request.form.get("email")
        password=request.form.get("password")

        if not email or not password:
            flash("Missing email or password!", "warning")
            return redirect(url_for("login_page"))

        user = find_user_by_email(email)
        if user is None:
            flash("No account found with this email. Please sign up!","warning")
            return redirect(url_for("login_page"))

        if not bcrypt.check_password_hash(user['password'], password):
            flash("Incorrect password. Please try again!", "danger")
            return redirect(url_for("login_page"))

        # Create a new session record
        session_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(seconds=SESSION_TIMEOUT)

        session_result = create_session(
            user_id=str(user['_id']),
            session_token=session_token,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            expires_at=expires_at
        )
        
        if session_result is None:
            logging.error(f"Session creation failed for user: {user.get('email')}")
            flash("Γ¥î Session creation failed. MongoDB may not be running.", "danger")
            return redirect(url_for("login_page"))

        # Update last login time
        update_user_last_login(str(user['_id']))

        # Store session info in Flask session
        session["user_id"] = str(user['_id'])
        session["session_token"] = session_token
        session.permanent = True
        app.permanent_session_lifetime = timedelta(hours=24)

        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("userpage"))  # Redirect to user page
    except KeyError as e:
        logging.error(f"Missing form field during login: {e}")
        flash(f"Γ¥î Missing required field: {str(e)}", "danger")
        return redirect(url_for("login_page"))
    except Exception as e:
        logging.error(f"Login error: {type(e).__name__}: {e}", exc_info=True)
        flash(f"Γ¥î An error occurred during login: {type(e).__name__}. Check server logs.", "danger")
        return redirect(url_for("login_page"))


@app.route("/userpage")
def userpage():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    # For MongoDB, we don't need to fetch user data for template since it's handled differently
    return render_template("userpage.html", user={'name': 'User'})  # Placeholder

@app.route("/logout")
def logout():
    """Logout user and invalidate session"""
    if "session_token" in session:
        deactivate_session(session["session_token"])
    
    # Clear Flask session
    session.clear()
    flash("You have been logged out successfully!", "info")
    return redirect(url_for("login_page"))

@app.before_request
def check_session_validity():
    """Check if session is valid and not expired"""
    if "user_id" in session and "session_token" in session:
        # Check if session exists in database and is still active
        user_session = find_session_by_token(session["session_token"])

        if user_session:
            # Check if session has expired
            if datetime.utcnow() > user_session['expires_at']:
                session.clear()
                flash("Your session has expired. Please log in again.", "warning")
                if request.endpoint and request.endpoint != 'login_page' and request.endpoint != 'login':
                    return redirect(url_for("login_page"))
            else:
                # Update last activity
                update_session_activity(session["session_token"])
        else:
            # Session record not found in database, clear Flask session
            session.clear()
            flash("Invalid session. Please log in again.", "warning")
            if request.endpoint and request.endpoint != 'login_page' and request.endpoint != 'login':
                return redirect(url_for("login_page"))

@app.route("/session_status")
def session_status():
    """Get current session status"""
    if "user_id" not in session:
        return jsonify({"authenticated": False, "message": "No active session"}), 401

    user_session = find_session_by_token(session.get("session_token"))

    if not user_session:
        return jsonify({"authenticated": False, "message": "Session not found"}), 401

    return jsonify({
        "authenticated": True,
        "user_id": user_session['user_id'],
        "session_info": user_session
    }), 200

@app.route("/active_sessions")
def active_sessions():
    """Get all active sessions for current user"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_sessions = get_active_sessions(session["user_id"])

    return jsonify({
        "total_active_sessions": len(user_sessions),
        "sessions": user_sessions
    }), 200


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
    # For MongoDB, user data is handled via session
    return render_template("chat.html", user={'name': 'User'})


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
        chat_data = create_chat(
            user_id=session["user_id"],
            user_message=user_message,
            ai_response=ai_response,
            detected_emotion=emotion_label,
            emotion_score=float(emotion_score)
        )

        return jsonify({
            'user_message': user_message,
            'ai_response': ai_response,
            'emotion': emotion_label,
            'emotion_score': float(emotion_score),
            'timestamp': chat_data['timestamp']
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
        chats = get_user_chats(session["user_id"])
        return jsonify(chats), 200
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
        stats = get_chat_stats(session["user_id"], period)
        return jsonify(stats), 200
    except Exception as e:
        logging.error(f"Error calculating chat stats: {str(e)}")
        return jsonify({'error': 'Failed to calculate statistics'}), 500


# ==================== GLOBAL CHAT WITH LIVE STREAM ROUTES ====================

@app.route("/live-chat")
def live_chat():
    """Display the global live chat page with video stream"""
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    # For MongoDB, user data is handled via session
    return render_template("live_chat.html", user={'name': 'User'})

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
        user = find_user_by_id(session["user_id"])
        if not user:
            return jsonify({'error': 'User not found'}), 404

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
        global_chat_data = create_global_chat(
            user_id=session["user_id"],
            username=user['name'],
            user_message=user_message or f"[Detected face emotion: {face_emotion}]",
            ai_response=None,
            detected_text_emotion=text_emotion,
            detected_face_emotion=face_emotion,
            face_emotion_confidence=data.get('face_confidence'),
            emotion_score=emotion_score,
            is_ai_response=False
        )
        
        if global_chat_data is None:
            # Database operation failed, but still respond to client
            logging.warning("Failed to save user message to database")
            return jsonify({
                'success': True,
                'message': 'Message processed but could not be saved to history',
                'ai_response_text': ai_response
            }), 200

        # Save AI response if generated
        ai_chat_data = None
        if ai_response:
            ai_chat_data = create_global_chat(
                user_id='system',  # Use system user ID for AI responses
                username='AI Assistant',
                user_message=ai_response,
                ai_response=None,
                detected_text_emotion=None,
                detected_face_emotion=None,
                emotion_score=None,
                is_ai_response=True
            )

        return jsonify({
            'success': True,
            'message_id': str(global_chat_data['_id']) if global_chat_data else None,
            'user_message': global_chat_data,
            'ai_response': ai_chat_data,
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

        # Fetch most recent messages using MongoDB
        chats = get_global_chats(limit=limit)

        return jsonify({
            'total_messages': len(chats),
            'messages': chats
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

        # Use MongoDB function instead of SQLAlchemy
        stats = get_global_chat_stats(start_date)

        # Count unique participants from global chats
        all_chats = get_global_chats(limit=10000)  # Get a large number to count unique users
        unique_users = len(set(chat['user_id'] for chat in all_chats if not chat.get('is_ai_response', False)))

        return jsonify({
            'total_messages': len(all_chats),
            'unique_participants': unique_users,
            'text_emotion_distribution': stats.get('text_emotion_distribution', {}),
            'face_emotion_distribution': stats.get('face_emotion_distribution', {})
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

        # Get filtered user chats using MongoDB
        query = {'user_id': session["user_id"]}
        if start_date:
            query['timestamp'] = {'$gte': start_date}
        chats = list(mongo.db.chats.find(query).sort('timestamp', -1).limit(1000))  # Get more for stats

        # Get filtered global chats using MongoDB
        global_query = {}
        if start_date:
            global_query['timestamp'] = {'$gte': start_date}
        global_chats = list(mongo.db.global_chats.find(global_query).sort('timestamp', -1).limit(10000))

        # Calculate stats
        emotion_counts = {}
        for chat in chats:
            emotion = chat.get('detected_emotion') or 'unknown'
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        global_text_emotions = {}
        global_face_emotions = {}
        for chat in global_chats:
            if chat.get('detected_text_emotion'):
                global_text_emotions[chat['detected_text_emotion']] = global_text_emotions.get(chat['detected_text_emotion'], 0) + 1
            if chat.get('detected_face_emotion'):
                global_face_emotions[chat['detected_face_emotion']] = global_face_emotions.get(chat['detected_face_emotion'], 0) + 1

        unique_users = len(set(chat['user_id'] for chat in global_chats if not chat.get('is_ai_response', False)))

        # Create report data
        report_data = {
            'generated_at': datetime.utcnow().isoformat(),
            'period': period,
            'user_analytics': {
                'total_chats': len(chats),
                'emotion_distribution': emotion_counts,
                'chat_history': chats[-50:]  # Last 50 chats (already dicts)
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


if __name__ == "__main__":
    app.run(debug=True)
