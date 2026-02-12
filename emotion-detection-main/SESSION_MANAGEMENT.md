# Session Management Documentation

## Overview
This document describes the session management and database authentication system implemented for the emotion detection application.

## Database Schema

### 1. Users Table (`user`)
Stores user account information with automatic timestamps and login tracking.

**Columns:**
- `id` (PRIMARY KEY): Auto-incrementing unique identifier
- `name`: User's display name (max 50 chars)
- `phone`: Unique phone number for account recovery
- `email`: Unique email address for authentication
- `password`: Bcrypt hashed password
- `created_at`: Account creation timestamp (auto-set)
- `last_login`: Timestamp of most recent login (updated on each login)
- `is_active`: Boolean flag for account status (enabled/disabled)

**Constraints:**
- Email and phone must be unique
- All fields except `last_login` are required

### 2. Sessions Table (`session`)
Tracks user login sessions with security information and expiration.

**Columns:**
- `id` (PRIMARY KEY): Auto-incrementing unique identifier
- `user_id` (FOREIGN KEY): References user.id with CASCADE delete
- `session_token`: Unique UUID token for session identification
- `ip_address`: IP address from which user logged in (security tracking)
- `user_agent`: Browser/client information for device tracking
- `login_time`: When the session was created (auto-set)
- `last_activity`: Last action timestamp (updated on each request)
- `logout_time`: When user explicitly logged out
- `is_active`: Boolean flag indicating if session is currently active
- `expires_at`: Automatic session expiration timestamp

**Key Features:**
- Sessions expire after 24 hours by default
- Each session is tied to a specific IP address and device
- Session tokens are unique and cryptographically secure UUIDs
- Activity tracking helps detect abandoned sessions
- Support for concurrent sessions across multiple devices

### 3. Chat Table (`chat`)
Stores user chat messages with emotion detection results.

**Columns:**
- `id` (PRIMARY KEY): Auto-incrementing identifier
- `user_id` (FOREIGN KEY): References user.id with CASCADE delete
- `user_message`: The user's input text
- `ai_response`: The AI's response to the user
- `detected_emotion`: Emotion detected from user's message
- `emotion_score`: Confidence score for emotion detection
- `timestamp`: Message creation time (auto-set)

### 4. GlobalChat Table (`globalchat`)
Stores public chat messages with face emotion detection support.

**Columns:**
- `id` (PRIMARY KEY): Auto-incrementing identifier
- `user_id` (FOREIGN KEY): References user.id with CASCADE delete
- `username`: Display name for public chat
- `user_message`: Public message content
- `ai_response`: AI response for public messages
- `detected_text_emotion`: Emotion from text analysis
- `detected_face_emotion`: Emotion from face recognition
- `face_emotion_confidence`: Confidence score for face emotion
- `emotion_score`: Overall emotion confidence
- `is_ai_response`: Flag indicating if message is from AI
- `timestamp`: Message creation time (auto-set)

## Session Management Features

### 1. Login Flow
```
1. User submits login credentials
2. System verifies email and password
3. New session record is created with:
   - Unique session token (UUID)
   - User's IP address
   - Browser user agent
   - Expiration time (24 hours from now)
4. Session token stored in Flask session cookie
5. User's last_login timestamp updated
6. User is redirected to dashboard/userpage
```

### 2. Session Validation
The `@app.before_request` decorator intercepts every request to:
- Verify session token exists in database
- Check if session has expired
- Update last_activity timestamp
- Invalidate expired or missing sessions
- Redirect to login if session is invalid

### 3. Logout Flow
```
1. User clicks logout button/link
2. System finds session record by session token
3. Session is marked as inactive (is_active = 0)
4. Logout timestamp is recorded
5. Flask session cookie is cleared
6. User is redirected to login page
7. Session data is preserved for audit logs
```

### 4. Session Expiration
- Default timeout: 24 hours from login
- Sessions are checked on every request
- Expired sessions are automatically invalidated
- User is prompted to log in again
- Logout time is recorded for sessions that expire

## API Endpoints

### POST /signup
**Description:** Register a new user account
**Parameters:**
- `name`: User's full name
- `phone`: Unique phone number
- `email`: Unique email address
- `password`: Password (hashed before storage)
- `Cpassword`: Password confirmation

**Response:**
- Success (302): Redirect to login page
- Error (302): Redirect to signup page with flash message

### POST /login
**Description:** Authenticate user and create session
**Parameters:**
- `email`: User's email address
- `password`: User's password

**Response:**
- Success (302): Redirect to userpage with session created
- Error (302): Redirect to login page with error message

### GET /logout
**Description:** End current session and logout user
**Parameters:** None

**Response:**
- Success (302): Redirect to login page
- Side Effects: 
  - Session marked as inactive in database
  - Flask session cookie cleared
  - Logout timestamp recorded

### GET /userpage
**Description:** User dashboard (protected route)
**Parameters:** None
**Requires:** Active session

**Response:**
- Success (200): Render userpage.html with user data
- Unauthorized (302): Redirect to login page if no session

### GET /session_status
**Description:** Get current session information
**Parameters:** None
**Requires:** Active session

