# Settings Implementation - Architecture & Flow Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         WEB BROWSER                             │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Frontend (HTML/CSS/JavaScript)              │ │
│  │                                                           │ │
│  │  settings.html                                           │ │
│  │  ├─ Navbar (Navigation)                                  │ │
│  │  ├─ Settings Grid (4 Cards)                              │ │
│  │  ├─ Change Password Form                                 │ │
│  │  ├─ Privacy Settings Form                                │ │
│  │  ├─ Notifications Form                                   │ │
│  │  └─ Preferences Form                                     │ │
│  │                                                           │ │
│  │  Form Handlers:                                          │ │
│  │  ├─ handlePasswordChange()                               │ │
│  │  ├─ handlePrivacyChange()                                │ │
│  │  ├─ handleNotificationsChange()                          │ │
│  │  └─ handlePreferencesChange()                            │ │
│  │                                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  fetch POST /account/settings (JSON)                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↑↓
                    HTTP POST/JSON Response
                              ↑↓
┌─────────────────────────────────────────────────────────────────┐
│                        WEB SERVER (Flask)                       │
│                                                                 │
│  app.py                                                         │
│  @app.route("/account/settings", methods=["GET", "POST"])      │
│  ├─ GET: render_template("settings.html")                      │
│  └─ POST:                                                       │
│      ├─ Check session valid (user_id in session)               │
│      ├─ Get action from request.json                           │
│      ├─ action = "password":                                   │
│      │   ├─ find_user_by_id(user_id)                           │
│      │   ├─ bcrypt.check_password_hash(...)                    │
│      │   ├─ Validation                                         │
│      │   ├─ mongo.db.users.update_one(...)                     │
│      │   └─ Return status                                      │
│      ├─ action = "privacy":                                    │
│      │   ├─ Build privacy_settings dict                        │
│      │   ├─ mongo.db.users.update_one(...)                     │
│      │   └─ Return status                                      │
│      ├─ action = "notifications":                              │
│      │   ├─ Build notification_settings dict                   │
│      │   ├─ mongo.db.users.update_one(...)                     │
│      │   └─ Return status                                      │
│      └─ action = "preferences":                                │
│          ├─ Build preferences dict                             │
│          ├─ mongo.db.users.update_one(...)                     │
│          └─ Return status                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↑↓
                    MongoDB update_one()
                              ↑↓
┌─────────────────────────────────────────────────────────────────┐
│                       MONGODB DATABASE                          │
│                                                                 │
│  Collection: users                                              │
│  Document:                                                      │
│  {                                                              │
│    _id: ObjectId(...),                                          │
│    email: "user@example.com",                                   │
│    password: "$2b$12$...",  (bcrypt hash)                       │
│    name: "John Doe",                                            │
│    created_at: ISODate(...),                                    │
│    updated_at: ISODate(...),                                    │
│    privacy_settings: { ... },     ← NEW                         │
│    notification_settings: { ... }, ← NEW                        │
│    preferences: { ... }          ← NEW                          │
│  }                                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## User Journey Flow

```
┌─────────────────────────┐
│ User on Dashboard Page  │
│ (userpage.html)         │
└────────────┬────────────┘
             │
             ↓
┌──────────────────────────────────┐
│ Account Settings Section visible │
│ with 4 buttons                   │
│ - Change Password                │
│ - Privacy                        │
│ - Notifications                  │
│ - Preferences                    │
└────────────┬─────────────────────┘
             │ (User clicks any button)
             ↓
┌──────────────────────────────────┐
│ GET /account/settings            │
│ (Flask routes to settings.html)  │
└────────────┬─────────────────────┘
             │
             ↓
┌──────────────────────────────────┐
│ Settings Page Loads              │
│ Displays Settings Grid with      │
│ 4 clickable cards                │
└────────────┬─────────────────────┘
             │ (User clicks a card)
             ↓
         ┌───┴────┬──────┬──────────┐
         ↓        ↓      ↓          ↓
    ┌────────┐ ┌─────┐ ┌──────┐ ┌──────────┐
    │Password│ │Priva│ │Notif │ │Preference│
    │Form    │ │cy   │ │cation│ │s         │
    └───┬────┘ └──┬──┘ └──┬───┘ └────┬─────┘
        │         │       │          │
        ↓         ↓       ↓          ↓
   (User fills out form & clicks Save)
        │         │       │          │
        ↓         ↓       ↓          ↓
   ┌─────────────────────────────────────┐
   │ JavaScript Validation               │
   │ ├─ Password: length, match check    │
   │ ├─ Privacy: boolean check           │
   │ ├─ Notifications: boolean check     │
   │ └─ Preferences: type check          │
   └──────────┬──────────────────────────┘
              │ (If validation passes)
              ↓
   ┌─────────────────────────────────────┐
   │ fetch POST /account/settings        │
   │ {                                   │
   │   action: "password|privacy|...",   │
   │   ... specific fields ...           │
   │ }                                   │
   └──────────┬──────────────────────────┘
              │
              ↓
   ┌─────────────────────────────────────┐
   │ Server Processing                   │
   │ ├─ Session check                    │
   │ ├─ Validation                       │
   │ ├─ Bcrypt hashing (if password)     │
   │ ├─ MongoDB update_one()             │
   │ ├─ Error handling                   │
   │ └─ Response JSON                    │
   └──────────┬──────────────────────────┘
              │
        ┌─────┴──────┐
        ↓            ↓
   ┌────────────┐ ┌──────────────┐
   │ Success    │ │ Error        │
   │ Response   │ │ Response     │
   └──┬─────────┘ └──────┬───────┘
      │                  │
      ↓                  ↓
   ┌─────────────────────────────────────┐
   │ Show Alert                          │
   │ "Setting updated successfully!" ✓   │
   │ or                                  │
   │ "Error message" ✗                   │
   └──────────┬──────────────────────────┘
              │
              ↓
   ┌─────────────────────────────────────┐
   │ After 4 seconds or user action:     │
   │ ├─ Form resets (password only)      │
   │ └─ Returns to settings grid         │
   │    (User can edit another setting)  │
   └─────────────────────────────────────┘
```

