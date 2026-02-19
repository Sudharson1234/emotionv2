# Settings Implementation - Code Examples & API Reference

## Quick Start: Using the Settings Feature

### For End Users

#### 1. Accessing Settings
```
1. Click on "Account Settings" section in Dashboard
2. Click any of the 4 buttons: Change Password, Privacy, Notifications, or Preferences
3. Fill out the form
4. Click Save
5. Success message appears
```

#### 2. From Code Perspective
The URL is `/account/settings` and all functionality is handled server-side.

---

## API Documentation

### POST /account/settings

Base URL: `/account/settings`
Method: `POST`
Content-Type: `application/json`
Authentication: Session-based (requires valid session)

### Request Examples

#### Change Password
```javascript
// Frontend JavaScript
fetch('/account/settings', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        action: 'password',
        current_password: 'currentPass123',
        new_password: 'newSecurePass456'
    })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

Response (Success):
```json
{
    "success": true,
    "message": "Password updated successfully"
}
```

Response (Error - Wrong Current Password):
```json
{
    "success": false,
    "message": "Current password is incorrect"
}
```

#### Privacy Settings
```javascript
fetch('/account/settings', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        action: 'privacy',
        profile_visibility: true,
        activity_visible: true,
        analytics_sharing: false
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('Privacy settings saved');
    }
});
```

Response:
```json
{
    "success": true,
    "message": "Privacy settings updated"
}
```

#### Notifications
```javascript
fetch('/account/settings', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        action: 'notifications',
        email_notifications: true,
        browser_notifications: false,
        analysis_alerts: true
    })
})
.then(response => response.json())
.then(data => console.log(data));
```

Response:
```json
{
    "success": true,
    "message": "Notification settings updated"
}
```

#### Preferences
```javascript
fetch('/account/settings', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        action: 'preferences',
        theme: 'dark',
        language: 'en',
        auto_save: true,
        animations: true
    })
})
.then(response => response.json())
.then(data => console.log(data));
```

Response:
```json
{
    "success": true,
    "message": "Preferences updated"
}
```

---

## Python Backend Examples

### Flask Route Handler

```python
@app.route("/account/settings", methods=["GET", "POST"])
def account_settings():
    """Account settings page"""
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    
    if request.method == "POST":
        action = request.json.get('action')
        user_id = session.get("user_id")
        
        try:
            if action == "password":
                # Get form data
                current_password = request.json.get('current_password')
                new_password = request.json.get('new_password')
                
                # Get user from database
                user = find_user_by_id(user_id)
                if not user:
                    return jsonify({'success': False, 'message': 'User not found'}), 404
                
                # Verify current password
                if not bcrypt.check_password_hash(user['password'], current_password):
                    return jsonify({
                        'success': False, 
                        'message': 'Current password is incorrect'
                    }), 400
                
                # Hash new password
                hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                
                # Update database
                mongo.db.users.update_one(
                    {'_id': user_id},
                    {'$set': {
                        'password': hashed_password, 
                        'updated_at': datetime.utcnow()
                    }}
                )
                
                return jsonify({
                    'success': True, 
                    'message': 'Password updated successfully'
                }), 200
                
            elif action == "privacy":
                settings = {
                    'profile_visibility': request.json.get('profile_visibility', True),
                    'activity_visible': request.json.get('activity_visible', True),
                    'analytics_sharing': request.json.get('analytics_sharing', True)
                }
                mongo.db.users.update_one(
                    {'_id': user_id},
                    {'$set': {
                        'privacy_settings': settings, 
                        'updated_at': datetime.utcnow()
                    }}
                )
                return jsonify({
                    'success': True, 
                    'message': 'Privacy settings updated'
                }), 200
            
            # ... similar for notifications and preferences
            
        except Exception as e:
            logging.error(f"Settings update error: {e}")
            return jsonify({
                'success': False, 
                'message': 'An error occurred'
            }), 500
    
    # GET request - display settings page
    return render_template("settings.html")