**Response:**
```json
{
    "authenticated": true,
    "user_id": 1,
    "session_info": {
        "id": 1,
        "user_id": 1,
        "session_token": "uuid-string",
        "ip_address": "192.168.1.1",
        "login_time": "2026-02-11T10:30:00",
        "last_activity": "2026-02-11T10:35:00",
        "expires_at": "2026-02-12T10:30:00",
        "is_active": true,
        "is_expired": false
    }
}
```

### GET /active_sessions
**Description:** Get all active sessions for current user
**Parameters:** None
**Requires:** Active session

**Response:**
```json
{
    "total_active_sessions": 2,
    "sessions": [
        {...session_info...},
        {...session_info...}
    ]
}
```

## Configuration

### Environment Variables (.env)
```
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here
DATABASE_URL=sqlite:///users.db
```

### Flask Configuration (app.py)
```python
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
SESSION_TIMEOUT = 24 * 60 * 60  # 24 hours
```

## Security Features

### 1. Password Security
- Passwords are hashed using bcrypt
- Stored as bcrypt hash (not plaintext)
- Hash verification on login

### 2. Session Security
- Unique session tokens (UUIDs)
- Session cookies are HTTP-only (JS cannot access)
- Session cookies marked as Secure (HTTPS only in production)
- SameSite = 'Lax' (CSRF protection)

### 3. Multi-Device Support
- Users can be logged in on multiple devices simultaneously
- Each session has unique IP address tracking
- Each session has device user agent information

### 4. Audit Trail
- All sessions recorded with login timestamp
- Logout timestamps recorded
- IP addresses logged for security monitoring
- Last activity timestamps for session tracking

## Database Maintenance

### Cleanup Expired Sessions
```python
# In a scheduled task or maintenance script
def cleanup_expired_sessions():
    expired = Session.query.filter(
        Session.expires_at < datetime.utcnow()
    ).delete()
    db.session.commit()
    return expired
```

### Force Logout All Sessions for User
```python
def logout_all_user_sessions(user_id):
    sessions = Session.query.filter_by(user_id=user_id, is_active=True).all()
    for s in sessions:
        s.is_active = False
        s.logout_time = datetime.utcnow()
    db.session.commit()
```

### Get User Login History
```python
def get_login_history(user_id, limit=10):
    return Session.query.filter_by(user_id=user_id).order_by(
        Session.login_time.desc()
    ).limit(limit).all()
```

## Migration Instructions

### For New Projects
1. Ensure `requirements.txt` includes required packages:
   - Flask
   - Flask-SQLAlchemy
   - Flask-Bcrypt
   - SQLAlchemy

2. Run database initialization:
   ```python
   from app import app, db
   with app.app_context():
       db.create_all()
   ```

3. Models will be created automatically from `models.py`

### For Existing Projects
If you're upgrading from a version without session management:

1. Back up your existing database file (`users.db`)

2. Update `models.py` with new User fields:
   - `created_at`
   - `last_login`
   - `is_active`
   - `sessions` relationship

3. Create migration:
   ```bash
   flask db migrate -m "Add session management"
   flask db upgrade
   ```

4. Or manually add columns (SQLite):
   ```sql
   ALTER TABLE user ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
   ALTER TABLE user ADD COLUMN last_login DATETIME;
   ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT 1;
   ```

5. Create the Session table (see DATABASE_SCHEMA.sql)

## Testing

### Test Login
```bash
curl -X POST http://localhost:5000/login \
  -d "email=test@example.com&password=password123"
```

### Test Session Status
```bash
curl http://localhost:5000/session_status
```

### Test Active Sessions
```bash
curl http://localhost:5000/active_sessions
```

### Test Logout
```bash
curl http://localhost:5000/logout
```

## Troubleshooting

### Issue: "Session has expired"
- **Cause:** Session timeout reached (24 hours default)
- **Solution:** User needs to log in again

### Issue: "Invalid session"
- **Cause:** Session token not found in database or corrupted
- **Solution:** Clear cookies and log in again

### Issue: Multiple sessions showing for same user
- **Expected Behavior:** Users can be logged in on multiple devices
- **To Restrict:** Implement logic to invalidate other sessions on login

### Issue: Database locked
- **Cause:** Multiple concurrent writes or active connections
- **Solution:** Check for long-running processes; consider using PostgreSQL for production

## Future Enhancements

1. **Refresh Tokens:** Implement token refresh without re-login
2. **Device Management:** UI to manage active sessions and devices
3. **Password Reset:** Secure password reset via email
4. **Two-Factor Authentication:** Add 2FA for enhanced security
5. **Session Analytics:** Dashboard showing login patterns and device usage
6. **IP Whitelisting:** Optional IP address restrictions per user
7. **Activity Logs:** Detailed action logging beyond session tracking
8. **Geolocation:** Track and alert on unusual login locations

## Production Deployment Notes

1. **Use PostgreSQL** instead of SQLite for production
2. **Enable HTTPS** to secure session cookies
3. **Set strong SECRET_KEY** in environment
4. **Use connection pooling** for database efficiency
5. **Implement rate limiting** on login endpoint
6. **Monitor failed login attempts** for security
7. **Schedule cleanup** of expired sessions
8. **Enable CORS** only for trusted domains
9. **Use environment-specific** database URLs
10. **Implement CSRF protection** for all forms
