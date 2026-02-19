from flask import Flask, request, jsonify,Response,json, render_template,flash,redirect,url_for,session,send_from_directory, send_file
import logging
import os
import sys
import uuid
from dotenv import load_dotenv
from datetime import datetime, timedelta
from language_utils import detect_language
from report_export import export_chat_to_excel

# Suppress TensorFlow warnings before importing (TF 2.20+ compatible)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

try:
    import tensorflow as tf
    # tf.get_logger() was removed in TF 2.20+, use logging module instead
    try:
        tf.get_logger().setLevel('ERROR')
    except AttributeError:
        logging.getLogger('tensorflow').setLevel(logging.ERROR)
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

from models import (
    mongo, create_user, find_user_by_email, find_user_by_phone, find_user_by_id,
    update_user_last_login, create_chat, get_user_chats, create_global_chat,
    get_global_chats, create_session, find_session_by_token,
    update_session_activity, deactivate_session, get_active_sessions,
    get_chat_stats
)  # Import MongoDB functions from models.py
# alias global chat stats separately to avoid naming conflict with route
from models import get_global_chat_stats as model_get_global_chat_stats
from deep_translator import GoogleTranslator
from werkzeug.utils import secure_filename
from bson import ObjectId
from flask_bcrypt import Bcrypt

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

bcrypt = Bcrypt(app)

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

# Error handlers to return JSON instead of HTML
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    logging.error(f"Unhandled exception: {str(error)}")
    return jsonify({'error': 'An unexpected error occurred'}), 500

if tf is not None:
    try:
        tf.get_logger().setLevel('ERROR')
    except AttributeError:
        pass  # tf.get_logger() removed in TF 2.20+
logging.getLogger("tensorflow").setLevel(logging.ERROR)

# Load ML modules at startup
load_ml_modules()

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


