# Settings Pages - Visual Reference & Navigation Guide

## Page Structure Overview

```
/account/settings
├── Navbar (persistent across all states)
│   ├── Logo: "emoti" with heart-pulse icon
│   ├── Navigation Links: Home | Dashboard | Analytics | Logout
│   └── Header background: Dark theme (--bg-secondary)
│
├── Main Container
│   ├── Settings Header
│   │   ├── Title: "Account Settings" with cogs icon
│   │   └── Description: "Manage your account preferences and security"
│   │
│   ├── STATE 1: Settings Grid (Initial Load)
│   │   ├── Card 1: Change Password
│   │   │   ├── Icon: Key
│   │   │   ├── Title: "Change Password"
│   │   │   └── Description: "Update your password and keep your account secure"
│   │   │
│   │   ├── Card 2: Privacy Settings
│   │   │   ├── Icon: Shield
│   │   │   ├── Title: "Privacy Settings"
│   │   │   └── Description: "Control who can see your activity and profile"
│   │   │
│   │   ├── Card 3: Notifications
│   │   │   ├── Icon: Bell
│   │   │   ├── Title: "Notifications"
│   │   │   └── Description: "Manage email and browser notifications"
│   │   │
│   │   └── Card 4: Preferences
│   │       ├── Icon: Sliders
│   │       ├── Title: "Preferences"
│   │       └── Description: "Customize your experience and display options"
│   │
│   ├── STATE 2: Change Password Form (onclick Card 1)
│   │   ├── Title: "Change Password" with key icon
│   │   ├── Message Container (for alerts)
│   │   ├── Form:
│   │   │   ├── Current Password (type: password)
│   │   │   ├── New Password (type: password, minlength: 8)
│   │   │   ├── Confirm Password (type: password, minlength: 8)
│   │   │   └── Button Group:
│   │   │       ├── "Update Password" (primary - cyan)
│   │   │       └── "Cancel" (secondary)
│   │   └── Transitions: Scroll to top, smooth fade
│   │
│   ├── STATE 3: Privacy Settings Form (onclick Card 2)
│   │   ├── Title: "Privacy Settings" with shield icon
│   │   ├── Message Container
│   │   ├── Form:
│   │   │   ├── Toggle 1: Profile Visibility
│   │   │   │   ├── Switch
│   │   │   │   ├── Label: "Profile Visibility"
│   │   │   │   └── Description: "Allow others to view your profile"
│   │   │   │
│   │   │   ├── Toggle 2: Activity Visibility
│   │   │   │   ├── Switch
│   │   │   │   ├── Label: "Activity Visibility"
│   │   │   │   └── Description: "Show your recent activity"
│   │   │   │
│   │   │   ├── Toggle 3: Analytics Sharing
│   │   │   │   ├── Switch
│   │   │   │   ├── Label: "Analytics Sharing"
│   │   │   │   └── Description: "Help us improve by sharing analytics"
│   │   │   │
│   │   │   └── Button Group:
│   │   │       ├── "Save Settings" (primary)
│   │   │       └── "Cancel" (secondary)
│   │   └── All toggles checked by default
│   │
│   ├── STATE 4: Notifications Form (onclick Card 3)
│   │   ├── Title: "Notifications" with bell icon
│   │   ├── Message Container
│   │   ├── Form:
│   │   │   ├── Toggle 1: Email Notifications
│   │   │   │   ├── Switch
│   │   │   │   ├── Label: "Email Notifications"
│   │   │   │   └── Description: "Receive email updates about your activity"
│   │   │   │
│   │   │   ├── Toggle 2: Browser Notifications
│   │   │   │   ├── Switch
│   │   │   │   ├── Label: "Browser Notifications"
│   │   │   │   └── Description: "Receive browser notifications"
│   │   │   │
│   │   │   ├── Toggle 3: Analysis Alerts
│   │   │   │   ├── Switch
│   │   │   │   ├── Label: "Analysis Alerts"
│   │   │   │   └── Description: "Get notified when analysis is complete"
│   │   │   │
│   │   │   └── Button Group:
│   │   │       ├── "Save Settings" (primary)
│   │   │       └── "Cancel" (secondary)
│   │   └── All toggles checked by default
│   │
│   └── STATE 5: Preferences Form (onclick Card 4)
│       ├── Title: "Preferences" with sliders icon
│       ├── Message Container
│       ├── Form:
│       │   ├── Dropdown 1: Theme
│       │   │   ├── Label: "Theme"
│       │   │   └── Options: Dark Mode (default) | Light Mode | Auto (System)
│       │   │
│       │   ├── Dropdown 2: Language
│       │   │   ├── Label: "Language"
│       │   │   └── Options: English | Spanish | French | German | Arabic
│       │   │
│       │   ├── Toggle 1: Auto-Save Results
│       │   │   ├── Switch
│       │   │   ├── Label: "Auto-Save Results"
│       │   │   └── Description: "Automatically save analysis results"
│       │   │
│       │   ├── Toggle 2: Enable Animations
│       │   │   ├── Switch
│       │   │   ├── Label: "Enable Animations"
│       │   │   └── Description: "Show animations and transitions"
│       │   │
│       │   └── Button Group:
│       │       ├── "Save Preferences" (primary)
│       │       └── "Cancel" (secondary)
│       └── Dropdowns and toggles use saved values
│
└── Footer: None (extends to bottom)
```