```

### MongoDB Query for Retrieving Settings

```python
def get_user_settings(user_id):
    """Retrieve user settings from database"""
    user = mongo.db.users.find_one(
        {'_id': user_id},
        {
            'privacy_settings': 1,
            'notification_settings': 1,
            'preferences': 1
        }
    )
    return user

# Usage
user_settings = get_user_settings(session['user_id'])
if user_settings:
    print(user_settings.get('privacy_settings', {}))
    print(user_settings.get('notification_settings', {}))
    print(user_settings.get('preferences', {}))
```

### MongoDB Update Examples

```python
# Update password
result = mongo.db.users.update_one(
    {'_id': ObjectId(user_id)},
    {'$set': {
        'password': new_hashed_password,
        'updated_at': datetime.utcnow()
    }}
)

# Update privacy settings
result = mongo.db.users.update_one(
    {'_id': ObjectId(user_id)},
    {'$set': {
        'privacy_settings': {
            'profile_visibility': True,
            'activity_visible': False,
            'analytics_sharing': True
        },
        'updated_at': datetime.utcnow()
    }}
)

# Update with $push/$pull (if storing in array)
result = mongo.db.users.update_one(
    {'_id': ObjectId(user_id)},
    {'$set': {'preferences': {...}, 'updated_at': datetime.utcnow()}}
)
```

---

## HTML Form Examples

### Password Change Form
```html
<div class="form-group">
    <label for="currentPassword">Current Password</label>
    <input 
        type="password" 
        id="currentPassword" 
        required 
        placeholder="Enter your current password"
    >
</div>
<div class="form-group">
    <label for="newPassword">New Password</label>
    <input 
        type="password" 
        id="newPassword" 
        required 
        placeholder="Enter new password" 
        minlength="8"
    >
</div>
<div class="form-group">
    <label for="confirmPassword">Confirm Password</label>
    <input 
        type="password" 
        id="confirmPassword" 
        required 
        placeholder="Confirm new password" 
        minlength="8"
    >
</div>
```

### Toggle Switch
```html
<label class="toggle-switch">
    <input type="checkbox" id="profileVisibility" checked>
    <span class="slider"></span>
</label>
```

### Dropdown Select
```html
<select id="theme">
    <option value="dark" selected>Dark Mode</option>
    <option value="light">Light Mode</option>
    <option value="auto">Auto (System)</option>