## Password Change Flow (Detailed)

```
User fills form:
- Current Password: "oldPass123"
- New Password: "newSecure456"
- Confirm Password: "newSecure456"
        ↓
Client-side validation:
├─ New ≠ Confirm? → Error
├─ Length < 8? → Error
└─ Pass → POST request
        ↓
Server receives request:
├─ Check session: user_id present?
├─ Find user in MongoDB
├─ Get stored password hash
├─ Verify: bcrypt.check_password_hash(stored, currentPwd)
│  ├─ Match? → Continue
│  └─ No match? → Return "Password incorrect" error
├─ Hash new password: bcrypt.generate_password_hash(newPwd)
├─ Update MongoDB:
│  └─ db.users.update_one({'_id': user_id}, {'$set': {
│       'password': new_hash,
│       'updated_at': datetime.utcnow()
│     }})
├─ Log: "Password changed for user_id"
└─ Return success
        ↓
Frontend receives success:
├─ Show "Password updated successfully!" alert
├─ Clear form
├─ After 2s: Hide form, show grid
└─ User can make another change
```

## Database Update Flow

```
MongoDB Document (Before):
{
  _id: ObjectId("..."),
  email: "user@example.com",
  password: "old_hash_...",
  name: "User",
  created_at: ISODate("2024-01-01T..."),
  updated_at: ISODate("2024-01-01T...")
  // No privacy_settings, notification_settings, preferences
}

        ↓ (First POST /account/settings for privacy)

MongoDB Document (After):
{
  _id: ObjectId("..."),
  email: "user@example.com",
  password: "old_hash_...",
  name: "User",
  created_at: ISODate("2024-01-01T..."),
  updated_at: ISODate("2024-01-15T14:30:00Z"),  ← Updated
  privacy_settings: {                           ← Added
    profile_visibility: true,
    activity_visible: true,
    analytics_sharing: false
  },
  notification_settings: { ... },               ← Will be added
  preferences: { ... }                          ← Will be added
}

        ↓ (Second POST /account/settings for notifications)

MongoDB Document (Final):
{
  _id: ObjectId("..."),
  email: "user@example.com",
  password: "old_hash_...",
  name: "User",
  created_at: ISODate("2024-01-01T..."),
  updated_at: ISODate("2024-01-15T14:45:00Z"),  ← Updated again
  privacy_settings: {
    profile_visibility: true,
    activity_visible: true,
    analytics_sharing: false
  },
  notification_settings: {                      ← Added
    email_notifications: true,
    browser_notifications: false,
    analysis_alerts: true
  },
  preferences: {                                ← Added
    theme: "dark",
    language: "en",
    auto_save: true,
    animations: true
  }
}
```

## Form State Machine

```
                    ┌──────────────────┐
                    │   INITIAL STATE  │
                    │  (Grid showing)  │
                    └────────┬─────────┘
                             │
                 (User clicks "Change Password")
                             │
                    ┌────────▼─────────┐
                    │  PASSWORD FORM   │
                    │  (form visible)  │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
   (User fills data)  (Click Cancel)  (Fill incomplete)
              │              │              │
              ↓              ↓              ↓
        ┌─────────────┐  GRID  ┌────────────────┐
        │ SUBMITTED   │  ←─────│ FORM RESET     │
        │ (validation)│        │ (returns to    │
        └──────┬──────┘        │  grid)         │
               │               └────────────────┘
        ┌──────┴──────┐
        │             │
   (Valid)       (Invalid)
        │             │
        ↓             ↓
   ┌────────┐    ┌──────────────┐
   │REQUEST │    │ERROR DISPLAYED│
   │ (POST) │    │ (message)    │
   └────┬───┘    │ (form stays) │
        │        └──────────────┘
    ┌───┴────┐
    │        │
(Success) (Error)
    │        │
    ↓        ↓
┌────────┐ ┌──────────┐
│ ALERT  │ │ ERROR    │
│ (ok)   │ │ DISPLAYED│
└───┬────┘ │ (form   │
    │      │  stays) │
    │      └──────────┘
    ↓
┌────────┐
│ GRID   │
│RESET  │
└────────┘
```

