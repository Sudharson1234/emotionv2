from flask_pymongo import PyMongo
from datetime import datetime, timedelta
import uuid
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
mongo = PyMongo()  # No app binding here!

# MongoDB collections will be accessed via mongo.db.collection_name
# No need for SQLAlchemy models - we'll use dictionaries for documents

def is_db_connected():
    """Check if MongoDB is connected"""
    try:
        return mongo.db is not None
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

def _handle_db_error(operation_name, error):
    """Handle and log database errors"""
    logger.error(f"Database error in {operation_name}: {str(error)}")
    raise Exception(f"Database connection failed. Please try again later. ({operation_name})")

# Helper functions for user operations
def create_user(name, phone, email, password):
    """Create a new user document"""
    try:
        if not is_db_connected():
            raise Exception("Database connection failed")
        user_doc = {
            'name': name,
            'phone': phone,
            'email': email,
            'password': password,
            'created_at': datetime.utcnow(),
            'last_login': None,
            'is_active': True
        }
        return mongo.db.users.insert_one(user_doc)
    except Exception as e:
        _handle_db_error("create_user", e)

def find_user_by_email(email):
    """Find user by email"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in find_user_by_email")
            return None
        return mongo.db.users.find_one({'email': email})
    except Exception as e:
        logger.error(f"Error finding user by email: {e}")
        return None

def find_user_by_phone(phone):
    """Find user by phone"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in find_user_by_phone")
            return None
        return mongo.db.users.find_one({'phone': phone})
    except Exception as e:
        logger.error(f"Error finding user by phone: {e}")
        return None

def find_user_by_id(user_id):
    """Find user by ID"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in find_user_by_id")
            return None
        return mongo.db.users.find_one({'_id': ObjectId(user_id)})
    except Exception as e:
        logger.error(f"Error finding user by ID: {e}")
        return None

def update_user_last_login(user_id, login_time=None):
    """Update user's last login time"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in update_user_last_login")
            return None
        if login_time is None:
            login_time = datetime.utcnow()
        return mongo.db.users.update_one(
            {'_id': user_id},
            {'$set': {'last_login': login_time}}
        )
    except Exception as e:
        logger.error(f"Error updating user last login: {e}")
        return None

# Helper functions for chat operations
def create_chat(user_id, user_message, ai_response, detected_emotion=None, emotion_score=None):
    """Create a new chat document"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in create_chat")
            return None
        chat_doc = {
            'user_id': user_id,
            'user_message': user_message,
            'ai_response': ai_response,
            'detected_emotion': detected_emotion,
            'emotion_score': emotion_score,
            'timestamp': datetime.utcnow()
        }
        return mongo.db.chats.insert_one(chat_doc)
    except Exception as e:
        logger.error(f"Error creating chat: {e}")
        return None

def get_user_chats(user_id, limit=50):
    """Get user's chat history"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in get_user_chats")
            return []
        return list(mongo.db.chats.find(
            {'user_id': user_id}
        ).sort('timestamp', -1).limit(limit))
    except Exception as e:
        logger.error(f"Error getting user chats: {e}")
        return []

# Helper functions for global chat operations
def create_global_chat(user_id, username, user_message, ai_response=None,
                      detected_text_emotion=None, detected_face_emotion=None,
                      face_emotion_confidence=None, emotion_score=None, is_ai_response=False):
    """Create a new global chat document"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in create_global_chat")
            return None
        chat_doc = {
            'user_id': user_id,
            'username': username,
            'user_message': user_message,
            'ai_response': ai_response,
            'detected_text_emotion': detected_text_emotion,
            'detected_face_emotion': detected_face_emotion,
            'face_emotion_confidence': face_emotion_confidence,
            'emotion_score': emotion_score,
            'is_ai_response': is_ai_response,
            'timestamp': datetime.utcnow()
        }
        return mongo.db.global_chats.insert_one(chat_doc)
    except Exception as e:
        logger.error(f"Error creating global chat: {e}")
        return None

def get_global_chats(limit=50):
    """Get global chat history"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in get_global_chats")
            return []
        return list(mongo.db.global_chats.find().sort('timestamp', -1).limit(limit))
    except Exception as e:
        logger.error(f"Error getting global chats: {e}")
        return []

