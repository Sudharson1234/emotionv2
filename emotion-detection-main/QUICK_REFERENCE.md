# Session Management - Quick Reference Card

## Installation & Setup (5 minutes)

```bash
# 1. Verify all packages are installed
pip install -r requirements.txt

# 2. Initialize database
python db_init.py
# Select option 1: Initialize Database

# 3. (Optional) Create sample users
python db_init.py
# Select option 2: Create Sample Users

# 4. Start application
python app.py

# 5. Visit login page
# http://localhost:5000/login_page
```

## Database Tables Quick Reference

### User Table (Enhanced)
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    phone INTEGER UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,  -- Bcrypt hash
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    is_active BOOLEAN DEFAULT 1
);
```

### Session Table (New)
```sql
CREATE TABLE session (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_token VARCHAR(100) UNIQUE NOT NULL,
    ip_address VARCHAR(50),
    user_agent VARCHAR(255),
    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    logout_time DATETIME,
    is_active BOOLEAN DEFAULT 1,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);
```

## API Endpoints

### Authentication
| URL | Method | Body | Auth | Purpose |
|-----|--------|------|------|---------|
| /signup_page | GET | - | No | Show signup form |
| /signup | POST | name, phone, email, password, Cpassword | No | Create account |
| /login_page | GET | - | No | Show login form |
| /login | POST | email, password | No | Login & create session |
| /logout | GET | - | Yes | End session |
| /userpage | GET | - | Yes | User dashboard |

### Session Info
| URL | Method | Body | Auth | Purpose |
|-----|--------|------|------|---------|
| /session_status | GET | - | Yes | Get current session |
| /active_sessions | GET | - | Yes | List all sessions |

## Session Lifecycle

```
1. User fills signup form → POST /signup → User created
2. User fills login form → POST /login
3. Backend validates password (Bcrypt)
4. Creates Session record with:
   - UUID token
   - IP address
   - User agent
   - Expiration time (24h from now)
5. Stores token in Flask session cookie
6. Redirects to /userpage
7. Every request validated by @app.before_request
8. Activity timestamp updated
9. Expiration checked
10. User logout → GET /logout → Session marked inactive
11. Flask session cleared
12. Redirect to login
```

## Python Code Examples

### Check if User is Logged In
```python
@app.route('/protected')
def protected():
    if "user_id" not in session:
        return redirect(url_for('login_page'))
    user = User.query.get(session["user_id"])
    return f"Hello {user.name}"
```

### Get Current Session Info
```python
def get_current_session():
    if "session_token" not in session:
        return None
    return Session.query.filter_by(
        session_token=session["session_token"]
    ).first()
```

### Check if Session Expired
```python
current_session = get_current_session()
if current_session and current_session.is_expired():
    print("Session expired!")
```

### Logout Specific User
```python
def logout_user(user_id):
    sessions = Session.query.filter_by(
        user_id=user_id,
        is_active=True
    ).all()
    for s in sessions:
        s.is_active = False
        s.logout_time = datetime.utcnow()
    db.session.commit()
```

### Get Login History
```python
def get_login_history(user_id, limit=10):
    return Session.query.filter_by(
        user_id=user_id
    ).order_by(
        Session.login_time.desc()
    ).limit(limit).all()
```

## JavaScript/Frontend Examples

### Check Session Status
```javascript
fetch('/session_status')
    .then(r => r.json())
    .then(data => {
        if (data.authenticated) {
            console.log('User:', data.user_id);
            console.log('Session expires:', data.session_info.expires_at);
        }
    });
