from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, session
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'instance', 'users.db')

# Ensure instance directory exists
os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)

# Initialize database
def init_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

# Call init_db on startup
init_db()

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Helper functions
def create_user(name, phone, email, password):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO users (name, phone, email, password) VALUES (?, ?, ?, ?)',
                  (name, phone, email, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return None
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return None

def find_user_by_email(email):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()
        return dict(user) if user else None
    except Exception as e:
        logging.error(f"Error finding user: {e}")
        return None

def find_user_by_phone(phone):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE phone = ?', (phone,))
        user = c.fetchone()
        conn.close()
        return dict(user) if user else None
    except Exception as e:
        logging.error(f"Error finding user by phone: {e}")
        return None

# Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login_page")
def login_page():
    return render_template("login.html")

@app.route("/signup_page")
def signup_page():
    return render_template("signup.html")

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            name = request.form['name']
            phone = request.form['phone']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form.get('Cpassword')

            # Check if passwords match
            if password != confirm_password:
                flash("Passwords do not match!", "danger")
                return redirect(url_for('signup_page'))

            # Check if user already exists
            existing_user = find_user_by_email(email)
            if existing_user:
                flash("Email already registered!", "warning")
                return redirect(url_for('signup_page'))

            existing_phone = find_user_by_phone(phone)
            if existing_phone:
                flash("Phone number is already in use! Use another number.", "warning")
                return redirect(url_for('signup_page'))

            # Store user (password stored as plain text for simplicity - in production, use hashing!)
            result = create_user(name=name, phone=phone, email=email, password=password)
            
            if result is None:
                flash("Database error. Please try again.", "danger")
                return redirect(url_for('signup_page'))
                
            flash("Signup successful! You can now log in.", "success")
            return redirect(url_for('login_page'))
        except KeyError as e:
            flash(f"Missing required field: {str(e)}", "danger")
            return redirect(url_for('signup_page'))
        except Exception as e:
            logging.error(f"Signup error: {e}")
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('signup_page'))

    return render_template('signup.html')

@app.route("/login", methods=['POST'])
def login():
    try:
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Missing email or password!", "warning")
            return redirect(url_for("login_page"))

        user = find_user_by_email(email)
        if user is None:
            flash("No account found with this email. Please sign up!", "warning")
            return redirect(url_for("login_page"))

        if user['password'] != password:
            flash("Incorrect password. Please try again!", "danger")
            return redirect(url_for("login_page"))

        # Store session info
        session["user_id"] = str(user['id'])
        session["user_name"] = user['name']
        session.permanent = True
        app.permanent_session_lifetime = timedelta(hours=24)

        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("userpage"))
    except Exception as e:
        logging.error(f"Login error: {e}")
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("login_page"))

@app.route("/userpage")
def userpage():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("userpage.html", user={'name': session.get('user_name', 'User')})

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully!", "info")
    return redirect(url_for("login_page"))

@app.route("/text_detection")
def text_detection():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("text_detection.html")

@app.route("/image_detection")
def image_detection():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("image_detection.html")

@app.route("/video_detection")
def video_detection():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("video_detection.html")

@app.route("/multi_language")
def multi_language():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("multi_language.html")

@app.route("/analytics")
def analytics():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("analytics.html", user={'name': session.get('user_name', 'User')})

@app.route("/chat")
def chat():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("chat.html", user={'name': session.get('user_name', 'User')})

@app.route("/live-chat")
def live_chat():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("live_chat.html", user={'name': session.get('user_name', 'User')})

@app.route("/settings")
def settings():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("settings.html", user={'name': session.get('user_name', 'User')})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