# Helper functions for session operations
def create_session(user_id, session_token, ip_address=None, user_agent=None, expires_at=None):
    """Create a new session document"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in create_session")
            return None
        if expires_at is None:
            expires_at = datetime.utcnow() + timedelta(hours=24)

        session_doc = {
            'user_id': user_id,
            'session_token': session_token,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'login_time': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'logout_time': None,
            'is_active': True,
            'expires_at': expires_at
        }
        return mongo.db.sessions.insert_one(session_doc)
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return None

def find_session_by_token(session_token):
    """Find session by token"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in find_session_by_token")
            return None
        return mongo.db.sessions.find_one({'session_token': session_token})
    except Exception as e:
        logger.error(f"Error finding session by token: {e}")
        return None

def update_session_activity(session_id):
    """Update session last activity"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in update_session_activity")
            return None
        return mongo.db.sessions.update_one(
            {'_id': session_id},
            {'$set': {'last_activity': datetime.utcnow()}}
        )
    except Exception as e:
        logger.error(f"Error updating session activity: {e}")
        return None

def deactivate_session(session_token):
    """Deactivate a session"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in deactivate_session")
            return None
        return mongo.db.sessions.update_one(
            {'session_token': session_token},
            {'$set': {'is_active': False, 'logout_time': datetime.utcnow()}}
        )
    except Exception as e:
        logger.error(f"Error deactivating session: {e}")
        return None

def get_active_sessions(user_id):
    """Get active sessions for a user"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in get_active_sessions")
            return []
        return list(mongo.db.sessions.find({
            'user_id': user_id,
            'is_active': True
        }))
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        return []

# Helper functions for analytics
def get_chat_stats(user_id, start_date=None):
    """Get chat statistics for a user"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in get_chat_stats")
            return {}
        query = {'user_id': user_id}
        if start_date:
            query['timestamp'] = {'$gte': start_date}

        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': '$detected_emotion',
                'count': {'$sum': 1}
            }}
        ]

        results = list(mongo.db.chats.aggregate(pipeline))
        return {result['_id'] or 'unknown': result['count'] for result in results}
    except Exception as e:
        logger.error(f"Error getting chat stats: {e}")
        return {}

def get_global_chat_stats(start_date=None):
    """Get global chat statistics"""
    try:
        if not is_db_connected():
            logger.warning("Database not connected in get_global_chat_stats")
            return {'text_emotion_distribution': {}, 'face_emotion_distribution': {}}
        query = {}
        if start_date:
            query['timestamp'] = {'$gte': start_date}

        # Text emotions
        text_pipeline = [
            {'$match': {**query, 'detected_text_emotion': {'$ne': None}}},
            {'$group': {
                '_id': '$detected_text_emotion',
                'count': {'$sum': 1}
            }}
        ]

        # Face emotions
        face_pipeline = [
            {'$match': {**query, 'detected_face_emotion': {'$ne': None}}},
            {'$group': {
                '_id': '$detected_face_emotion',
                'count': {'$sum': 1}
            }}
        ]

        text_results = list(mongo.db.global_chats.aggregate(text_pipeline))
        face_results = list(mongo.db.global_chats.aggregate(face_pipeline))

        return {
            'text_emotion_distribution': {r['_id']: r['count'] for r in text_results},
            'face_emotion_distribution': {r['_id']: r['count'] for r in face_results}
        }
    except Exception as e:
        logger.error(f"Error getting global chat stats: {e}")
        return {'text_emotion_distribution': {}, 'face_emotion_distribution': {}}