```

### Logout
```javascript
document.getElementById('logout-btn').addEventListener('click', () => {
    window.location.href = '/logout';
});
```

### Refresh Session Info
```javascript
setInterval(() => {
    fetch('/session_status')
        .then(r => r.json())
        .then(data => {
            if (!data.authenticated) {
                // Session expired, redirect
                window.location.href = '/login_page';
            }
        });
}, 60000); // Check every minute
```

## Database Queries

### Find Active Sessions
```sql
SELECT * FROM session WHERE is_active = 1 AND expires_at > CURRENT_TIMESTAMP;
```

### Find User's Sessions
```sql
SELECT * FROM session WHERE user_id = ? ORDER BY login_time DESC;
```

### Remove Expired Sessions
```sql
DELETE FROM session WHERE expires_at < CURRENT_TIMESTAMP;
```

### User Login Statistics
```sql
SELECT user.name, COUNT(*) as login_count, MAX(session.login_time) as last_login
FROM user
LEFT JOIN session ON user.id = session.user_id
GROUP BY user.id
ORDER BY login_count DESC;
```

### Currently Logged In Users
```sql
SELECT DISTINCT user.name, session.login_time, session.ip_address
FROM user
INNER JOIN session ON user.id = session.user_id
WHERE session.is_active = 1 AND session.expires_at > CURRENT_TIMESTAMP;
```

## Configuration

### Session Timeout
Default: 24 hours

**Change to 12 hours in app.py:**
```python
SESSION_TIMEOUT = 12 * 60 * 60
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)
```

### Database URL
**SQLite (Development):**
```
DATABASE_URL=sqlite:///users.db
```

**PostgreSQL (Production):**
```
DATABASE_URL=postgresql://user:password@localhost/emotion_db
```

## Testing Checklist

- [ ] Can create account
- [ ] Can login
- [ ] Session is created in DB
- [ ] Can view session status
- [ ] Can see active sessions
- [ ] Can logout
- [ ] Session marked inactive after logout
- [ ] Protected routes redirect if not logged in
- [ ] Session expires after timeout
- [ ] IP address recorded
- [ ] Device info recorded

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "No active session" | Session cookie missing | Clear cookies, login again |
| "Invalid session" | Token not in database | Verify DB connection |
| Session expires immediately | SESSION_TIMEOUT too low | Check value is in seconds |
| Multiple sessions shown | Expected behavior | Each device = separate session |
| Can't logout | DB commit failed | Check database permissions |
| Password doesn't match | Bcrypt hash mismatch | Ensure correct password |
| "Session has expired" | 24h timeout | User needs to login again |

## Files Modified

```
✅ models.py
   - Added Session model
   - Enhanced User model

✅ app.py
   - Added uuid import
   - Added session config
   - Enhanced login route
   - Added logout route
   - Added session validation middleware
   - Added session_status endpoint
   - Added active_sessions endpoint
```

## Files Created

```
📄 DATABASE_SCHEMA.sql - SQL reference
📄 SESSION_MANAGEMENT.md - Full documentation
📄 IMPLEMENTATION_GUIDE.md - Setup guide
📄 SYSTEM_SUMMARY.md - Complete overview
📄 db_init.py - Database utility
📄 QUICK_REFERENCE.md - This file
📄 migrations/versions/001_add_session_management.py - Migration
```

## Important Notes

1. **Passwords are hashed** with bcrypt - never store plaintext
2. **Session tokens are UUIDs** - unique and secure
3. **Sessions expire** after 24 hours by default
4. **Activity is tracked** - last_activity updated on each request
5. **Multi-device support** - different device = different session
6. **IP addresses logged** - for security tracking
7. **Device info stored** - user agent in each session
8. **Cascade delete** - deleting user deletes all sessions

## Environment Variables (.env)

```
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here
DATABASE_URL=sqlite:///users.db
```

## Production Checklist

- [ ] Use PostgreSQL instead of SQLite
- [ ] Set strong SECRET_KEY
- [ ] Enable HTTPS
- [ ] Set SESSION_COOKIE_SECURE = True (done)
- [ ] Set SESSION_COOKIE_HTTPONLY = True (done)
- [ ] Schedule cleanup of expired sessions
- [ ] Monitor failed login attempts
- [ ] Enable CORS only for trusted domains
- [ ] Use environment-specific variables
- [ ] Implement rate limiting on login

## Getting Help

1. See `SESSION_MANAGEMENT.md` for complete documentation
2. See `IMPLEMENTATION_GUIDE.md` for setup steps
3. See `DATABASE_SCHEMA.sql` for SQL reference
4. Run `python db_init.py` for database utilities
5. Check model code in `models.py`
6. Check routes in `app.py`

---

**Version:** 1.0 | **Date:** 2026-02-11 | **Framework:** Flask 3.1.2