def parse_period_dates(period, start_str=None, end_str=None):
    """Return a (start_date, end_date) tuple based on query params.
    If explicit start/end strings are provided they take precedence.
    Otherwise fall back to the simple period shortcuts handled by
    :func:`get_date_filter`.

    The strings are expected to be ISO‑formatted timestamps from the
    front end (e.g. produced by <input type="datetime-local"/>).
    """
    start_date = None
    end_date = None

    # parse explicit values first
    if start_str:
        try:
            start_date = datetime.fromisoformat(start_str)
        except Exception:
            logger.warning(f"Invalid start date format: {start_str}")
    if end_str:
        try:
            end_date = datetime.fromisoformat(end_str)
        except Exception:
            logger.warning(f"Invalid end date format: {end_str}")

    # if neither explicit value given, derive from period
    if not start_date and not end_date:
        start_date = get_date_filter(period)
    return start_date, end_date

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
        is_api = request.path.startswith('/api/')

        if user_session:
            # Check if session has expired
            if datetime.utcnow() > user_session['expires_at']:
                session.clear()
                if is_api:
                    return jsonify({'error': 'Session expired. Please log in again.', 'redirect': '/login_page'}), 401
                flash("Your session has expired. Please log in again.", "warning")
                if request.endpoint and request.endpoint != 'login_page' and request.endpoint != 'login':
                    return redirect(url_for("login_page"))
            else:
                # Update last activity
                update_session_activity(session["session_token"])
        else:
            # Session record not found in database, clear Flask session
            session.clear()
            if is_api:
                return jsonify({'error': 'Invalid session. Please log in again.', 'redirect': '/login_page'}), 401
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
    try:
        # Ensure ML modules are loaded
        if not ML_AVAILABLE or detect_text_emotion is None:
            load_ml_modules()
            if not ML_AVAILABLE:
                return jsonify({'error': 'ML modules not available. Please try again.', 'success': False}), 503
        
        data = request.json
        text = data.get("text", "")

        if not text.strip():
            return jsonify({'error': 'No text provided'}), 400

        emotion, status_code = detect_text_emotion(text)  
        return jsonify(emotion), status_code
    except Exception as e:
        logging.error(f"Text emotion detection error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route("/detect_text_emotion", methods=['POST'])
def detect_text_emotion_endpoint():
    """
    Main endpoint for text emotion detection
    Used by text_detection.html frontend
    """
    try:
        # Ensure ML modules are loaded
        if not ML_AVAILABLE or detect_text_emotion is None:
            load_ml_modules()
            if not ML_AVAILABLE:
                return jsonify({'error': 'ML modules not available. Please try again.', 'success': False}), 503
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        text = data.get("text", "")

        if not text.strip():
            return jsonify({'error': 'Please enter a statement.', 'success': False}), 400

        # Call the detection function
        emotion_result, status_code = detect_text_emotion(text)
        
        if status_code == 200:
            # Format response for frontend compatibility
            response = {
                'emotion': emotion_result.get('Dominant_emotion', {}).get('label', 'neutral'),
                'confidence': emotion_result.get('Dominant_emotion', {}).get('score', 0.5),
                'percentage': emotion_result.get('Dominant_emotion', {}).get('percentage', 0),
                'emotion_analysis': emotion_result.get('Emotion Analysis', []),
                'analysis_report': emotion_result.get('analysis_report', ''),
                'key_indicators': emotion_result.get('key_indicators', []),
                'emotional_intensity': emotion_result.get('emotional_intensity', 'Unknown'),
                'model_used': emotion_result.get('model_used', 'unknown'),
                'detected_language': emotion_result.get('detected_language', 'en'),
                'language_name': emotion_result.get('language_name', 'English'),
                'was_translated': emotion_result.get('was_translated', False),
                'success': True
            }

            # Save to analytics if user is logged in
            if "user_id" in session:
                try:
                    create_chat(
                        user_id=session["user_id"],
                        user_message=f"[Text Analysis] {text[:100]}",
                        ai_response=response.get('analysis_report'),
                        detected_emotion=response['emotion'],
                        emotion_score=float(response['confidence']),
                        detected_language=response['detected_language'],
                        language_name=response['language_name']
                    )
                except Exception as e:
                    logging.warning(f"Failed to save text emotion analytics: {e}")

            return jsonify(response), 200
        else:
            return jsonify({
                'error': emotion_result.get('error', 'Emotion detection failed'),
                'success': False
            }), status_code
            
    except Exception as e:
        logging.error(f"Text emotion detection error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route("/get_text_detection_history", methods=['GET'])
def get_text_detection_history():
    """
    Get text detection history for the current user
    Used by text_detection.html to display history
    """
    try:
        if "user_id" not in session:
            # Return empty history for non-logged-in users
            return jsonify({'detections': []}), 200
        
        user_id = session["user_id"]
        
        # Query text detections from MongoDB
        detections = list(mongo.db.chats.find(
            {'user_id': user_id, 'detected_emotion': {'$exists': True}}
        ).sort('timestamp', -1).limit(20))
        
        # Format detections for frontend
        result = []
        for det in detections:
            result.append({
                'text': det.get('user_message', ''),
                'emotion': det.get('detected_emotion', 'neutral'),
                'confidence': det.get('emotion_score', 0.5),
                'timestamp': det.get('timestamp', datetime.now()).isoformat() if isinstance(det.get('timestamp'), datetime) else str(det.get('timestamp', ''))
            })
        
        return jsonify({'detections': result}), 200
        
    except Exception as e:
        logging.error(f"Error fetching text detection history: {str(e)}")
        return jsonify({'detections': [], 'error': str(e)}), 500


@app.route("/api/track-emotion", methods=['POST'])
def track_emotion():
    """
    Track emotion detection result
    Used by text_detection.html to save detection results
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        emotion = data.get('emotion', 'neutral')
        source = data.get('source', 'text')
        confidence = data.get('confidence', 0.5)
        text = data.get('text', '')  # Get the actual text from the request
        
        # If user is logged in, save to their history
        if "user_id" in session:
            user_id = session["user_id"]
            try:
                # Create a chat entry to track the emotion with the actual text
                # Use distinct prefix for live camera detections
                if source == 'live_camera':
                    default_msg = '[Live Detection] Camera Emotion Scan'
                else:
                    default_msg = f'[Text Emotion Detection: {source}]'
                chat_data = create_chat(
                    user_id=user_id,
                    user_message=text if text else default_msg,
                    ai_response=None,
                    detected_emotion=emotion,
                    emotion_score=float(confidence),
                    detected_language='en',
                    language_name='English'
                )
                return jsonify({'success': True, 'tracked': True}), 200
            except Exception as e:
                logging.warning(f"Failed to save emotion tracking: {e}")
                return jsonify({'success': True, 'tracked': False}), 200
        
        return jsonify({'success': True, 'tracked': False}), 200
        
    except Exception as e:
        logging.error(f"Error tracking emotion: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route("/image_upload",methods=['POST'])
def upload_image():
    try:
        # Ensure ML modules are loaded
        if not ML_AVAILABLE or process_image is None:
            load_ml_modules()
            if not ML_AVAILABLE:
                return jsonify({"error": "ML modules not available. Please try again.", "success": False}), 503
        
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
        return jsonify({"error": str(e), "success": False}), 500

@app.route("/detect_image_emotion", methods=['POST'])
def detect_image_emotion():
    """API endpoint for image emotion detection - used by image_detection.html"""
    try:
        # Ensure ML modules are loaded
        if not ML_AVAILABLE or process_image is None:
            load_ml_modules()
            if not ML_AVAILABLE:
                return jsonify({"error": "ML modules not available. Please try again.", "success": False}), 503
        
        # The frontend sends the file with field name 'image'
        file = request.files.get("image") or request.files.get("file")
        if file:
            response = process_image(file)

            # Save to analytics if user is logged in
            if "user_id" in session and response.get("success", False):
                try:
                    # Use a descriptive message or filename for the log
                    msg = f"[Image Analysis] {file.filename}" if hasattr(file, 'filename') else "[Image Analysis]"
                    
                    create_chat(
                        user_id=session["user_id"],
                        user_message=msg,
                        ai_response=response.get("analysis_report", None),
                        detected_emotion=response.get("emotion", "neutral"),
                        emotion_score=float(response.get("confidence", 0.0)),
                        detected_language='en',
                        language_name='English'
                    )
                except Exception as e:
                    logging.warning(f"Failed to save image emotion analytics: {e}")

            return jsonify(response)
        elif request.is_json and "image_base64" in request.json:
            response = process_image()
            return jsonify(response)
        return jsonify({"error": "No valid image provided"}), 400
    except Exception as e:
        logging.error(f"Image emotion detection error: {str(e)}")
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/get_image_detection_history", methods=['GET'])
def get_image_detection_history():
    """Get image detection history for the current user"""
    try:
        if "user_id" not in session:
            return jsonify({'detections': []}), 200
        
        user_id = session["user_id"]
        
        # Query image detections from MongoDB
        detections = list(mongo.db.chats.find(
            {'user_id': user_id, 'detected_emotion': {'$exists': True}}
        ).sort('timestamp', -1).limit(20))
        
        result = []
        for det in detections:
            result.append({
                'emotion': det.get('detected_emotion', 'neutral'),
                'confidence': det.get('emotion_score', 0.5),
                'image_path': det.get('image_path', ''),
                'timestamp': det.get('timestamp', datetime.now()).isoformat() if isinstance(det.get('timestamp'), datetime) else str(det.get('timestamp', ''))
            })
        
        return jsonify({'detections': result}), 200
        
    except Exception as e:
        logging.error(f"Error fetching image detection history: {str(e)}")
        return jsonify({'detections': [], 'error': str(e)}), 500


@app.route("/video_upload", methods=["POST"])
def video_upload():
    try:
        # Ensure ML modules are loaded
        if not ML_AVAILABLE or process_video is None:
            load_ml_modules()
            if not ML_AVAILABLE:
                return jsonify({"error": "ML modules not available. Please try again.", "success": False}), 503
        
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file provided"}), 400

        result = process_video(file)

        # Save to analytics if user is logged in and detection succeeded
        if isinstance(result, dict) and result.get("success", False) and "user_id" in session:
            try:
                msg = f"[Video Analysis] {file.filename}" if hasattr(file, 'filename') else "[Video Analysis]"
                dominant = result.get("dominant_emotion", "neutral")
                confidence = float(result.get("dominant_emotion_confidence", 0.0))
                create_chat(
                    user_id=session["user_id"],
                    user_message=msg,
                    ai_response=None,
                    detected_emotion=dominant,
                    emotion_score=confidence,
                    detected_language='en',
                    language_name='English'
                )
            except Exception as e:
                logging.warning(f"Failed to save video upload analytics: {e}")

        return result
    except Exception as e:
        logging.error(f"Video upload error: {str(e)}")
        return jsonify({"error": str(e), "success": False}), 500

@app.route("/detect_video_emotion", methods=['POST'])
def detect_video_emotion():
    """API endpoint for video emotion detection - used by video_detection.html"""
    try:
        # Ensure ML modules are loaded
        if not ML_AVAILABLE or process_video is None:
            load_ml_modules()
            if not ML_AVAILABLE:
                return jsonify({"error": "ML modules not available. Please try again.", "success": False}), 503
        
        # The frontend sends the file with field name 'video'
        file = request.files.get("video") or request.files.get("file")
        if not file:
            return jsonify({"error": "No video file provided"}), 400

        result = process_video(file)

        # Save to analytics if user is logged in and detection succeeded
        if "user_id" in session and result.get("success", False):
            try:
                msg = f"[Video Analysis] {file.filename}" if hasattr(file, 'filename') else "[Video Analysis]"
                dominant = result.get("dominant_emotion", "neutral")
                confidence = float(result.get("dominant_emotion_confidence", 0.0))
                create_chat(
                    user_id=session["user_id"],
                    user_message=msg,
                    ai_response=None,
                    detected_emotion=dominant,
                    emotion_score=confidence,
                    detected_language='en',
                    language_name='English'
                )
            except Exception as e:
                logging.warning(f"Failed to save video emotion analytics: {e}")

        # Ensure all values are JSON-serializable (convert numpy types)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Video emotion detection error: {str(e)}")
        return jsonify({"error": str(e), "success": False}), 500

@app.route("/detect_live_emotion", methods=["POST"])
def detect_live_emotion():
    """
    Detect emotion from live video frame (base64 image)
    Used by live_chat.html for real-time emotion detection
    """
    try:
        if not ML_AVAILABLE:
            load_ml_modules()
            if not ML_AVAILABLE:
                return jsonify({"error": "ML modules not available. Please try again.", "success": False}), 503
        
        # Import necessary libraries
        import base64
        from io import BytesIO
        import numpy as np
        from PIL import Image

        # Check for file upload (multipart/form-data) or JSON base64
        image_np = None
        
        if 'image' in request.files:
            file = request.files['image']
            image = Image.open(file.stream).convert('RGB')
            image_np = np.array(image)
        else:
            # Fallback to base64 from JSON
            data = request.json or {}
            image_base64 = data.get("image_base64")
            
            if image_base64:
                # Decode base64 to image
                import base64
                from io import BytesIO
                image_data = base64.b64decode(image_base64.split(",")[1] if "," in image_base64 else image_base64)
                image = Image.open(BytesIO(image_data)).convert('RGB')
                image_np = np.array(image)
        
        if image_np is None:
            return jsonify({"error": "No image data provided"}), 400
            
        # Convert RGB to BGR for DeepFace (OpenCV format)
        if len(image_np.shape) == 3 and image_np.shape[2] == 3:
            image_np = image_np[:, :, ::-1].copy()
        
        # Use DeepFace for emotion detection
        # Ensure deepface path is set up (should be done by load_ml_modules or top level)
        try:
            from deepface import DeepFace
        except ImportError:
             # Setup local DeepFace path if import fails
             sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deepface'))
             from deepface import DeepFace

        result = DeepFace.analyze(
            image_np,
            actions=['emotion'],
            enforce_detection=False,
            silent=True
        )
        
        if result and isinstance(result, list) and len(result) > 0:
            # DeepFace returns numpy floats, convert to native Python float
            emotion_dict = {k: float(v) for k, v in result[0]['emotion'].items()}
            detected_emotion = result[0]['dominant_emotion']
            confidence = float(emotion_dict.get(detected_emotion, 0)) / 100
            
            # Extract face region for bounding box
            region = result[0].get('region', {})
            face_box = {
                'x': int(region.get('x', 0)),
                'y': int(region.get('y', 0)),
                'w': int(region.get('w', 0)),
                'h': int(region.get('h', 0))
            }
            
            return jsonify({
                "emotion": detected_emotion,
                "confidence": round(confidence, 4),
                "confidence_percentage": round(confidence * 100, 2),
                "emotion_scores": emotion_dict,
                "region": face_box,
                "success": True
            }), 200
        else:
            return jsonify({
                "error": "No face detected",
                "success": False
            }), 200 # Return 200 with success=False so frontend handles it gracefully
            
    except Exception as e:
        logging.error(f"Live emotion detection error: {str(e)}")
        return jsonify({"error": str(e), "success": False}), 500

@app.route("/multilang_text", methods=['POST'])
def multilang_text():
    try:
        # Ensure ML modules are loaded
        if not ML_AVAILABLE or detect_text_emotion is None:
            load_ml_modules()
            if not ML_AVAILABLE:
                return jsonify({"error": "ML modules not available. Please try again.", "success": False}), 503
        
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
    """Handle chat messages and emotion-based responses with multilingual support"""
    try:
        if "user_id" not in session:
            logging.warning("Chat request without user_id in session")
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.json
        if not data:
            logging.warning("No JSON data in chat request")
            return jsonify({'error': 'No data provided'}), 400
            
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400

        logging.info(f"Processing chat message from user {session['user_id'][:8]}: {user_message[:50]}...")

        try:
            # Ensure ML modules are loaded
            if not ML_AVAILABLE or detect_text_emotion is None or generate_emotion_aware_response is None:
                logging.info("ML modules not available, loading...")
                load_ml_modules()
                if not ML_AVAILABLE:
                    return jsonify({'error': 'ML modules not available. Please try again.', 'success': False}), 503
            
            # Detect user language
            try:
                user_language, lang_name, _ = detect_language(user_message)
                logging.info(f"Detected user language: {lang_name} ({user_language})")
            except Exception as e:
                logging.warning(f"Language detection failed: {e}. Defaulting to English.")
                user_language = 'en'
                lang_name = 'English'
            
            # Detect emotion in user's message
            try:
                emotion_response, status_code = detect_text_emotion(user_message, user_language)
                logging.info(f"Emotion detection status: {status_code}")

                if status_code != 200:
                    # If emotion detection fails, use neutral response
                    logging.warning(f"Emotion detection failed with status {status_code}: {emotion_response}")
                    emotion_label = "neutral"
                    emotion_score = 0.5
                else:
                    emotion_label = emotion_response.get('Dominant_emotion', {}).get('label', 'neutral')
                    emotion_score = emotion_response.get('Dominant_emotion', {}).get('score', 0.5)
                    logging.info(f"Detected emotion: {emotion_label} with score {emotion_score}")
            except Exception as e:
                logging.error(f"Emotion detection exception: {str(e)}")
                emotion_label = "neutral"
                emotion_score = 0.5

            # Generate emotion-aware response in user's language
            try:
                ai_response = generate_emotion_aware_response(user_message, emotion_label, emotion_score, user_language)
                logging.info("Generated AI response successfully")
            except Exception as e:
                logging.error(f"Response generation failed: {str(e)}")
                ai_response = "Thank you for sharing. I'm here to listen. Tell me more about what you're thinking."

            # Save chat to database
            try:
                chat_data = create_chat(
                    user_id=session["user_id"],
                    user_message=user_message,
                    ai_response=ai_response,
                    detected_emotion=emotion_label,
                    emotion_score=float(emotion_score),
                    detected_language=user_language,
                    language_name=lang_name
                )
                logging.info(f"Chat saved to database: {chat_data}")
            except Exception as e:
                logging.error(f"Database save failed: {str(e)}")
                chat_data = None

            return jsonify({
                'user_message': user_message,
                'ai_response': ai_response,
                'emotion': emotion_label,
                'emotion_score': float(emotion_score),
                'language': user_language,
                'language_name': lang_name,
                'timestamp': chat_data['timestamp'].isoformat() if chat_data and isinstance(chat_data.get('timestamp'), datetime) else datetime.now().isoformat()
            }), 200

        except Exception as e:
            logging.error(f"Chat processing error: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to process message: {str(e)}', 'ai_response': 'I had trouble processing that. Please try again.'}), 200

    except Exception as e:
        logging.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route("/api/chat-history", methods=['GET'])
def get_chat_history():
    """Get user's chat history"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        raw_chats = get_user_chats(session["user_id"])
        chats = []
        for chat in raw_chats:
            # Determine source based on content
            source = 'Chat'
            msg = chat.get('user_message', '')
            if msg.startswith('[Live Detection]') or 'live_camera' in msg:
                source = 'Live'
            elif msg.startswith('[Text Analysis]') or '[Text Emotion Detection:' in msg:
                source = 'Text'
            elif '[Image Analysis]' in msg:
                source = 'Image'
            elif '[Video Analysis]' in msg:
                source = 'Video'
            
            # Format timestamp — append 'Z' so the browser treats it as UTC
            timestamp = chat.get('timestamp')
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat() + 'Z'
            elif timestamp:
                timestamp = str(timestamp)
            else:
                timestamp = ''
            
            chat_data = {
                'user_message': msg,
                'detected_emotion': chat.get('detected_emotion', 'neutral'),
                'timestamp': timestamp,
                'source': source
            }
            chats.append(chat_data)
            
        return jsonify(chats), 200
    except Exception as e:
        logging.error(f"Error fetching chat history: {str(e)}")
        return jsonify({'error': 'Failed to fetch chat history'}), 500


@app.route("/api/chat-stats", methods=['GET'])
def chat_stats_endpoint():
    """Get emotion statistics from chat history"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        period = request.args.get('period', 'all')
        start_str = request.args.get('start')
        end_str = request.args.get('end')
        start_date, end_date = parse_period_dates(period, start_str, end_str)
        stats = get_chat_stats(session["user_id"], start_date, end_date)
        return jsonify(stats), 200
    except Exception as e:
        logging.error(f"Error calculating chat stats: {str(e)}")
        return jsonify({'error': 'Failed to calculate statistics'}), 500


@app.route("/api/emotions-summary", methods=['GET'])
def get_emotions_summary():
    """Get aggregated emotion statistics for the dashboard"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        user_id = session["user_id"]
        period = request.args.get('period', 'all')
        start_str = request.args.get('start')
        end_str = request.args.get('end')
        start_date, end_date = parse_period_dates(period, start_str, end_str)

        # Query chat history
        query = {'user_id': user_id}
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        chats = list(mongo.db.chats.find(query).sort('timestamp', -1))
        
        # Aggregate data
        total_emotions = len(chats)
        emotion_counts = {}
        source_counts = {'Text': 0, 'Image': 0, 'Video': 0, 'Live': 0, 'Chat': 0}
        
        for chat in chats:
            # Emotion distribution
            emotion = chat.get('detected_emotion')
            if emotion:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            # Source distribution
            msg = chat.get('user_message', '')
            if msg.startswith('[Live Detection]') or 'live_camera' in msg:
                source_counts['Live'] += 1
            elif msg.startswith('[Text Analysis]') or '[Text Emotion Detection:' in msg:
                source_counts['Text'] += 1
            elif '[Image Analysis]' in msg:
                source_counts['Image'] += 1
            elif '[Video Analysis]' in msg:
                source_counts['Video'] += 1
            else:
                source_counts['Chat'] += 1

        # Format recent activity (convert non-serializable types)
        recent_activity = []
        for chat in chats[:10]:
            ts = chat.get('timestamp')
            msg = chat.get('user_message', '')
            # Determine source from message prefix
            if msg.startswith('[Live Detection]') or 'live_camera' in msg:
                source = 'Live'
            elif msg.startswith('[Text Analysis]') or '[Text Emotion Detection:' in msg:
                source = 'Text'
            elif msg.startswith('[Image Analysis]') or '[Image Analysis]' in msg:
                source = 'Image'
            elif msg.startswith('[Video Analysis]') or '[Video Analysis]' in msg:
                source = 'Video'
            else:
                source = 'Chat'
            recent_activity.append({
                'user_message': msg,
                'detected_emotion': chat.get('detected_emotion', 'neutral'),
                'emotion_score': float(chat.get('emotion_score', 0.5)),
                'timestamp': ts.isoformat() + 'Z' if isinstance(ts, datetime) else str(ts or ''),
                'detected_language': chat.get('detected_language', 'en'),
                'language_name': chat.get('language_name', 'English'),
                'source': source,
            })

        return jsonify({
            'total_emotions': total_emotions,
            'emotion_distribution': emotion_counts,
            'source_distribution': source_counts,
            'recent_activity': recent_activity
        }), 200

    except Exception as e:
        logging.error(f"Error summarising emotions: {str(e)}")
        return jsonify({'error': 'Failed to summarize emotions'}), 500


# ==================== ACCOUNT SETTINGS ROUTES ====================

@app.route("/api/change-password", methods=['POST'])
def change_password():
    """Change user password"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        data = request.json
        current_pw = data.get('current_password', '')
        new_pw = data.get('new_password', '')
        confirm_pw = data.get('confirm_password', '')

        if not current_pw or not new_pw:
            return jsonify({'error': 'All fields are required'}), 400
        if new_pw != confirm_pw:
            return jsonify({'error': 'New passwords do not match'}), 400
        if len(new_pw) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if not bcrypt.check_password_hash(user['password'], current_pw):
            return jsonify({'error': 'Current password is incorrect'}), 400

        hashed = bcrypt.generate_password_hash(new_pw).decode('utf-8')
        mongo.db.users.update_one({'_id': ObjectId(session['user_id'])}, {'$set': {'password': hashed}})
        return jsonify({'success': True, 'message': 'Password changed successfully'}), 200
    except Exception as e:
        logging.error(f"Change password error: {e}")
        return jsonify({'error': 'Failed to change password'}), 500


@app.route("/api/update-preferences", methods=['POST'])
def update_preferences():
    """Update user preferences"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        data = request.json or {}
        prefs = {
            'theme': data.get('theme', 'dark'),
            'language': data.get('language', 'en'),
            'auto_detect': data.get('auto_detect', True),
        }
        mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {'preferences': prefs}}
        )
        return jsonify({'success': True, 'message': 'Preferences updated'}), 200
    except Exception as e:
        logging.error(f"Update preferences error: {e}")
        return jsonify({'error': 'Failed to update preferences'}), 500