## Visual Design Elements

### Color Palette
```css
Primary Background:     #0f1419 (very dark blue-gray)
Secondary Background:   #1a2332 (dark blue)
Border Color:          #2a3f5f (medium dark blue)
Primary Text:          #e0e6ed (light gray)
Secondary Text:        #8b96a5 (medium gray)
Accent Primary:        #00d4ff (cyan)
Accent Success:        #10b981 (green)
Accent Danger:         #ef4444 (red)
```

### Typography
```
Headings:    Bold, primary text color, 18-32px
Labels:      Font weight 600, 14px
Placeholder: Secondary text color
Body:        Regular weight, 14px
```

### Components

#### Cards (Initial Grid)
- Background: Secondary (darker)
- Border: 1px solid border-color
- Border-radius: 12px
- Padding: 24px
- Hover: Border becomes accent-primary, subtle background highlight
- Cursor: Pointer

#### Forms
- Background: Secondary color
- Padding: 30px
- Border-radius: 12px
- Border: 1px solid border-color
- Displayed: One at a time (display: none/block)

#### Input Fields
- Background: Primary (darker than form)
- Text color: Primary text
- Border: 1px solid border-color
- Border-radius: 6px
- Padding: 12px
- Focus: Border becomes accent-primary with subtle glow

#### Buttons
- Primary (Save/Update): Accent cyan with dark text
- Secondary (Cancel): Border color background
- Padding: 12px 24px
- Border-radius: 6px
- Font-weight: 600
- Cursor: Pointer
- Hover: Slight transform + shadow effects