</select>
```

---

## JavaScript Functions

### Form Submission Handler
```javascript
async function handlePasswordChange(e) {
    e.preventDefault();
    
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    // Validation
    if (newPassword !== confirmPassword) {
        showAlert('passwordMessage', 'Passwords do not match!', 'error');
        return;
    }

    if (newPassword.length < 8) {
        showAlert('passwordMessage', 
            'Password must be at least 8 characters long!', 'error');
        return;
    }

    try {
        // Send to server
        const response = await fetch('/account/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'password',
                current_password: currentPassword,
                new_password: newPassword
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            showAlert('passwordMessage', 
                'Password updated successfully!', 'success');
            document.getElementById('password-section')
                .querySelector('form').reset();
            setTimeout(hideSection, 2000);
        } else {
            showAlert('passwordMessage', 
                data.message || 'An error occurred', 'error');
        }
    } catch (error) {
        showAlert('passwordMessage', 
            'An error occurred. Please try again.', 'error');
        console.error('Error:', error);
    }
}
```

### Navigation Functions
```javascript
function showSection(section) {
    // Hide all sections
    document.getElementById('settingsGrid').style.display = 'none';
    document.getElementById('password-section').style.display = 'none';
    document.getElementById('privacy-section').style.display = 'none';
    document.getElementById('notifications-section').style.display = 'none';
    document.getElementById('preferences-section').style.display = 'none';

    // Show selected section
    document.getElementById(section + '-section').style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function hideSection() {
    document.getElementById('settingsGrid').style.display = 'grid';
    document.getElementById('password-section').style.display = 'none';
    document.getElementById('privacy-section').style.display = 'none';
    document.getElementById('notifications-section').style.display = 'none';
    document.getElementById('preferences-section').style.display = 'none';
}
```

### Alert Display
```javascript
function showAlert(containerId, message, type) {
    const container = document.getElementById(containerId);
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `<i class="fas fa-${type === 'success' 
        ? 'check-circle' 
        : 'exclamation-circle'}"></i> ${message}`;
    
    container.innerHTML = '';
    container.appendChild(alertDiv);
    
    setTimeout(() => alertDiv.remove(), 4000);
}
```

---

## Current Database Schema (After Settings Implementation)

```javascript
// User Document in MongoDB
{
    _id: ObjectId("..."),
    email: "user@example.com",
    password: "$2b$12$...",  // bcrypt hash
    name: "John Doe",
    phone: "1234567890",
    created_at: ISODate("2024-01-15T10:30:00Z"),
    updated_at: ISODate("2024-01-15T14:45:00Z"),
    
    // NEW: Privacy Settings
    privacy_settings: {
        profile_visibility: true,
        activity_visible: true,
        analytics_sharing: true
    },
    
    // NEW: Notification Settings
    notification_settings: {
        email_notifications: true,
        browser_notifications: true,
        analysis_alerts: true
    },
    
    // NEW: User Preferences
    preferences: {
        theme: "dark",
        language: "en",
        auto_save: true,
        animations: true
    }
}
```

---

## Error Handling Examples

### Try-Catch Block
```python
try:
    # Attempt database operation
    mongo.db.users.update_one(
        {'_id': user_id},
        {'$set': {'preferences': settings}}
    )
    return jsonify({'success': True, 'message': '...'}), 200
except pymongo.errors.PyMongoError as e:
    logging.error(f"Database error: {e}")
    return jsonify({'success': False, 'message': 'Database error'}), 500
except Exception as e:
    logging.error(f"Unexpected error: {e}")
    return jsonify({'success': False, 'message': 'An error occurred'}), 500
```

### Frontend Error Handling
```javascript
try {
    const response = await fetch('/account/settings', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.success) {
        // Handle success
    } else {
        // Handle API error
        showAlert(containerId, result.message, 'error');
    }
} catch (error) {
    // Handle network/parsing errors
    showAlert(containerId, 'An error occurred. Please try again.', 'error');
    console.error('Fetch error:', error);
}
```

---

## Testing / Debugging

### Check MongoDB Settings
```python
# In Python shell
from models import find_user_by_id
user = find_user_by_id('your_user_id')
print(user.get('privacy_settings'))
print(user.get('notification_settings'))
print(user.get('preferences'))
```

### Test Password Hashing
```python
from flask_bcrypt import Bcrypt
from flask import Flask

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Hash a password
password = "myPassword123"
hashed = bcrypt.generate_password_hash(password).decode('utf-8')

# Check password
is_correct = bcrypt.check_password_hash(hashed, password)
print(is_correct)  # Should be True
```

### Browser DevTools
```javascript
// In browser console
// Check if settings were saved to localStorage
console.log(localStorage.getItem('theme'));

// Make test API call
fetch('/account/settings', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        action: 'preferences',
        theme: 'light',
        language: 'es',
        auto_save: false,
        animations: true
    })
})
.then(r => r.json())
.then(d => console.log('Response:', d));
```

---

## Production Deployment Checklist

- [ ] Verify MongoDB is connected and indexes created
- [ ] Test password change with actual bcrypt hashing
- [ ] Verify session validation works correctly
- [ ] Test all form submissions and error cases
- [ ] Check responsive design on mobile devices
- [ ] Verify navigation between settings sections
- [ ] Test with different user accounts
- [ ] Check browser console for JavaScript errors
- [ ] Verify alerts display correctly
- [ ] Test logout after settings change
- [ ] Verify settings persist after refresh
- [ ] Monitor server logs for errors
- [ ] Check HTTPS/SSL configuration
- [ ] Verify CORS headers if API called from different domain
- [ ] Load test the endpoints
- [ ] Document any custom configurations needed