@app.route("/api/update-privacy", methods=['POST'])
def update_privacy():
    """Update user privacy settings"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        data = request.json or {}
        privacy = {
            'share_analytics': data.get('share_analytics', False),
            'public_profile': data.get('public_profile', False),
            'save_history': data.get('save_history', True),
        }
        mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {'privacy': privacy}}
        )
        return jsonify({'success': True, 'message': 'Privacy settings updated'}), 200
    except Exception as e:
        logging.error(f"Update privacy error: {e}")
        return jsonify({'error': 'Failed to update privacy settings'}), 500


@app.route("/api/update-notifications", methods=['POST'])
def update_notifications():
    """Update notification preferences"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        data = request.json or {}
        notifs = {
            'email_alerts': data.get('email_alerts', True),
            'emotion_reports': data.get('emotion_reports', True),
            'weekly_summary': data.get('weekly_summary', False),
        }
        mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {'notifications': notifs}}
        )
        return jsonify({'success': True, 'message': 'Notification settings updated'}), 200
    except Exception as e:
        logging.error(f"Update notifications error: {e}")
        return jsonify({'error': 'Failed to update notifications'}), 500


@app.route("/api/get-settings", methods=['GET'])
def get_settings():
    """Get user settings (preferences, privacy, notifications)"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({
            'preferences': user.get('preferences', {'theme': 'dark', 'language': 'en', 'auto_detect': True}),
            'privacy': user.get('privacy', {'share_analytics': False, 'public_profile': False, 'save_history': True}),
            'notifications': user.get('notifications', {'email_alerts': True, 'emotion_reports': True, 'weekly_summary': False}),
        }), 200
    except Exception as e:
        logging.error(f"Get settings error: {e}")
        return jsonify({'error': 'Failed to get settings'}), 500


# ==================== GLOBAL CHAT WITH LIVE STREAM ROUTES ====================

@app.route("/live-chat")
def live_chat():
    """Display the global live chat page with video stream"""
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    # For MongoDB, user data is handled via session
    return render_template("live_chat.html", user={'name': 'User'})

@app.route("/api/global-chat", methods=['POST'])
@app.route("/api/send-global-chat", methods=['POST'])
def post_global_chat():
    """Post a message to global chat with emotion detection with multilingual support
    This endpoint allows anonymous access to the global chat"""
    
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    user_message = data.get('message', '').strip()
    face_emotion = data.get('face_emotion')  # Emotion detected from live video feed

    if not user_message and not face_emotion:
        return jsonify({'error': 'Message or face emotion must be provided'}), 400

    try:
        # Ensure ML modules are loaded
        if not ML_AVAILABLE or detect_text_emotion is None or generate_emotion_aware_response is None:
            logging.info("ML modules not available, loading...")
            load_ml_modules()
            if not ML_AVAILABLE:
                return jsonify({'error': 'ML modules not available. Please try again.', 'success': False}), 503
        
        # Get or create anonymous user_id for session tracking
        if "user_id" not in session:
            session["user_id"] = f"anonymous_{uuid.uuid4()}"
            session.permanent = True
            app.permanent_session_lifetime = timedelta(hours=24)
            logging.info(f"Created anonymous session: {session['user_id']}")
        
        user_id = session["user_id"]
        username = "Anonymous"
        
        text_emotion = None
        ai_response = None
        emotion_score = None
        user_language = 'en'
        lang_name = 'English'

        # Detect user language and emotion from text if message provided
        if user_message:
            try:
                user_language, lang_name, _ = detect_language(user_message)
                logging.info(f"Global chat - Detected user language: {lang_name} ({user_language})")
            except Exception as e:
                logging.warning(f"Language detection failed: {e}. Defaulting to English.")
                user_language = 'en'
                lang_name = 'English'
            
            try:
                emotion_response, status_code = detect_text_emotion(user_message, user_language)
                if status_code == 200:
                    text_emotion = emotion_response.get('Dominant_emotion', {}).get('label', 'neutral')
                    emotion_score = emotion_response.get('Dominant_emotion', {}).get('score', 0.5)
                    logging.info(f"Detected emotion: {text_emotion}")
            except Exception as e:
                logging.error(f"Emotion detection failed: {str(e)}")
                text_emotion = 'neutral'
                emotion_score = 0.5

        # Generate AI response based on emotions with language support
        try:
            if user_message:
                ai_response = generate_emotion_aware_response(
                    user_message, 
                    text_emotion or 'neutral', 
                    emotion_score or 0.5, 
                    user_language
                )
                logging.info("Generated AI response successfully")
            elif face_emotion:
                ai_response = f"Based on your facial expression showing {face_emotion}, I'm here to support you. How are you feeling?"
        except Exception as e:
            logging.error(f"AI response generation failed: {str(e)}")
            ai_response = "I appreciate you sharing with me. Please tell me more about what you're experiencing."

        # Save user message to global chat
        try:
            global_chat_data = create_global_chat(
                user_id=user_id,
                username=username,
                user_message=user_message or f"[Detected face emotion: {face_emotion}]",
                ai_response=None,
                detected_text_emotion=text_emotion,
                detected_face_emotion=face_emotion,
                face_emotion_confidence=data.get('face_confidence'),
                emotion_score=emotion_score,
                detected_language=user_language,
                language_name=lang_name,
                is_ai_response=False
            )
            logging.info(f"Saved user message to global chat")
        except Exception as e:
            logging.error(f"Failed to save user message: {str(e)}")
            global_chat_data = None
        
        if global_chat_data is None:
            # Database operation failed, but still respond to client
            logging.warning("Failed to save user message to database")
            return jsonify({
                'success': True,
                'message': 'Message processed but could not be saved to history',
                'ai_response_text': ai_response,
                'language': user_language,
                'language_name': lang_name
            }), 200

        # Save AI response if generated
        ai_chat_data = None
        if ai_response:
            try:
                ai_chat_data = create_global_chat(
                    user_id='system',  # Use system user ID for AI responses
                    username='AI Assistant',
                    user_message=ai_response,
                    ai_response=None,
                    detected_text_emotion=None,
                    detected_face_emotion=None,
                    emotion_score=None,
                    detected_language=user_language,
                    language_name=lang_name,
                    is_ai_response=True
                )
                logging.info("Saved AI response to global chat")
            except Exception as e:
                logging.error(f"Failed to save AI response: {str(e)}")
                ai_chat_data = None

        return jsonify({
            'success': True,
            'message_id': str(global_chat_data['_id']) if global_chat_data else None,
            'user_message': global_chat_data,
            'ai_response': ai_chat_data,
            'ai_response_text': ai_response,
            'language': user_language,
            'language_name': lang_name,
            'emotion': text_emotion or face_emotion
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

        # Map fields for frontend compatibility
        messages = []
        for chat in chats:
            messages.append({
                'username': chat.get('username', 'Anonymous'),
                'message': chat.get('user_message', ''),
                'emotion': chat.get('detected_text_emotion') or chat.get('detected_face_emotion') or 'neutral',
                'confidence': chat.get('emotion_score', 0.5),
                'timestamp': chat.get('timestamp').isoformat() if hasattr(chat.get('timestamp', ''), 'isoformat') else str(chat.get('timestamp', '')),
                'is_ai_response': chat.get('is_ai_response', False),
                'user_id': chat.get('user_id', '')
            })

        return jsonify({
            'total_messages': len(messages),
            'messages': messages
        }), 200
    except Exception as e:
        logging.error(f"Error fetching global chat history: {str(e)}")
        return jsonify({'error': 'Failed to fetch chat history'}), 500


@app.route("/api/global-chat-users", methods=['GET'])
def get_global_chat_users():
    """Get list of active users in global chat"""
    try:
        # Get recent chats to find active users
        chats = get_global_chats(limit=100)
        seen_users = set()
        users = []
        for chat in chats:
            user_id = chat.get('user_id', '')
            if user_id and user_id != 'system' and user_id not in seen_users:
                seen_users.add(user_id)
                users.append({
                    'username': chat.get('username', 'Anonymous'),
                    'user_id': user_id
                })
        return jsonify({'users': users}), 200
    except Exception as e:
        logging.error(f"Error fetching global chat users: {str(e)}")
        return jsonify({'users': []}), 200


@app.route("/api/global-chat-stats", methods=['GET'])
def get_global_chat_stats():
    """Get statistics about global chat emotions and participants"""
    try:
        period = request.args.get('period', 'all')
        start_str = request.args.get('start')
        end_str = request.args.get('end')
        start_date, end_date = parse_period_dates(period, start_str, end_str)

        # Use MongoDB function instead of SQLAlchemy
        stats = model_get_global_chat_stats(start_date, end_date)

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


@app.route("/api/export-chat-report", methods=['GET'])
def export_chat_report():
    """Export chat history to Excel file with emotion data, domain name, and timestamps"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get parameters
        period = request.args.get('period', 'all')
        domain_name = request.args.get('domain', 'EmotiChat')
        start_str = request.args.get('start')
        end_str = request.args.get('end')
        start_date, end_date = parse_period_dates(period, start_str, end_str)

        # Query user chats from MongoDB
        query = {'user_id': session["user_id"]}
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        # Convert MongoDB cursor to list and add domain/timestamp info
        raw_chats = list(mongo.db.chats.find(query).sort('timestamp', -1))
        
        # Format chats for report
        chats = []
        for chat in raw_chats:
            # Convert ObjectId to string
            chat_data = {
                'timestamp': chat.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S') if isinstance(chat.get('timestamp'), datetime) else str(chat.get('timestamp', '')),
                'username': chat.get('username', 'User'),
                'user_message': chat.get('user_message', ''),
                'ai_response': chat.get('ai_response', ''),
                'detected_emotion': chat.get('detected_emotion', 'neutral'),
                'emotion_score': chat.get('emotion_score', 0),
                'detected_language': chat.get('detected_language', 'en'),
                'language_name': chat.get('language_name', 'English'),
            }
            chats.append(chat_data)
        
        if not chats:
            return jsonify({'error': 'No chat data found for this period'}), 404
        
        # Export to Excel
        excel_file = export_chat_to_excel(chats, domain_name=domain_name)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"EmotiChat_Report_{domain_name}_{timestamp}.xlsx"
        
        # Return file
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logging.error(f"Chat report export error: {str(e)}")
        return jsonify({'error': f'Failed to export report: {str(e)}'}), 500


