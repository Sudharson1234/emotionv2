# Settings Implementation Guide

## Overview
A comprehensive account settings page has been implemented with four major sections to manage user preferences and security:

1. **Change Password** - Securely update account password
2. **Privacy Settings** - Control profile visibility and activity sharing
3. **Notifications** - Manage email, browser, and alert notifications
4. **Preferences** - Customize theme, language, and display options

## Features Implemented

### 1. Change Password
- **Route:** `/account/settings` (POST with action: "password")
- **Security Features:**
  - Requires current password verification
  - Password hash validation using bcrypt
  - Minimum 8-character requirement enforced
  - Password confirmation matching
  - MongoDB database update with timestamp

- **Form Fields:**
  - Current Password (required)
  - New Password (required, min 8 chars)
  - Confirm Password (required, min 8 chars)

- **Backend Flow:**
  1. Validates user session
  2. Fetches user from database
  3. Verifies current password against stored hash
  4. Validates new password format
  5. Hashes new password with bcrypt
  6. Updates MongoDB user document
  7. Returns success/error response

### 2. Privacy Settings
- **Route:** `/account/settings` (POST with action: "privacy")
- **Features:**
  - Profile Visibility toggle (allow others to view profile)
  - Activity Visibility toggle (show recent activity)
  - Analytics Sharing toggle (help improve app with data sharing)

- **Data Persistence:**
  - Stored in MongoDB under `privacy_settings` object
  - Includes: `profile_visibility`, `activity_visible`, `analytics_sharing` (all boolean)

- **Backend:**
  - Validates user session
  - Creates/updates `privacy_settings` object in user document
  - Stores timestamp of last update

### 3. Notifications
- **Route:** `/account/settings` (POST with action: "notifications")
- **Options:**
  - Email Notifications (receive email updates about activity)
  - Browser Notifications (receive browser push notifications)
  - Analysis Alerts (get notified when analysis is complete)

- **Data Persistence:**
  - Stored in MongoDB under `notification_settings` object
  - Includes: `email_notifications`, `browser_notifications`, `analysis_alerts` (all boolean)

- **Implementation:**
  - Frontend toggles with visual on/off state
  - Backend stores preferences for future use
  - Can be integrated with notification delivery system

### 4. Preferences
- **Route:** `/account/settings` (POST with action: "preferences")
- **Options:**
  - **Theme:** Dark Mode (default), Light Mode, Auto (System)
  - **Language:** English (en), Spanish (es), French (fr), German (de), Arabic (ar)
  - **Auto-Save Results:** Toggle automatic result saving
  - **Enable Animations:** Toggle UI animations and transitions

- **Data Persistence:**
  - Stored in MongoDB under `preferences` object
  - Theme also saved to localStorage for instant client-side application
  - Includes: `theme`, `language`, `auto_save`, `animations`

## File Structure

### Frontend Files
```
templates/
└── settings.html (new)
    ├── Navbar with navigation
    ├── Settings grid (4 cards)
    ├── Change Password form
    ├── Privacy Settings form
    ├── Notifications form
    ├── Preferences form
    └── Client-side validation & submission handlers
```

### Backend Files
```
app.py (modified)
├── @app.route("/account/settings") - GET shows settings page
│   └── POST handles form submissions with action parameter
├── Password validation & hashing
├── MongoDB updates for all settings
└── Session verification

templates/userpage.html (modified)
├── Changed settings buttons from onclick alerts to links
└── All buttons now link to /account/settings route
```

## UI Design

### Layout
- **Header:** Dark theme navbar with navigation links
- **Main Section:** Settings grid showing 4 cards (initially)
- **Form Sections:** Display one form at a time (card shows; others hidden)
- **Responsive:** Grid layout adapts to different screen sizes

### Design Features
- **Color Scheme:** Matches existing dark theme (--bg-primary, --accent-primary, etc.)
- **Icons:** Font Awesome icons for visual identification
- **Cards:** Clickable cards to select settings section
- **Forms:** Clean form layout with labels and input validation
- **Alerts:** Toast-style success/error messages
- **Animations:** Smooth transitions and slidein effects

### Styling Variables
```css
--bg-primary: #0f1419        /* Dark background */
--bg-secondary: #1a2332      /* Secondary background */
--border-color: #2a3f5f      /* Borders */
--text-primary: #e0e6ed      /* Main text */
--text-secondary: #8b96a5    /* Secondary text */
--accent-primary: #00d4ff    /* Cyan accent */
--accent-success: #10b981    /* Green success */
--accent-danger: #ef4444     /* Red danger */
```

## API Endpoints

### Settings Update Endpoint
- **URL:** `/account/settings`
- **Method:** POST
- **Content-Type:** application/json
- **Authentication:** Required (session-based)

#### Request Format
```json
{
    "action": "password|privacy|notifications|preferences",
    // Additional fields based on action
}
```

#### Password Change Request
```json
{
    "action": "password",
    "current_password": "currentPass123",
    "new_password": "newPass12345"
}
```

#### Privacy Settings Request
```json
{
    "action": "privacy",
    "profile_visibility": true,
    "activity_visible": true,
    "analytics_sharing": true
}
```

