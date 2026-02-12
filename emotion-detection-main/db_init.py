#!/usr/bin/env python3
"""
Database initialization and utility script for session management system.
Provides functions for database setup, cleanup, and testing.
"""

import os
import sys
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Session, Chat, GlobalChat


def init_database():
    """Initialize database with tables"""
    print("Initializing database...")
    with app.app_context():
        db.create_all()
        print("✓ Database tables created successfully!")


def create_sample_users():
    """Create sample users for testing"""
    print("\nCreating sample users...")
    
    bcrypt = Bcrypt(app)
    
    with app.app_context():
        # Check if users already exist
        if User.query.first():
            print("✓ Sample users already exist!")
            return
        
        sample_users = [
            {
                'name': 'John Doe',
                'phone': 9876543210,
                'email': 'john@example.com',
                'password': 'password123'
            },
            {
                'name': 'Jane Smith',
                'phone': 9876543211,
                'email': 'jane@example.com',
                'password': 'password123'
            },
            {
                'name': 'Bob Johnson',
                'phone': 9876543212,
                'email': 'bob@example.com',
                'password': 'password123'
            }
        ]
        
        for user_data in sample_users:
            hashed_password = bcrypt.generate_password_hash(
                user_data['password']
            ).decode('utf-8')
            
            user = User(
                name=user_data['name'],
                phone=user_data['phone'],
                email=user_data['email'],
                password=hashed_password,
                is_active=True
            )
            db.session.add(user)
        
        db.session.commit()
        print(f"✓ Created {len(sample_users)} sample users!")
        
        # Print user credentials
        print("\nSample User Credentials:")
        print("-" * 50)
        for user_data in sample_users:
            print(f"Email: {user_data['email']}")
            print(f"Password: {user_data['password']}")
            print("-" * 50)


