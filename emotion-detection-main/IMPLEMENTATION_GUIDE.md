# Session Management Implementation Guide

## Quick Start

### Step 1: Verify Requirements
Ensure your `requirements.txt` contains these packages:
```
Flask==3.1.2
Flask-SQLAlchemy==3.1.1
Flask-Bcrypt==1.0.1
SQLAlchemy>=2.0.0
alembic==1.18.4
Flask-Migrate==4.1.0
```

### Step 2: Initialize Database
```bash
# Create fresh database with all tables
python
>>> from app import app, db
>>> with app.app_context():
>>>     db.create_all()
>>> exit()
```

Or using Flask-Migrate:
```bash
# Run migration
flask db upgrade
```

### Step 3: Update Environment Variables (.env)
```
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here
DATABASE_URL=sqlite:///users.db
```

### Step 4: Test the Implementation
```bash
# Start the Flask server
python app.py
```

Then test in browser:
1. Go to http://localhost:5000/signup_page
2. Create a new account
3. Go to http://localhost:5000/login_page
4. Login with your credentials
5. Check session status at http://localhost:5000/session_status
6. Logout using http://localhost:5000/logout

## File Changes Summary

### Modified Files
1. **models.py**
   - Added Session model with session tracking
   - Added columns to User model: `created_at`, `last_login`, `is_active`, `sessions` relationship

2. **app.py**
   - Imported Session model and uuid
   - Added session configuration
   - Updated login route to create session records
   - Added logout route
   - Added session validation middleware (@app.before_request)
   - Added session status endpoint
   - Added active sessions endpoint

### New Files
1. **DATABASE_SCHEMA.sql** - Complete SQL schema documentation
2. **SESSION_MANAGEMENT.md** - Comprehensive documentation
3. **IMPLEMENTATION_GUIDE.md** - This file
4. **migrations/versions/001_add_session_management.py** - Database migration

## Key Features Added

### 1. Session Tracking
- Unique session tokens per login
- IP address recording
- User agent tracking
- Login/logout/activity timestamps

### 2. Session Validation
- Automatic validation on every request
- Expiration checking (24 hours default)
- Activity tracking
- Invalid session handling

### 3. Security Features
- Bcrypt password hashing
- HTTP-only cookies
- CSRF protection
- Secure cookie settings

### 4. New Routes
- `POST /login` - Enhanced with session creation
- `POST /signup` - User registration
- `GET /logout` - Session termination
- `GET /session_status` - Current session info
- `GET /active_sessions` - All active sessions for user
- `GET /userpage` - Protected user dashboard

## Database Schema

### User Table
```
- id (PK)
- name, phone, email, password
- created_at, last_login, is_active
```

### Session Table
```
- id (PK)
- user_id (FK)
- session_token, ip_address, user_agent
- login_time, last_activity, logout_time
- is_active, expires_at
```

### Chat & GlobalChat Tables (Unchanged)
- Existing functionality preserved

## Configuration

### Session Timeout
Default: 24 hours
To change, modify in `app.py`:
```python
SESSION_TIMEOUT = 12 * 60 * 60  # 12 hours
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)
```

### Security Settings
All configured in `app.py`:
```python
app.config['SESSION_COOKIE_SECURE'] = True        # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True      # No JS access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'     # CSRF protection
```

## Testing

### Manual Testing Checklist
- [ ] User can sign up
- [ ] User can login
- [ ] Session is created in database
- [ ] Session status shows correct info
- [ ] User can see active sessions
- [ ] User can logout
- [ ] Session is marked as inactive after logout
- [ ] Accessing protected pages redirects to login if not authenticated
- [ ] Session expires after timeout
- [ ] Multiple devices can be logged in simultaneously

### Automated Testing (Example)
```python
import pytest
from app import app, db
from models import User, Session

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

def test_login_creates_session(client):
    # Create user
    user = User(name='Test', phone=123456, email='test@test.com', password='hash')
    db.session.add(user)
    db.session.commit()
    
    # Login
    response = client.post('/login', data={'email': 'test@test.com', 'password': 'pass'})
    
    # Check session exists
    session = Session.query.first()
    assert session is not None
    assert session.user_id == user.id
    assert session.is_active == True

def test_logout_invalidates_session(client):
    # ... login first ...
    response = client.get('/logout')
    
    # Check session is inactive
    session = Session.query.first()
    assert session.is_active == False
    assert session.logout_time is not None
```

## Troubleshooting

### Issue: "No module named 'uuid'"
**Solution:** uuid is built-in to Python, check your import statement

### Issue: "Session table already exists"
**Solution:** 
```bash
# Drop all tables and recreate
python
>>> from app import app, db
>>> with app.app_context():
>>>     db.drop_all()
>>>     db.create_all()
```

### Issue: "Invalid session" on every request
**Solution:** 
- Check SECRET_KEY is set in .env
- Clear browser cookies and login again
- Verify database connection is working

### Issue: Session expires immediately
**Solution:** Check `SESSION_TIMEOUT` value is in seconds (default: 86400 = 24 hours)

### Issue: Database locked (SQLite)
**Solution:** 
- Close other connections
- For production, migrate to PostgreSQL
- Check for long-running queries

## Migration from Old System (If Applicable)

If upgrading from a system without MySQL database:

1. Back up existing database:
   ```bash
   cp users.db users.db.backup
   ```

2. Apply migrations:
   ```bash
   flask db upgrade
   ```

3. Verify tables created:
   ```bash
   python
   >>> from app import app, db
   >>> with app.app_context():
   >>>     inspector = db.inspect(db.engine)
   >>>     print(inspector.get_table_names())
   ```

4. Test login flow completely

## Next Steps

1. **Customize session timeout:** Update `SESSION_TIMEOUT` in app.py
2. **Add logout button:** Include in userpage.html template
3. **Add session management UI:** Create page to manage active sessions
4. **Implement refresh tokens:** For longer session persistence
5. **Add geolocation tracking:** Optional security enhancement
6. **Set up logging:** Monitor login attempts and sessions
7. **Deploy to production:** Use PostgreSQL, HTTPS, and environment variables

## Support & Questions

For detailed information, see:
- `SESSION_MANAGEMENT.md` - Full documentation
- `DATABASE_SCHEMA.sql` - SQL reference
- `models.py` - Model definitions
- `app.py` - Route implementations

## Version Info
- Created: 2026-02-11
- Flask: 3.1.2
- SQLAlchemy: 3.1.1
- Python: 3.8+