#### Notifications Request
```json
{
    "action": "notifications",
    "email_notifications": true,
    "browser_notifications": true,
    "analysis_alerts": true
}
```

#### Preferences Request
```json
{
    "action": "preferences",
    "theme": "dark",
    "language": "en",
    "auto_save": true,
    "animations": true
}
```

#### Success Response
```json
{
    "success": true,
    "message": "Settings updated successfully"
}
```

#### Error Response
```json
{
    "success": false,
    "message": "Error description"
}
```

## Database Schema

Existing user document enhanced with settings fields:

```javascript
{
    _id: ObjectId,
    email: string,
    password: string,  // bcrypt hash
    name: string,
    created_at: Date,
    updated_at: Date,
    
    // New fields
    privacy_settings: {
        profile_visibility: Boolean,
        activity_visible: Boolean,
        analytics_sharing: Boolean
    },
    
    notification_settings: {
        email_notifications: Boolean,
        browser_notifications: Boolean,
        analysis_alerts: Boolean
    },
    
    preferences: {
        theme: String,        // "dark", "light", "auto"
        language: String,     // "en", "es", "fr", "de", "ar"
        auto_save: Boolean,
        animations: Boolean
    }
}
```

## Security Considerations

1. **Password Validation:**
   - Current password verification before allowing change
   - Minimum 8-character requirement
   - Bcrypt hashing with salt

2. **Session Management:**
   - All routes check for valid session
   - User ID retrieved from session (not user input)
   - MongoDB operations scoped to current user only

3. **Input Validation:**
   - Client-side form validation
   - Server-side type checking (boolean, string)
   - MongoDB queries use user session ID (prevents cross-user updates)

4. **Error Handling:**
   - Specific error messages for debugging
   - Generic messages in production could be added
   - Logging of errors for monitoring

## User Journey

### From Dashboard to Settings
```
userpage.html (Dashboard)
    ↓
Settings buttons (Account Settings section)
    ↓
/account/settings route (GET)
    ↓
settings.html page (Settings grid)
    ↓
User clicks card → Form shows
    ↓
User submits form
    ↓
JavaScript fetch POST to /account/settings
    ↓
Backend processes (validates, updates MongoDB)
    ↓
Success/error alert
    ↓
Redirect to grid or show error
```

## Frontend JavaScript Functions

### Navigation
- `showSection(section)` - Display selected settings section
- `hideSection()` - Hide form, show grid

### Alerts
- `showAlert(containerId, message, type)` - Display toast alert

### Form Handlers
- `handlePasswordChange(e)` - Validate and submit password form
- `handlePrivacyChange(e)` - Submit privacy settings
- `handleNotificationsChange(e)` - Submit notification preferences
- `handlePreferencesChange(e)` - Submit user preferences

### Utilities
- `loadUserSettings()` - Load saved settings on page load

## Testing Checklist

- [ ] Can navigate to settings from userpage
- [ ] Can display settings grid with 4 cards
- [ ] Can click cards to show/hide forms
- [ ] Can enter current password (validation for minimum length)
- [ ] Can verify password change validation
- [ ] Can toggle privacy settings
- [ ] Can toggle notification preferences
- [ ] Can select theme, language, auto-save, animations
- [ ] Can submit forms and see success message
- [ ] MongoDB updates are reflected in database
- [ ] Session check blocks unauthorized access
- [ ] Error messages display on form submission errors
- [ ] Responsive design works on mobile/tablet
- [ ] Icons display correctly
- [ ] Navigation links work

## Future Enhancements

1. **Theme Application:** Implement theme switching system for light/dark/auto modes
2. **Language System:** Integrate multilingual support based on language preference
3. **Email Notifications:** Connect to email service (SendGrid, etc.)
4. **Browser Notifications:** Implement Web Push API integration
5. **Two-Factor Authentication:** Add 2FA option to security settings
6. **Activity Log:** Show user account activity history
7. **Connected Devices:** List and manage active sessions
8. **Data Export:** Allow users to export their data
9. **Account Deletion:** Add secure account deletion flow
10. **Settings Recovery:** Allow users to recover previous settings

## Integration Notes

- Settings page fully matches dark theme of existing application
- Uses same CSS variables and styling patterns as other pages
- Navbar includes links back to home, dashboard, and analytics
- All form submissions use modern fetch API
- Error handling includes both client-side and server-side validation
- MongoDB integration follows existing patterns in the application

## Troubleshooting

### Settings page not loading
- Check `/account/settings` route exists in app.py
- Verify user session is valid
- Check browser console for JavaScript errors

### Form submissions fail
- Verify POST request includes proper JSON content-type
- Check MongoDB connection
- Review server logs for error details
- Ensure bcrypt is properly initialized for password changes

### Settings not persisting in MongoDB
- Verify MongoDB is connected
- Check user_id is correctly retrieved from session
- Ensure MongoDB update_one query has proper user_id filter
- Check MongoDB user document for new fields

### Styling issues
- Verify Font Awesome CDN link loads
- Check CSS variable names match
- Inspect element to see if styles apply
- Clear browser cache if changes not visible
