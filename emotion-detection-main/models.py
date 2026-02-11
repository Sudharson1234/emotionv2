from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()  # No app binding here!

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone=db.Column(db.Integer,unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    chats = db.relationship('Chat', backref='user', lazy=True)
    global_chats = db.relationship('GlobalChat', backref='user', lazy=True)


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    detected_emotion = db.Column(db.String(50), nullable=True)
    emotion_score = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'detected_emotion': self.detected_emotion,
            'emotion_score': self.emotion_score,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class GlobalChat(db.Model):
    """Model for global/public chat messages with face emotion integration"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=True)
    detected_text_emotion = db.Column(db.String(50), nullable=True)
    detected_face_emotion = db.Column(db.String(50), nullable=True)
    face_emotion_confidence = db.Column(db.Float, nullable=True)
    emotion_score = db.Column(db.Float, nullable=True)
    is_ai_response = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'detected_text_emotion': self.detected_text_emotion,
            'detected_face_emotion': self.detected_face_emotion,
            'face_emotion_confidence': self.face_emotion_confidence,
            'emotion_score': self.emotion_score,
            'is_ai_response': self.is_ai_response,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