#### Toggle Switches
- Width: 50px
- Height: 24px
- Background: Gray when off
- Background: Accent cyan when on (#00d4ff)
- Smooth animation: 0.4s transition
- Thumb: White circle, 18x18px

#### Alerts
- Success: Green background + border (#10b981)
- Error: Red background + border (#ef4444)
- Padding: 16px
- Border-radius: 6px
- Auto-hide: 4 seconds
- Animation: Slide in from top + fade in

### Icons (Font Awesome 6.4.0)
```
Key:              fas fa-key            (Password)
Shield:           fas fa-shield-alt     (Privacy)
Bell:             fas fa-bell           (Notifications)
Sliders:          fas fa-sliders-h      (Preferences)
Heart Pulse:      fas fa-heart-pulse    (Logo)
Home:             fas fa-home           (Navigation)
User:             fas fa-user           (Dashboard)
Chart:            fas fa-chart-line     (Analytics)
Sign Out:         fas fa-sign-out-alt   (Logout)
Save:             fas fa-save           (Button)
Times:            fas fa-times          (Cancel)
Check Circle:     fas fa-check-circle   (Success)
Exclamation:      fas fa-exclamation-circle (Error)
```

## Navigation Flow

### Access Points to Settings
1. **From Dashboard/Userpage:**
   - Look for "Account Settings" section
   - Click any button (Change Password, Privacy, Notifications, Preferences)
   - Links: `/account/settings`

2. **Direct URL:**
   - `/account/settings` (requires user session)
   - GET: Shows settings page
   - POST: Submits form data

### Navigation Within Settings Page
```
Landing (Grid View)
    ↓
Choose Option (Click Card)
    → Change Password → Form
    → Privacy → Form
    → Notifications → Form
    → Preferences → Form
    ↓
Submit Form or Click Cancel
    ↓
Return to Grid / Show Alert
```

### Returning to Other Pages
- **Home:** Click "emoti" logo or "Home" link → `/`
- **Dashboard:** Click "Dashboard" link → `/userpage`
- **Analytics:** Click "Analytics" link → `/analytics`
- **Logout:** Click "Logout" button → Session cleared, redirect to `/login_page`

## Responsive Behavior

### Desktop (1200px+)
- Grid layout: 2 columns × 2 rows
- Full form width: 50-80% container
- Buttons: Side by side

### Tablet (768px - 1199px)
- Grid layout: 2 columns × 2 rows
- Form width: 90% container
- Buttons: Side by side

### Mobile (< 768px)
- Grid layout: 1 column × 4 rows
- Form width: 100% container
- Buttons: Stacked vertically (full width)
- Navbar: Adjusted spacing

## Accessibility Features

- ✅ Semantic HTML (labels for inputs, button elements)
- ✅ ARIA labels on interactive elements
- ✅ Keyboard navigation (Tab through inputs)
- ✅ Focus states on inputs and buttons
- ✅ Color contrast meets WCAG AA standards
- ✅ Form validation messages
- ✅ Icon + text labels (not icons alone)

## States & Transitions

### Form States
- **Empty:** Initial/reset state
- **Focused:** Field has focus indicator
- **Filled:** User entered data
- **Validating:** Client-side validation in progress
- **Submitting:** POST request in progress (button disabled?)
- **Success:** Alert shown, form may reset
- **Error:** Alert shown, form retains data

### Page States
- **Grid View:** Initial load, all cards visible
- **Form View:** Single form displayed, grid hidden
- **Alert Active:** Toast notification visible, auto-hides
- **Content Transition:** Smooth scroll to top when showing form

### Visual Feedback
- **Button Hover:** Transform up 2px + shadow
- **Card Hover:** Border becomes accent color
- **Input Focus:** Border accent + subtle glow box-shadow
- **Toggle Hover:** Slight opacity change
- **Alert Slide:** Smooth slide-in from top animation

## Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Move between form fields |
| Shift+Tab | Move to previous field |
| Enter | Submit form (when on button or last field) |
| Escape | Could close form (implement? optional) |
| Space | Toggle checkbox/switch |

## Form Validation

### Change Password
- Current Password: Required (any length accepted)
- New Password: Required, minimum 8 characters
- Confirm Password: Required, must match New Password
- Validation: Client-side real-time, server-side verification

### Privacy Settings
- All toggles: Boolean (validated on server)
- Default: All checked (true)

### Notifications
- All toggles: Boolean (validated on server)  
- Default: All checked (true)

### Preferences
- Theme: Dropdown selection (dark/light/auto)
- Language: Dropdown selection (en/es/fr/de/ar)
- Auto-Save: Boolean toggle
- Animations: Boolean toggle
- Defaults: dark, en, checked, checked

## Error Messages

### Password Change Errors
- "Passwords do not match!" - Confirm password doesn't match new password
- "Password must be at least 8 characters long!" - New password too short
- "Current password is incorrect" - Wrong current password (server response)
- "An error occurred. Please try again." - Generic server error

### All Other Form Errors
- "An error occurred. Please try again." - Generic message
- Server returns specific error in response
- Form data is retained for user to fix

## Success Messages

All forms:
- "[Setting] updated successfully!" - Shown when POST succeeds
- Auto-hides after 4 seconds
- Form clears after success (passwords only)
- User remains on form or returns to grid

## Background & Philosophy

This implementation prioritizes:
1. **Security:** Password verification, bcrypt hashing, session validation
2. **Usability:** Clear form layout, helpful descriptions, immediate feedback
3. **Consistency:** Matches existing dark theme and design patterns
4. **Performance:** Minimal DOM operations, efficient database queries
5. **Maintainability:** Well-structured code, clear naming, comprehensive docs
