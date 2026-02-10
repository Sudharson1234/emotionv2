from flask import Flask, request, jsonify,Response,json, render_template,flash,redirect,url_for,session,send_from_directory
import tensorflow as tf
import logging
import os
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_migrate import Migrate
from flask_cors import CORS
from detections.detection import detect_text_emotion
from models import db, User  # Import db & User from models.py
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

@app.route("/video_detection")
def video_detection():
    return render_template("video_detection.html")

@app.route("/multi_language")
def multi_language():
    return render_template("multi_language.html")

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
    if "file" in request.files:
        file = request.files["file"]
        response= process_image(file)
        return jsonify(response)
    elif request.is_json and "image_base64" in request.json:
        response = process_image()
        return jsonify(response)
    return jsonify({"error":"No valid image provided"}),400

@app.route("/video_upload", methods=["POST"])
def video_upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    result = process_video(file)
    return result

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
            'emotion_analysis': emotion_response['Emotion Analysis'],
            'analysis_report': emotion_response.get('analysis_report'),
            'key_indicators': emotion_response.get('key_indicators'),
            'emotional_intensity': emotion_response.get('emotional_intensity'),
            'model_used': emotion_response.get('model_used')
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
