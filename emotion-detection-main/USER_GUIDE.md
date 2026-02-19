# 🎨 Modern Dark Theme - User Guide

## What's New

Your emotion detection app now features a professional **EmotiSense-style dark theme** with:
- ✨ Cyan/indigo gradients and glassmorphic effects
- 🎯 Real-time emotion tracking across all pages
- 📊 Live analytics dashboard with downloadable reports
- 💬 Fixed chat with emotion-aware AI responses
- 📱 Fully responsive mobile design

---

## 🚀 Quick Start

### 1. **Chat with Emotion Detection** 💬
Navigate to **Chat** → Type your message → Emotion detected automatically
- Messages display in real-time with emotion badges
- AI responds based on your emotional tone
- Emotions tracked to analytics

### 2. **Detect Emotions in Text** 📝
Navigate to **Text** → Paste text → Click "Detect Emotion"
- See emotion with confidence percentage
- View sentiment analysis (positive/negative/neutral)
- Check detection history
- Auto-tracked to analytics

### 3. **Analyze Faces in Images** 📸
Navigate to **Image** → Upload image → Click "Analyze Image"
- Detects multiple faces with emotions
- Shows confidence scores
- Full detection history with thumbnails
- Emotions tracked per face

### 4. **Frame-by-Frame Video Analysis** 🎬
Navigate to **Video** → Upload video → Click "Analyze Video"
- Analyzes every frame for emotion
- Shows emotion timeline
- Displays distribution charts
- Tracks dominant emotion

### 5. **Connect in Live Chat** 👥
Navigate to **Live Chat** → Type message → Press Enter
- Real-time global chat with other users
- All messages analyzed for emotion
- Online users counter
- Emotion badges on each message

### 6. **View Analytics Dashboard** 📈
Navigate to **Analytics** → See real-time data
- **Overview Cards**: Total interactions, dominant emotion, etc.
- **Emotion Charts**: Breakdown by detection source
- **Timeline**: Recent activity with timestamps (now displayed with AM/PM)
- **Download Report**: Export all data as JSON

---

## 🎨 Color Meanings

| Emotion | Emoji | Color | Meaning |
|---------|-------|-------|---------|
| Joy | 😊 | 🟡 Gold | Happy, positive |
| Sadness | 😢 | 🔵 Blue | Sad, down |
| Anger | 😠 | 🔴 Red | Angry, frustrated |
| Fear | 😨 | 🟣 Purple | Scared, anxious |
| Disgust | 🤢 | 🟢 Green | Disgusted, repulsed |
| Surprise | 😮 | 🟠 Orange | Surprised, shocked |
| Neutral | 😐 | ⚪ Gray | Neutral, calm |

---

## 📊 How Emotion Tracking Works

```
1. User detects emotion (text, image, video, or chat)
   ↓
2. ML model analyzes and returns emotion + confidence
   ↓
3. Emotion displayed in UI with color-coded badge
   ↓
4. Automatically tracked to database
   ↓
5. Analytics sum emotions by source
   ↓
6. Dashboard shows real-time emotion distribution
   ↓
7. Download report includes all tracked emotions
```

---

## 📥 Download Your Report

1. Go to **Analytics**
2. Select time period: All Time / Last 24 Hours / Last 7 Days / Last 30 Days or choose **Custom Range** to specify an exact start/end date and time.
3. Click **"Download Report"**
4. File saves as `emoti-analytics-{period}-{date}.json`

### Report Includes:
- Total interactions
- Emotion distribution from all sources
- Recent interactions with timestamps
- Global chat analytics
- Confidence scores for each emotion
- Source breakdown (text, image, video, chat)

---

## 🎯 Features Breakdown

### Chat Page
- [x] Dark theme with glassmorphic effects
- [x] Real-time message sending
- [x] Emotion detection on user message
- [x] Emotion-aware AI responses
- [x] Emotion badges on every message
- [x] Auto-scrolling message history
- [x] Responsive on mobile

### Text Detection Page
- [x] Large textarea for input
- [x] Emotion display with emoji
- [x] Confidence bar visualization
- [x] Sentiment analysis meter
- [x] Text intensity indicator
- [x] Detection history with timestamps
- [x] Copy-paste friendly

### Image Detection Page
- [x] Drag-and-drop upload area
- [x] Multi-face detection support
- [x] Emotion per face with confidence
- [x] Image preview in history
- [x] Supports JPEG, PNG, WebP

### Video Detection Page
- [x] Video player with controls
- [x] Frame-by-frame emotion analysis
- [x] Emotion statistics grid
- [x] Timeline visualization
- [x] Distribution charts
- [x] Metadata tracking

### Live Chat Page
- [x] Global chat room
- [x] Real-time message updates
- [x] Online users list
- [x] Emotion on every message
- [x] Message count tracking
- [x] User status indicators

### Analytics Dashboard
- [x] Live stat cards (4 metrics)
- [x] Emotion charts by detection type
- [x] Emotion spectrum progress bars
- [x] Recent activity timeline
- [x] Source breakdown (Text, Image, Video)
- [x] Period filters (day/week/month/all)
- [x] Download report button
- [x] Auto-refresh every 10 seconds

---

## 🔧 Technical Details

### Frontend
- **Framework**: Bootstrap 5.3
- **Charts**: Chart.js 4.4
- **Styling**: Custom CSS with CSS variables
- **Theme Colors**: 7 emotion colors + 3 accent colors

### Backend
- **Framework**: Flask
- **Database**: MongoDB
- **ML Models**: DeepFace, Transformers, Groq API
- **Authentication**: Session-based

### API Endpoints
```
POST /api/track-emotion              - Track emotion from any source
GET /api/emotions-summary            - Get emotion summary
GET /api/analytics-report            - Download report
POST /api/chat                       - Send chat message
POST /api/send-global-chat           - Send live chat message
GET /api/global-chat-history         - Get chat history
GET /api/global-chat-users           - Get online users
```

---

## 💡 Tips & Tricks

1. **Faster Emotion Detection**: Keep text between 50-200 characters for best results
2. **Better Face Detection**: Use well-lit images with clear facial views
3. **Video Analysis**: Shorter videos (under 5 minutes) process faster
4. **Report Export**: Download reports regularly to track patterns over time
5. **Mobile Usage**: All pages are touch-friendly on smartphones

---

## 🐛 Troubleshooting

### Chat messages not sending?
→ Refresh the page and try again. Check your internet connection.

### Emotion not detecting?
→ Try different text/image with clearer emotional content.

### Analytics not updating?
→ It auto-updates every 10 seconds. Manual refresh: Click the "Update" button.

### Download report not working?
→ Try smaller time period (day/week instead of all time).

---

## 📞 Support

For issues or feature requests, check:
1. Console error messages (F12 → Console tab)
2. Network requests (F12 → Network tab)
3. Database connection status in logs

---

## 🎓 Emotion Detection Technology

Your app uses:
- **Text**: Transformer-based emotion classifier (huggingface)
- **Faces**: DeepFace facial emotion detection
- **Responses**: Groq AI (llama-3.1-8b-instant)
- **Tracking**: Real-time MongoDB storage

---

**Status**: ✅ Active | **Theme**: Dark Mode | **Version**: 2.1

Enjoy analyzing emotions with **emoti**! 🎯
