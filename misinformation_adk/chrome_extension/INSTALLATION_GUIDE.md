# Vishwas Netra Chrome Extension - Installation & Usage Guide

## Installation Steps

### 1. Load Extension in Chrome

1. **Open Chrome Extensions Page**
   - Open Google Chrome
   - Navigate to `chrome://extensions/`
   - OR click the three dots menu (⋮) → More Tools → Extensions

2. **Enable Developer Mode**
   - Toggle the **Developer mode** switch in the top-right corner to ON

3. **Load the Extension**
   - Click **"Load unpacked"** button
   - Navigate to: `d:\misinfo final repo\mumbaihacks_missinfo\misinformation_adk\chrome_extension`
   - Select the `chrome_extension` folder and click **"Select Folder"**

4. **Pin the Extension** (Optional but Recommended)
   - Click the puzzle piece icon 🧩 in Chrome toolbar
   - Find "Vishwas Netra" in the list
   - Click the pin 📌 icon to keep it visible in the toolbar

### 2. Start Required Servers

The extension needs both backend and frontend servers running:

#### Start Backend Server (Flask API)
```powershell
cd "d:\misinfo final repo\mumbaihacks_missinfo\misinformation_adk\orchestrator_agent_reel"
python api_server.py
```
✅ Backend should run on: `http://localhost:5001`

#### Start Frontend Server (React/Vite)
```powershell
cd "d:\misinfo final repo\mumbaihacks_missinfo\misinformation_adk\reel-frontend"
npm run dev
```
✅ Frontend should run on: `http://localhost:3000` (or 3001/3002)

---

## How to Use the Extension

### Main Features

#### 1. **Text Analysis Tab** 📝
- **Paste Text**: Copy any news article or social media post, paste it in the text box
- **Analyze**: Click "Analyze Text" to check for:
  - Misinformation detection
  - Sentiment analysis (positive/negative/neutral)
  - Bias detection
  - Emotional manipulation
  - Clickbait detection
  
- **News Reels Generator**: Click "🎬 News Reels Generator" to open the automated news reel website

#### 2. **Image Analysis Tab** 🖼️
- **Capture Screenshot**: Click "✂️ Capture Screenshot" to use the snipping tool
  - **Interactive Selection**: Click and drag to select any area of the screen
  - **Visual Feedback**: See your selection with a blue dashed border
  - **Cancel Anytime**: Press ESC to cancel the selection
  - Automatically captures only the selected portion
  - Works just like Windows Snipping Tool!
  
- **Upload Image**: Click "📁 Upload Image" to upload from your computer
  - Or drag-and-drop an image file
  
- **Analyze**: Automatically checks for:
  - Deepfake detection
  - Image manipulation
  - Context verification
  
- **News Reels**: Click "🎬 Open News Reels" to access the news reel generator

#### 3. **Video Analysis Tab** 🎥
- **Paste Video URL**: Enter YouTube, Twitter, or other video URLs
- **Analyze**: Detects:
  - Video manipulation
  - Deepfake videos
  - Audio-visual inconsistencies
  
- **News Reels**: Click "🎬 Open News Reels" to create video reels from news

#### 4. **Audio Analysis Tab** 🎵
- **Upload Audio**: Upload MP3, WAV, or other audio files
- **Analyze**: Checks for:
  - Voice cloning/deepfake audio
  - Audio manipulation
  - Synthetic speech detection
  
- **News Reels**: Click "🎬 Open News Reels" to generate audio-based news content

---

## News Reels Generator Feature

### What It Does
Automatically fetches trending Indian news, generates AI summaries, creates images, and composes Instagram-style video reels with "Vishwas Netra" branding.

### How to Use It

1. **Open News Reels**
   - Click any "🎬 News Reels" button in the extension (available in all 4 tabs)
   - This opens `http://localhost:3000` in a new tab

2. **View News Reels**
   - **News Reels Tab**: Auto-generated reels from Google News (India)
     - Scroll vertically (Instagram-style) to view different news reels
     - Videos auto-play as you scroll
     - Each reel has 8 scenes with AI-generated images and voiceover
   
   - **Custom Reel Tab**: Create custom reels
     - Enter your own text
     - Click "Generate Reel" to create a custom video

### Features
- ✅ 8-scene video reels with AI narration
- ✅ AI-generated images with "Vishwas Netra" watermark
- ✅ Automatic fallback images if generation fails
- ✅ Instagram-style scrollable interface
- ✅ Auto-play videos on scroll
- ✅ Daily Indian news from Google News RSS

---

## Troubleshooting

### Extension Not Loading?
- ✅ Make sure Developer Mode is enabled in `chrome://extensions/`
- ✅ Check that you selected the correct folder (`chrome_extension`)
- ✅ Click "Reload" button (🔄) on the extension card if you make changes

### News Reels Not Opening?
- ✅ Ensure both servers are running:
  - Backend: `http://localhost:5001` (check terminal for "Running on http://127.0.0.1:5001")
  - Frontend: `http://localhost:3000` (check terminal for "Local: http://localhost:3000/")
- ✅ If frontend is on a different port (3001/3002), update `popup.js` line with correct port

### Analysis Features Not Working?
- ✅ Backend server must be running (`python api_server.py`)
- ✅ Check Chrome console for errors (F12 → Console)
- ✅ Verify you have required API keys configured (Google Cloud, NewsGuard, etc.)

### Videos Not Generating?
- ✅ Check Google Cloud quota (Imagen, TTS APIs)
- ✅ Wait for rate limiting (3 seconds between image generations)
- ✅ Fallback images will be used if generation fails

---

## Keyboard Shortcuts (Extension Popup)

- **Alt + 1**: Switch to Text Analysis tab
- **Alt + 2**: Switch to Image Analysis tab
- **Alt + 3**: Switch to Video Analysis tab
- **Alt + 4**: Switch to Audio Analysis tab

---

## Configuration

### Update News Country
Edit `orchestrator_agent_reel/api_server.py`:
```python
country = request.json.get('country', 'in')  # Change 'in' to your country code
```

### Update Number of Scenes
Edit `orchestrator_agent_reel/api_server.py`:
```python
num_scenes = request.json.get('num_scenes', 8)  # Change 8 to desired number
```

### Change Frontend Port in Extension
Edit `chrome_extension/popup.js` (if frontend runs on different port):
```javascript
chrome.tabs.create({ url: 'http://localhost:3001' });  // Update port number
```

---

## Support & Credits

**Vishwas Netra** - AI-Powered Misinformation Detection & News Reel Generator

For issues or questions, check the project documentation or contact the development team.
