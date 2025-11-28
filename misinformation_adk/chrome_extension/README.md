# Vishwas Netra - Chrome Extension

**विश्वास का नेत्र** (The Eye of Trust)

AI-powered fact-checking extension for Chrome that analyzes text, images, videos, and YouTube content.

## 🚀 Features

- **📝 Text Fact-Checking**: Analyze selected text or entire pages
- **🎨 Auto-Highlighting**: Automatically highlights suspicious claims on webpages
  - 🔴 **Red** = Likely false (>70% confidence)
  - 🟡 **Yellow** = Questionable/suspicious (40-70%)
  - 🟠 **Orange** = Unverified claim
  - 🟣 **Purple** = AI-generated content
  - Click highlighted text for detailed analysis!
- **🛡️ Elder Protection Mode**: Continuous monitoring with automatic highlighting
- **🎬 YouTube Integration**: Automatically transcribe and fact-check videos
- **🖼️ Image Analysis**: Detect deepfakes in images
- **🎥 Video Deepfake Detection**: Analyze video authenticity
- **🎵 Audio Deepfake Detection**: Detect voice cloning
- **⌨️ Keyboard Shortcuts**:
  - `Ctrl+Shift+F` - Fact-check & highlight current page
  - `Ctrl+Shift+C` - Fact-check selected text
- **🔗 Shareable Reports**: Get a unique link for every fact-check
- **⚡ Fast Mode**: Skips content type detection for instant results

## 📦 Installation

### Prerequisites

1. **API Server Running**: The extension requires the API server to be running
   ```bash
   cd "d:\mumbaihax try"
   pip install -r requirements-api.txt
   python api_server.py
   ```

2. **Install Extension in Chrome**:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" (top right)
   - Click "Load unpacked"
   - Select the `chrome_extension` folder
   - Extension icon should appear in toolbar

## 🎯 Usage

### Method 1: Extension Popup
1. Click the extension icon in toolbar
2. Enter text or paste a YouTube URL
3. Click appropriate button:
   - **Check Text** - Analyze typed/pasted content
   - **Check Selection** - Analyze selected text on page
   - **Check Page** - **Scans & highlights ALL suspicious claims on page!** 🎨
   - **Check Video** - Analyze YouTube video transcript

### Method 2: Elder Protection Mode (Auto-Highlighting)
1. Click extension icon → Click ⚙️ settings
2. Enable "Elder Protection Mode"
3. All webpages are automatically scanned
4. Suspicious claims highlighted in real-time:
   - **Red** = Likely false
   - **Yellow** = Questionable
   - **Orange** = Unverified
5. **Click any highlight** to see detailed fact-check!

### Method 3: Keyboard Shortcuts
- Press `Ctrl+Shift+F` - **Highlight all claims on current page**
- Press `Ctrl+Shift+C` - Fact-check selected text
- Results appear as page highlights + notification

### Method 4: Context Menu
- Right-click on selected text → "Fact-check [text]"
- Right-click on image → "Fact-check this image"
- Right-click on video → "Fact-check this video"

## 📊 Features

### Shareable Reports
Every fact-check generates a unique shareable link:
- Click "Copy" to copy the link
- Click "View" to open full report
- Share link with others - they see the same analysis

### YouTube Transcription
- Paste YouTube URL or use extension on YouTube page
- Automatically extracts video transcript
- Analyzes entire video content for misinformation

### Fast Processing
Extension tells the API what type of content it is:
- `text` - Text content
- `image` - Image file
- `video` - Video file
- `url` - YouTube URL

This skips the content intake stage for 2-3x faster results!

## 🔧 Configuration

Edit API endpoint if running server on different port:

**popup.js** (line 3):
```javascript
const API_BASE = 'http://localhost:8000';
```

**background.js** (line 110):
```javascript
const response = await fetch('http://localhost:8000/api/fact-check', {
```

## 📝 Report Format

Each report includes:
- **Verdict**: TRUE, FALSE, UNCERTAIN, PARTIALLY_TRUE, OUTDATED_INFO
- **Confidence Score**: 0-100%
- **Temporal Status**: CURRENT, OUTDATED, TIMELESS
- **Key Evidence**: Bullet points
- **Sources**: Referenced websites
- **Time Verification**: When events occurred
- **Warnings**: Red flags detected

## 🎨 Icons

To add custom icons, create these files in `icons/` folder:
- `icon16.png` - 16x16px
- `icon32.png` - 32x32px
- `icon48.png` - 48x48px
- `icon128.png` - 128x128px

Or use an online icon generator like:
- https://favicon.io/
- https://realfavicongenerator.net/

## 🐛 Troubleshooting

**Extension shows "Error" when fact-checking:**
- Make sure API server is running: `python api_server.py`
- Check console: `chrome://extensions/` → Click "Details" → "Inspect views: service worker"

**YouTube videos don't work:**
- Install YouTube Transcript API: `pip install youtube-transcript-api`
- Some videos don't have transcripts (live streams, music videos)

**Keyboard shortcuts don't work:**
- Go to `chrome://extensions/shortcuts`
- Configure custom shortcuts for this extension

## 🔒 Privacy

- Extension sends content to localhost API only
- No data sent to external servers
- Reports stored locally in `data/reports/` folder

## 📚 API Endpoints Used

- `POST /api/fact-check` - Submit content for analysis
- `GET /api/report/{id}` - Get JSON report
- `GET /report/{id}` - Get HTML report (shareable)

## 🛠️ Development

To modify the extension:
1. Edit files in `chrome_extension/` folder
2. Go to `chrome://extensions/`
3. Click "Reload" button for your extension
4. Changes take effect immediately

## 📄 Files

```
chrome_extension/
├── manifest.json        # Extension configuration
├── popup.html          # Extension popup UI
├── popup.js            # Popup logic
├── background.js       # Background service worker
├── content.js          # Content script for web pages
├── icons/              # Extension icons
└── README.md           # This file
```

## ⚡ Performance

- Text analysis: ~2-5 seconds
- YouTube videos: ~5-15 seconds (depending on length)
- Image analysis: ~3-7 seconds
- Fast mode (with content_type): 30-50% faster

## 🌟 Tips

1. **For best results**: Select clear, complete sentences
2. **YouTube**: Videos with closed captions work best
3. **Images**: Works best with clear, high-quality images
4. **Share reports**: Use shareable link to discuss findings

## 🔄 Updates

Check for updates:
```bash
cd "d:\mumbaihax try"
git pull  # If using git
```

Reload extension after code updates.