@app.route("/api/export-global-chat-report", methods=['GET'])
def export_global_chat_report():
    """Export global chat history to Excel file with all participants, emotions, and timestamps"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get parameters
        period = request.args.get('period', 'all')
        domain_name = request.args.get('domain', 'EmotiChat Global')
        start_str = request.args.get('start')
        end_str = request.args.get('end')
        start_date, end_date = parse_period_dates(period, start_str, end_str)

        # Query global chats from MongoDB
        query = {'is_ai_response': {'$ne': True}}  # Exclude AI responses to avoid duplicates
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        # Convert MongoDB cursor to list
        raw_chats = list(mongo.db.global_chats.find(query).sort('timestamp', -1).limit(5000))
        
        # Format chats for report
        chats = []
        for chat in raw_chats:
            chat_data = {
                'timestamp': chat.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S') if isinstance(chat.get('timestamp'), datetime) else str(chat.get('timestamp', '')),
                'username': chat.get('username', 'Anonymous'),
                'user_message': chat.get('user_message', ''),
                'ai_response': chat.get('ai_response', ''),
                'detected_emotion': chat.get('detected_text_emotion') or chat.get('detected_face_emotion') or 'neutral',
                'emotion_score': chat.get('emotion_score', 0),
                'detected_language': chat.get('detected_language', 'en'),
                'language_name': chat.get('language_name', 'English'),
            }
            chats.append(chat_data)
        
        if not chats:
            return jsonify({'error': 'No global chat data found for this period'}), 404
        
        # Export to Excel
        excel_file = export_chat_to_excel(chats, domain_name=domain_name)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"EmotiChat_Global_Report_{domain_name}_{timestamp}.xlsx"
        
        # Return file
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logging.error(f"Global chat report export error: {str(e)}")
        return jsonify({'error': f'Failed to export report: {str(e)}'}), 500


@app.route("/api/export-live-scan-report", methods=['POST'])
def export_live_scan_report():
    """Export live camera scan data to Excel with optional captured frame images."""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        import base64
        import tempfile
        import shutil
        from io import BytesIO
        import xlsxwriter

        data = request.json or {}
        scans = data.get('scans', [])

        if not scans:
            return jsonify({'error': 'No scan data provided'}), 400

        # Create temp dir for frame images
        tmp_dir = tempfile.mkdtemp(prefix='emoti_frames_')

        try:
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output, {'remove_timezone': True})

            # ── formats ──
            title_fmt = workbook.add_format({
                'bold': True, 'font_size': 16,
                'bg_color': '#00d4ff', 'font_color': '#1a202c',
                'align': 'center', 'valign': 'vcenter',
            })
            header_fmt = workbook.add_format({
                'bold': True, 'bg_color': '#1a202c', 'font_color': '#ffffff',
                'border': 1, 'align': 'center', 'valign': 'vcenter',
            })
            info_fmt = workbook.add_format({'bold': True, 'font_size': 11, 'bg_color': '#e8e8e8'})
            data_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
            pct_fmt  = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.0%'})

            # ===== SUMMARY SHEET =====
            ws_sum = workbook.add_worksheet('Summary')
            ws_sum.set_column('A:A', 20)
            ws_sum.set_column('B:B', 15)
            ws_sum.set_column('C:C', 15)
            ws_sum.merge_range('A1:C1', 'emoti — Live Scan Summary', title_fmt)
            ws_sum.set_row(0, 30)
            ws_sum.write('A3', 'Report Generated:', info_fmt)
            ws_sum.write('B3', datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'))
            ws_sum.write('A4', 'Total Scans:', info_fmt)
            ws_sum.write('B4', len(scans))

            # emotion counts
            emotion_counts = {}
            for s in scans:
                e = s.get('emotion', 'neutral')
                emotion_counts[e] = emotion_counts.get(e, 0) + 1

            ws_sum.write('A6', 'Emotion', header_fmt)
            ws_sum.write('B6', 'Count', header_fmt)
            ws_sum.write('C6', 'Percentage', header_fmt)
            row = 7
            for emo, cnt in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
                pct = cnt / len(scans) if scans else 0
                ws_sum.write(row, 0, emo, data_fmt)
                ws_sum.write(row, 1, cnt, data_fmt)
                ws_sum.write(row, 2, pct, pct_fmt)
                row += 1

            # ===== TIMELINE SHEET =====
            ws_tl = workbook.add_worksheet('Scan Timeline')
            ws_tl.set_column('A:A', 22)   # Timestamp
            ws_tl.set_column('B:B', 16)   # Emotion
            ws_tl.set_column('C:C', 14)   # Confidence
            ws_tl.set_column('D:D', 30)   # Frame
            ws_tl.merge_range('A1:D1', 'emoti — Live Scan Timeline', title_fmt)
            ws_tl.set_row(0, 30)
            ws_tl.write('A2', 'Timestamp', header_fmt)
            ws_tl.write('B2', 'Emotion', header_fmt)
            ws_tl.write('C2', 'Confidence', header_fmt)
            ws_tl.write('D2', 'Captured Frame', header_fmt)

            row = 2
            for idx, scan in enumerate(scans):
                ws_tl.set_row(row, 80)   # row height for embedded image
                ws_tl.write(row, 0, scan.get('timestamp', ''), data_fmt)
                ws_tl.write(row, 1, scan.get('emotion', 'neutral'), data_fmt)
                conf = scan.get('confidence', 0)
                ws_tl.write(row, 2, f"{round(conf * 100, 1)}%", data_fmt)

                # Embed frame image if available
                frame_b64 = scan.get('frame')
                if frame_b64:
                    try:
                        # Strip data-url prefix if present
                        if ',' in frame_b64:
                            frame_b64 = frame_b64.split(',', 1)[1]
                        img_bytes = base64.b64decode(frame_b64)
                        img_path = os.path.join(tmp_dir, f'frame_{idx}.jpg')
                        with open(img_path, 'wb') as f:
                            f.write(img_bytes)
                        ws_tl.insert_image(row, 3, img_path, {
                            'x_scale': 0.25, 'y_scale': 0.25,
                            'x_offset': 4, 'y_offset': 4,
                        })
                    except Exception as img_err:
                        logging.warning(f"Frame embed error: {img_err}")
                        ws_tl.write(row, 3, '(frame unavailable)', data_fmt)
                else:
                    ws_tl.write(row, 3, '', data_fmt)
                row += 1

            workbook.close()
            output.seek(0)

            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"emoti_LiveScan_Report_{ts}.xlsx"

            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename,
            )
        finally:
            # Clean up temp frames dir
            shutil.rmtree(tmp_dir, ignore_errors=True)

    except Exception as e:
        logging.error(f"Live scan report export error: {e}")
        return jsonify({'error': f'Failed to export report: {str(e)}'}), 500


if __name__ == "__main__":
    app.run(debug=True)