## API Request/Response Cycle

```
FRONTEND (Browser)
├─ Collect form data
├─ Validate locally
├─ Build JSON payload
├─ Call fetch('/account/settings', {...})
│
├─ Request Headers:
│  ├─ Content-Type: application/json
│  ├─ Cookie: session=abc123... (automatic)
│  └─ (CORS headers as needed)
│
└─ Request Body:
   {
     action: "password|privacy|notifications|preferences",
     // action-specific fields
   }

                    ↓↓↓ HTTP POST ↓↓↓

SERVER (Flask)
├─ Receive request
├─ Parse JSON
├─ Check request.method == "POST"
├─ Extract action parameter
├─ Validate session:
│  └─ Check user_id in session
│
├─ IF action == "password":
│  ├─ Get current/new passwords
│  ├─ Query user from MongoDB
│  ├─ Verify current password with bcrypt
│  ├─ Hash new password
│  ├─ Update MongoDB
│  ├─ Log action
│  └─ Build response
│
├─ ... (similar for other actions) ...
│
└─ Response Headers:
   ├─ Content-Type: application/json
   └─ (CORS headers as needed)

Response Body (Success):
{
  "success": true,
  "message": "Setting updated successfully"
}

Response Body (Error):
{
  "success": false,
  "message": "Error description here"
}

                    ↓↓↓ Response ↓↓↓

FRONTEND (Browser)
├─ Parse response JSON
├─ Check response.ok
├─ Check result.success
├─ IF success:
│  ├─ Show success alert
│  ├─ Clear form
│  └─ Schedule return to grid (2s)
│
└─ IF error:
   ├─ Show error alert
   ├─ Keep form data
   └─ User can retry
```

## Component Interaction Matrix

```
                 Settings    Password   Privacy   Notifications  Preferences
                  Grid        Form      Form       Form            Form
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Display          Visible     Hidden    Hidden     Hidden          Hidden
(Initial)        (all cards)

Click Card 1     Hide        Show      Hide       Hide            Hide
                 (Password)

Click Card 2     Hide        Hide      Show       Hide            Hide
                 (Privacy)

Click Card 3     Hide        Hide      Hide       Show            Hide
                 (Notifications)

Click Card 4     Hide        Hide      Hide       Hide            Show
                 (Preferences)

Click Cancel     Show        Hide      Hide       Hide            Hide
                 (all cards)

Submit Form      Show        Hide      Hide       Hide            Hide
(Success)        (all cards)

Submit Form      Unchanged   Visible   Visible    Visible        Visible
(Error)          (remains)   (keeps    (keeps     (keeps         (keeps
                             data)     data)      data)          data)

MongoDB          ----        Updated   Updated    Updated        Updated
Update                       (password)(privacy)  (notifications)(preferences)

Browser Storage  ----        ----      ----       ----           Updated
localStorage                                                     (theme)
```

## Data Flow For Settings Persistence

```
User enters settings → Form validation → POST request → Server processes
                                              ↓
                                    Check session valid
                                              ↓
                                    Validate input types
                                              ↓
                                    Hash password (if password)
                                              ↓
                                    MongoDB: find user by _id
                                              ↓
                                    MongoDB: update_one with $set
                                              ↓
                                    Timestamp added automatically
                                              ↓
                                    Return success response
                                              ↓
                                    Frontend shows alert
                                              ↓
                                    (On next login, settings reload)
                                              ↓
                                    Settings are persistent!
```

---

## Technology Stack Diagram

```
┌────────────────┐
│  FRONTEND      │
├────────────────┤
│ HTML5          │
│ CSS3           │
│ JavaScript ES6+│
│ Font Awesome   │
│ Responsive     │
└────────┬───────┘
         │
    ┌────▼────┐
    │  HTTP   │
    │  REST   │
    └────┬────┘
         │
┌────────▼────────┐
│  BACKEND        │
├────────────────┤
│ Flask          │
│ Python 3.x     │
│ Flask-Bcrypt   │
│ Flask-Session  │
└────────┬────────┘
         │
    ┌────▼────┐
    │ MongoDB │
    │ Query   │
    └────┬────┘
         │
┌────────▼────────┐
│  DATABASE       │
├────────────────┤
│ MongoDB        │
│ Collections    │
│ Indexes        │
└────────────────┘
```

---

These diagrams provide visual representations of:
1. System architecture and component relationships
2. User journey through the settings system
3. Detailed flow for password changes
4. Database state transitions
5. Form state machine
6. API request/response cycle
7. Component interaction matrix
8. Data persistence flow
9. Technology stack

Use these diagrams when:
- Onboarding new developers
- Explaining the system to stakeholders
- Debugging issues (trace through the flow)
- Planning enhancements
- Documentation and training