def create_sample_sessions():
    """Create sample sessions for testing"""
    print("\nCreating sample sessions...")
    
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("! No users found. Run create_sample_users() first!")
            return
        
        # Clear existing sessions
        Session.query.delete()
        db.session.commit()
        
        for user in users:
            # Create one active session and one expired session per user
            import uuid
            
            # Active session
            active_session = Session(
                user_id=user.id,
                session_token=str(uuid.uuid4()),
                ip_address='192.168.1.100',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                login_time=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                is_active=True,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            # Expired session
            expired_session = Session(
                user_id=user.id,
                session_token=str(uuid.uuid4()),
                ip_address='192.168.1.101',
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
                login_time=datetime.utcnow() - timedelta(days=2),
                last_activity=datetime.utcnow() - timedelta(days=2),
                logout_time=datetime.utcnow() - timedelta(days=2),
                is_active=False,
                expires_at=datetime.utcnow() - timedelta(hours=1)
            )
            
            db.session.add(active_session)
            db.session.add(expired_session)
        
        db.session.commit()
        print(f"✓ Created sample sessions for {len(users)} users!")


def create_sample_chats():
    """Create sample chat messages for testing"""
    print("\nCreating sample chat messages...")
    
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("! No users found. Run create_sample_users() first!")
            return
        
        # Clear existing chats
        Chat.query.delete()
        db.session.commit()
        
        sample_messages = [
            {
                'user_message': 'I feel happy today!',
                'ai_response': 'That\'s wonderful! Happiness is a great emotion to embrace.',
                'detected_emotion': 'happiness',
                'emotion_score': 0.95
            },
            {
                'user_message': 'I\'m feeling stressed.',
                'ai_response': 'I understand. Try taking deep breaths and taking a break.',
                'detected_emotion': 'sadness',
                'emotion_score': 0.87
            },
            {
                'user_message': 'This is amazing!',
                'ai_response': 'It\'s great that you\'re excited! Energy and enthusiasm are powerful.',
                'detected_emotion': 'surprise',
                'emotion_score': 0.92
            }
        ]
        
        chat_count = 0
        for user in users:
            for msg in sample_messages:
                chat = Chat(
                    user_id=user.id,
                    user_message=msg['user_message'],
                    ai_response=msg['ai_response'],
                    detected_emotion=msg['detected_emotion'],
                    emotion_score=msg['emotion_score'],
                    timestamp=datetime.utcnow()
                )
                db.session.add(chat)
                chat_count += 1
        
        db.session.commit()
        print(f"✓ Created {chat_count} sample chat messages!")


def cleanup_expired_sessions():
    """Remove expired sessions from database"""
    print("\nCleaning up expired sessions...")
    
    with app.app_context():
        expired_count = Session.query.filter(
            Session.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
        print(f"✓ Removed {expired_count} expired sessions!")


def list_all_users():
    """List all users in database"""
    print("\nUsers in Database:")
    print("=" * 80)
    
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("No users found!")
            return
        
        for user in users:
            print(f"\nUser ID: {user.id}")
            print(f"  Name: {user.name}")
            print(f"  Email: {user.email}")
            print(f"  Phone: {user.phone}")
            print(f"  Created: {user.created_at}")
            print(f"  Last Login: {user.last_login}")
            print(f"  Active: {user.is_active}")
            print(f"  Active Sessions: {len([s for s in user.sessions if s.is_active])}")


def list_all_sessions():
    """List all sessions in database"""
    print("\nSessions in Database:")
    print("=" * 80)
    
    with app.app_context():
        sessions = Session.query.all()
        
        if not sessions:
            print("No sessions found!")
            return
        
        for session in sessions:
            user = User.query.get(session.user_id)
            print(f"\nSession ID: {session.id}")
            print(f"  User: {user.name} ({user.email})")
            print(f"  Token: {session.session_token[:20]}...")
            print(f"  IP Address: {session.ip_address}")
            print(f"  Login Time: {session.login_time}")
            print(f"  Last Activity: {session.last_activity}")
            print(f"  Expires At: {session.expires_at}")
            print(f"  Active: {session.is_active}")
            print(f"  Expired: {session.is_expired()}")


def reset_database():
    """Drop all tables and recreate (WARNING: Data loss!)"""
    print("\n⚠️  WARNING: This will delete ALL data!")
    confirm = input("Are you sure? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Cancelled!")
        return
    
    print("\nResetting database...")
    
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✓ Database reset complete!")


def database_stats():
    """Print database statistics"""
    print("\nDatabase Statistics:")
    print("=" * 80)
    
    with app.app_context():
        user_count = User.query.count()
        session_count = Session.query.count()
        active_sessions = Session.query.filter_by(is_active=True).count()
        chat_count = Chat.query.count()
        global_chat_count = GlobalChat.query.count()
        
        print(f"Total Users: {user_count}")
        print(f"Total Sessions: {session_count}")
        print(f"Active Sessions: {active_sessions}")
        print(f"Chat Messages: {chat_count}")
        print(f"Global Chat Messages: {global_chat_count}")
        print("=" * 80)


def main():
    """Main menu"""
    print("\n" + "=" * 80)
    print("EMOTION DETECTION APP - DATABASE UTILITY")
    print("=" * 80)
    print("\nOptions:")
    print("1. Initialize Database")
    print("2. Create Sample Users")
    print("3. Create Sample Sessions")
    print("4. Create Sample Chat Messages")
    print("5. List All Users")
    print("6. List All Sessions")
    print("7. Database Statistics")
    print("8. Cleanup Expired Sessions")
    print("9. Reset Database (WARNING!)")
    print("0. Exit")
    
    choice = input("\nEnter your choice (0-9): ").strip()
    
    if choice == '1':
        init_database()
    elif choice == '2':
        create_sample_users()
    elif choice == '3':
        create_sample_sessions()
    elif choice == '4':
        create_sample_chats()
    elif choice == '5':
        list_all_users()
    elif choice == '6':
        list_all_sessions()
    elif choice == '7':
        database_stats()
    elif choice == '8':
        cleanup_expired_sessions()
    elif choice == '9':
        reset_database()
    elif choice == '0':
        print("Goodbye!")
        return
    else:
        print("Invalid choice!")
    
    # Ask to continue
    again = input("\nPerform another operation? (yes/no): ").strip().lower()
    if again == 'yes':
        main()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
