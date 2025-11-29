# Vishwas Netra 🛡️

**An ecosystem that Not just detects but PREVENTS misinformation**

> विश्वास का नेत्र - The Eye of Trust

---

## 🚀 Twitter Bot (Live & Deployed)

Our Twitter bot is actively monitoring and combating misinformation on X (Twitter) in real-time. Tag **@VishwasNetra** on suspicious tweets to get instant fact-checking!

---

## ✨ Features

- 🔍 **Multi-Modal Analysis** - Text, images, videos, and audio deepfake detection
- 🤖 **AI-Powered Detection** - Advanced pattern recognition and bias detection
- 📰 **Automated News Reels** - AI-generated video summaries from verified news sources
- 🌐 **Source Credibility Check** - Domain reputation and WHOIS verification
- 😊 **Emotion & Sentiment Analysis** - Detect emotional manipulation and clickbait
- 🎭 **Deepfake Detection** - Identify synthetic media across all formats
- 🔗 **Claim Database** - Cross-reference against known misinformation
- 👨‍👩‍👧 **Parent Protection Mode** - 24/7 monitoring for vulnerable users
- 🌍 **Chrome Extension** - Real-time protection while browsing
- 📊 **Comprehensive Reports** - Detailed analysis with confidence scores

---

## 🏗️ Architecture

Vishwas Netra consists of **3 main components**:

1. **orchestrator_agent** - Main misinformation detection engine
2. **orchestrator_agent_reel** - News reel generation backend (Flask API)
3. **reel-frontend** - Instagram-style news reel viewer (React)

---

## ⚡ Quick Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Cloud credentials (Vertex AI, Cloud Storage)
- API keys: NewsGuard, Google News

### 1️⃣ Main Detection Engine

```bash
cd misinformation_adk
pip install -r requirements.txt
python -m agents.orchestrator_agent
```

### 2️⃣ News Reel Backend

```bash
cd misinformation_adk/orchestrator_agent_reel
pip install -r requirements.txt
python api_server.py
```
✅ Backend runs on **http://localhost:5001**

### 3️⃣ News Reel Frontend

```bash
cd misinformation_adk/reel-frontend
npm install
npm run dev
```
✅ Frontend runs on **http://localhost:3000**

### 4️⃣ Chrome Extension (Optional)

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer Mode**
3. Click **Load unpacked**
4. Select folder: `misinformation_adk/chrome_extension`
5. Pin the extension to toolbar

---

## 📝 Configuration

### Google Cloud Setup
1. Create a Google Cloud project
2. Enable APIs: Vertex AI, Cloud Storage, Cloud TTS
3. Download service account JSON key
4. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
   ```

### API Keys
Add to `misinformation_adk/config/settings.py`:
- NewsGuard API key
- Google News RSS (free, no key needed)
- Twitter API credentials (for bot deployment)

---

## 🎯 Usage

### Via Chrome Extension
1. Click extension icon in toolbar
2. Choose tab: **Text**, **Image**, **Video**, or **Audio**
3. Paste content or upload file
4. Click **Analyze** for instant fact-check
5. Click **🎬 News Reels** for AI-generated news videos

### Via News Reels Website
1. Open http://localhost:3000
2. **News Reels Tab** - Auto-generated Indian news reels
3. **Custom Reel Tab** - Create your own video from text
4. Scroll vertically (Instagram-style) to view reels

### Via API
```bash
curl -X POST http://localhost:5001/api/fetch_news \
  -H "Content-Type: application/json" \
  -d '{"country": "in", "num_articles": 5}'
```

---

## 🛠️ Tech Stack

**AI/ML**: Google Vertex AI (Gemini 2.0, Imagen 3.0), Cloud TTS  
**Backend**: Python, Flask, CrewAI, LangChain  
**Frontend**: React, Vite, CSS3  
**Browser**: Chrome Extension (Manifest V3)  
**Video**: MoviePy, FFmpeg  
**Storage**: Google Cloud Storage  
**News**: Google News RSS API  

---

## 📂 Project Structure

```
misinformation_adk/
├── agents/                    # AI agents (fact-check, sentiment, credibility)
├── orchestrator_agent_reel/   # News reel generation backend
│   ├── api_server.py         # Flask API (port 5001)
│   └── sub_agents/           # Script, image, audio, video agents
├── reel-frontend/            # React frontend (port 3000)
│   ├── src/App.jsx          # Main Instagram-style UI
│   └── vite.config.js       # Dev server config
├── chrome_extension/         # Browser extension
│   ├── popup.html           # Extension UI
│   ├── popup.js            # Extension logic
│   └── manifest.json       # Extension config
├── config/                  # Settings and configurations
└── data/                   # Claims database
```

---

## 🎬 Branding

All generated content includes **"Vishwas Netra"** watermark:
- Videos: Top-right text overlay
- Images: Embedded watermark text
- Website: Header branding

---

## 🐛 Troubleshooting

**Backend not starting?**
- Check Python dependencies: `pip install -r requirements.txt`
- Verify Google Cloud credentials are set

**Frontend shows errors?**
- Ensure backend is running on port 5001
- Check Node modules: `npm install`

**Extension not loading?**
- Enable Developer Mode in `chrome://extensions/`
- Click reload button on extension card

**Images/Videos failing?**
- System uses fallback images automatically
- Check Google Cloud quota (Imagen, TTS APIs)

---

## 👥 Team

Built with ❤️ for combating misinformation and protecting vulnerable users online.

---

## 📜 License

This project is part of Mumbai Hacks hackathon submission.

---

**Stay Safe. Stay Informed. Stay Vishwas Netra. 🛡️**
