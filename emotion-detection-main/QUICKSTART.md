# 🚀 EMOTI - Emotion Detection AI Chat

## Quick Start Guide

### Option 1: Windows Batch File (Easiest)
```bash
1. Open Command Prompt (cmd)
2. Navigate to project folder
3. Double-click: run_app.bat
```

### Option 2: Python Script
```bash
1. Open Command Prompt or PowerShell
2. Navigate to project folder
3. Run: python start_app.py
```

### Option 3: Manual Setup
```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate.bat

# Install dependencies (first time only)
python setup.py

# Start the app
python app.py
```

## ✅ What's Included

- ✅ **Emotion Detection**: Text, Image, Video, Live Camera
- ✅ **Multilingual Support**: English, Spanish, French, Chinese, Arabic, etc.
- ✅ **Global Chat**: Anonymous access to global emotion chat
- ✅ **Professional AI Responses**: Empathetic responses in user's language
- ✅ **Real-time Processing**: Fast emotion detection and analysis

## 🔧 System Requirements

- Python 3.8+
- 8GB RAM (recommended)
- 10GB free disk space
- MongoDB (optional - for persistent storage)

## 📋 Environment Variables

Create a `.env` file in the project root:
```
MONGO_URI=mongodb+srv://your_username:your_password@cluster.mongodb.net/
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
```

## 🌐 Access the App

Once running, open your browser and go to:
- **http://127.0.0.1:5000**

### Available Features:
1. **Global Chat** - Chat with anonymous global users
2. **Text Emotion Detection** - Analyze emotions in written text
3. **Image Detection** - Detect emotions from faces in images
4. **Video Detection** - Analyze emotions in video files
5. **Live Camera** - Real-time emotion detection from webcam

## 🆘 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'langdetect'"
```bash
# Make sure virtual environment is activated
.venv\Scripts\activate.bat

# Reinstall dependencies
python -m pip install langdetect transformers torch flask-migrate tf-keras imageio -q
```

### Error: "Cannot connect to MongoDB"
- Global Chat and Text Detection still work without MongoDB
- For persistent storage, ensure MongoDB is running and MONGO_URI is correct

### Error: "Port 5000 is already in use"
```bash
# Kill existing Python process
taskkill /F /IM python.exe

# Wait 2 seconds
timeout /t 2

# Restart the app
python start_app.py
```

### App runs slowly on first start
- First run downloads ML models (~2GB)
- Subsequent runs will be much faster
- Models are cached locally

## 📊 Features Explained

### 🎭 Emotion Detection
- Uses advanced AI models (RoBERTa, DeepFace)
- Detects: Joy, Sadness, Anger, Fear, Surprise, Neutral, etc.
- Confidence scores for accuracy assessment

### 🌍 Multilingual Support
- Automatic language detection
- Responses in user's native language
- Supports 100+ languages

### 💬 Global Chat
- No login required - just start chatting!
- See emotions detected from other users
- Professional AI responses to every message

### 📸 Image/Video Analysis
- Upload images to detect face emotions
- Upload videos to analyze emotional expressions
- Live camera stream for real-time detection

## 🔐 Security

- Passwords are bcrypt encrypted
- JWT-based session management
- HTTPS ready for production
- Secure MongoDB connections

## 📞 Support

For issues or feature requests, check the logs in the terminal console output.

---

**Made with 💙 for emotional intelligence**
