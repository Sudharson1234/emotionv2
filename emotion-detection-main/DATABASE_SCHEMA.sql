-- ============================================================================
-- EMOTION DETECTION APPLICATION - DATABASE SCHEMA
-- ============================================================================
-- This SQL schema defines the complete database structure for the emotion 
-- detection application with user authentication and session management.
--
-- Created: 2026-02-11
-- Database: SQLite (users.db)
-- ============================================================================

-- ============================================================================
-- USER TABLE - Stores user account information
-- ============================================================================
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL,
    phone INTEGER UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    is_active BOOLEAN DEFAULT 1,
    CONSTRAINT user_email_unique UNIQUE(email),
    CONSTRAINT user_phone_unique UNIQUE(phone)
);

-- Create indexes for faster queries
CREATE INDEX idx_user_email ON user(email);
CREATE INDEX idx_user_phone ON user(phone);
CREATE INDEX idx_user_is_active ON user(is_active);

-- ============================================================================
-- SESSION TABLE - Tracks user login sessions with expiration
-- ============================================================================
CREATE TABLE session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token VARCHAR(100) UNIQUE NOT NULL,
    ip_address VARCHAR(50),
    user_agent VARCHAR(255),
    login_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    logout_time DATETIME,
    is_active BOOLEAN DEFAULT 1,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    CONSTRAINT session_token_unique UNIQUE(session_token)
);

-- Create indexes for faster session queries
CREATE INDEX idx_session_user_id ON session(user_id);
CREATE INDEX idx_session_token ON session(session_token);
CREATE INDEX idx_session_is_active ON session(is_active);
CREATE INDEX idx_session_expires_at ON session(expires_at);
CREATE INDEX idx_session_login_time ON session(login_time);

-- ============================================================================
-- CHAT TABLE - Stores one-on-one user chat messages
-- ============================================================================
CREATE TABLE chat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    detected_emotion VARCHAR(50),
    emotion_score FLOAT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_chat_user_id ON chat(user_id);
CREATE INDEX idx_chat_timestamp ON chat(timestamp);

-- ============================================================================
-- GLOBALCHAT TABLE - Stores public/group chat messages with face emotion
-- ============================================================================
CREATE TABLE globalchat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username VARCHAR(50) NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT,
    detected_text_emotion VARCHAR(50),
    detected_face_emotion VARCHAR(50),
    face_emotion_confidence FLOAT,
    emotion_score FLOAT,
    is_ai_response BOOLEAN DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_globalchat_user_id ON globalchat(user_id);
CREATE INDEX idx_globalchat_timestamp ON globalchat(timestamp);
CREATE INDEX idx_globalchat_is_ai_response ON globalchat(is_ai_response);

-- ============================================================================
-- USEFUL QUERIES FOR SESSION MANAGEMENT
-- ============================================================================

-- Query 1: Get all active sessions for a specific user
-- SELECT * FROM session WHERE user_id = ? AND is_active = 1;

-- Query 2: Get expired sessions that need cleanup
-- SELECT * FROM session WHERE expires_at < CURRENT_TIMESTAMP AND is_active = 1;

-- Query 3: Mark all sessions for a user as inactive (logout all devices)
-- UPDATE session SET is_active = 0, logout_time = CURRENT_TIMESTAMP 
-- WHERE user_id = ? AND is_active = 1;

-- Query 4: Get user login history
-- SELECT * FROM session WHERE user_id = ? ORDER BY login_time DESC;

-- Query 5: Get currently logged-in users
-- SELECT DISTINCT user.id, user.name, user.email, session.login_time, session.ip_address
-- FROM user
-- INNER JOIN session ON user.id = session.user_id
-- WHERE session.is_active = 1 AND session.expires_at > CURRENT_TIMESTAMP;

-- Query 6: Delete expired sessions (cleanup)
-- DELETE FROM session WHERE expires_at < CURRENT_TIMESTAMP;

-- Query 7: Get user chat statistics
-- SELECT DATE(timestamp) as date, COUNT(*) as message_count, COUNT(DISTINCT user_id) as active_users
-- FROM chat
-- GROUP BY DATE(timestamp)
-- ORDER BY date DESC;

-- ============================================================================
-- DATA MIGRATION GUIDE
-- ============================================================================
-- 
-- If you have existing user data without the session table:
-- 
-- 1. Add new columns to user table:
--    ALTER TABLE user ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
--    ALTER TABLE user ADD COLUMN last_login DATETIME;
--    ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT 1;
--
-- 2. Create the session table (see SESSION TABLE section above)
--
-- 3. The application will automatically handle session creation on login
--
-- ============================================================================
