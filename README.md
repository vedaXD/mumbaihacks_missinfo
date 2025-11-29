# 🛡️ Vishwas Netra

### **An Agentic AI Ecosystem that Not just Detects but PREVENTS Misinformation**

> विश्वास का नेत्र - The Eye of Trust  
> *Protecting vulnerable users, empowering informed decisions*

---

## 🌟 Why Vishwas Netra?

In an era of deepfakes, AI-generated content, and viral misinformation, **Vishwas Netra** stands as a guardian for those who need it most - **elderly citizens, parents, and everyday users** who can fall victim to online frauds, scams, and fake news.

### 🎯 Our Mission
- **Protect Elders** from financial frauds, fake news, and AI-generated scams
- **Real-time Alerts** when viewing AI content, manipulated media, or suspicious claims
- **24/7 Monitoring** through Parent/Elderly Protection Mode
- **Instant Notifications** about deepfakes, emotional manipulation, and clickbait
- **Prevent harm** before it happens, not just detect after the fact

---

## 🤖 Live Telegram Bot (Deployed!)

Our intelligent bot is **actively fighting misinformation 24/7** on Telegram!

**👉 Start chatting: [@VishwasNetra_bot](https://t.me/VishwasNetra_bot)**

Send any suspicious message, image, video, or link to get instant AI-powered fact-checking and credibility analysis!

---

## 🧠 Agentic AI Architecture

Vishwas Netra is built on **CrewAI** - a powerful multi-agent system where specialized AI agents collaborate to combat misinformation:

### 🎭 Our AI Agents Team:

1. **Orchestrator Agent** 🎯 - Coordinates all specialized agents
2. **Fact-Check Agent** ✅ - Verifies claims against trusted sources
3. **Sentiment Analysis Agent** 😊 - Detects emotional manipulation
4. **Source Credibility Agent** 🔍 - Validates domain reputation
5. **Bias Detector Agent** ⚖️ - Identifies political/ideological bias
6. **Deepfake Detector Agent** 🎭 - Analyzes synthetic media
7. **Emotion Detection Agent** ❤️ - Spots psychological manipulation
8. **Clickbait Detector Agent** 🎣 - Flags sensationalist content
9. **Pattern Detector Agent** 📊 - Identifies misinformation patterns
10. **News Fetcher Agent** 📰 - Curates verified news sources

Each agent specializes in one aspect, working together to provide **comprehensive protection**.

---

## 🚨 Elder & Parent Protection Features

### **24/7 Guardian Mode**
- ⚡ **Real-time Monitoring** - Scans web pages automatically as users browse
- 🔔 **Instant Notifications** - Alerts when AI content or suspicious claims detected
- 🛡️ **Fraud Prevention** - Blocks access to known scam websites
- 📊 **Confidence Scores** - Shows how likely content is fake/manipulated
- 📈 **Activity Reports** - Daily summaries of protected browsing sessions
- 👨‍👩‍👧 **Family Dashboard** - Parents can monitor elderly relatives' online safety

### **What We Protect Against:**
- 💰 Financial fraud schemes and fake investment opportunities
- 🎭 AI-generated deepfake videos impersonating officials/celebrities
- 📧 Phishing attempts and fake emergency messages
- 🗞️ Viral fake news targeting emotional responses
- 🎤 Voice cloning scams (synthetic audio detection)
- 🖼️ Manipulated images spreading false narratives

---

## ✨ Key Features

- 🔍 **Multi-Modal Analysis** - Text, images, videos, and audio deepfake detection
- 🤖 **AI Content Detection** - Identifies Gemini, GPT, and synthetic media
- 📰 **Automated News Reels** - AI-generated video summaries from verified sources
- 🌐 **Source Credibility Check** - Domain reputation, WHOIS, and NewsGuard validation
- 😊 **Emotion & Sentiment Analysis** - Detect emotional manipulation tactics
- 🎭 **Advanced Deepfake Detection** - Visual, audio, and video synthesis detection
- 🔗 **Claim Database** - Cross-reference against known misinformation
- 👨‍👩‍👧 **Parent Protection Mode** - 24/7 monitoring with real-time alerts
- 🌍 **Chrome Extension** - Seamless protection while browsing
- 📊 **Detailed Reports** - Comprehensive analysis with confidence scores
- 🎬 **News Reel Generator** - Instagram-style scrollable verified news videos
- ✂️ **Screenshot Analysis** - Snipping tool to check any screen content

---

## 🏗️ System Architecture

Vishwas Netra is an **agentic multi-server ecosystem** with 3 core components working in harmony:

### **1. Orchestrator Agent** 🎯
Main AI detection engine powered by **CrewAI** - coordinates 10+ specialized agents for comprehensive misinformation analysis.

### **2. Orchestrator Agent Reel** 📰
News reel generation backend (Flask API) - fetches verified news, generates AI summaries, creates images, and composes videos with voiceover.

### **3. Reel Frontend** 🎬
Instagram-style news viewer (React) - smooth scrolling interface with auto-play videos and "Vishwas Netra" branding.

---

## ⚡ Quick Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Cloud credentials (Vertex AI, Cloud Storage)
- API keys: NewsGuard, Google News

---

### 🚀 **Step 1: Main Detection Engine (Orchestrator Agent)**

```bash
cd misinformation_adk
pip install -r requirements.txt
python -m agents.orchestrator_agent
```

✅ **This starts the core agentic AI system**

---

### 🎬 **Step 2: News Reel Backend**

```bash
cd misinformation_adk/orchestrator_agent_reel
pip install -r requirements.txt
python api_server.py
```

✅ Backend runs on **http://localhost:5001**

---

### 🌐 **Step 3: News Reel Frontend**

```bash
cd misinformation_adk/reel-frontend
npm install
npm run dev
```

✅ Frontend runs on **http://localhost:3000**

---

### 🧩 **Step 4: Chrome Extension (Optional but Recommended)**

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer Mode** (toggle in top-right)
3. Click **Load unpacked**
4. Select folder: `misinformation_adk/chrome_extension`
5. Pin the extension to toolbar (🧩 icon → 📌)

**Now you have 24/7 protection while browsing!**

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

## 🎯 How to Use

### 🌐 **Via Chrome Extension (Recommended for Elders)**

**Protection happens automatically while browsing!**

1. Click extension icon in toolbar
2. **Parent Protection Mode** - Toggle ON for 24/7 monitoring
3. Choose analysis tab:
   - **Text Tab**: Paste news/messages → Analyze
   - **Image Tab**: Screenshot or upload → Detect manipulation
   - **Video Tab**: Upload suspicious videos → Deepfake check
   - **Audio Tab**: Check voice messages → Synthetic audio detection
4. Click **🎬 News Reels** for verified news videos

### 📱 **Via Telegram Bot**

1. Open Telegram and search **@VishwasNetra_bot**
2. Send any suspicious content (text, image, video, link)
3. Get instant AI-powered analysis with confidence scores

### 🎬 **Via News Reels Website**

1. Open http://localhost:3000
2. **News Reels Tab**: Auto-generated Indian news (verified sources)
3. **Custom Reel Tab**: Create videos from your own text
4. Scroll vertically (Instagram-style) with auto-play

### 🔧 **Via API**

```bash
# Fetch verified news
curl -X POST http://localhost:5001/api/fetch_news \
  -H "Content-Type: application/json" \
  -d '{"country": "in", "num_articles": 5}'

# Generate news reels
curl -X POST http://localhost:5001/api/auto_generate_news_reels \
  -H "Content-Type: application/json" \
  -d '{"country": "in", "num_reels": 3}'
```

---

## 🛠️ Tech Stack

### **AI/ML & Agents**
- **CrewAI** - Multi-agent orchestration framework
- **Google Vertex AI** - Gemini 2.0 Flash, Imagen 3.0
- **LangChain** - Agent tooling and chains
- **Cloud TTS** - Natural voice synthesis

### **Backend**
- **Python 3.8+** - Core language
- **Flask** - API server
- **MoviePy** - Video composition
- **Pillow** - Image processing

### **Frontend**
- **React 18** - UI framework
- **Vite** - Build tool
- **CSS3** - Styling with scroll-snap

### **Browser Extension**
- **Chrome Manifest V3** - Latest extension API
- **Content Scripts** - Real-time monitoring
- **Service Worker** - Background processing

### **Infrastructure**
- **Google Cloud Storage** - Media storage
- **Google News RSS** - News aggregation
- **NewsGuard API** - Domain credibility

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
- Verify Google Cloud credentials: `echo $GOOGLE_APPLICATION_CREDENTIALS`
- Ensure all API keys are configured in `config/settings.py`

**Frontend shows errors?**
- Ensure backend is running on port 5001 first
- Clear cache: `rm -rf node_modules && npm install`
- Check proxy config in `vite.config.js`

**Extension not loading?**
- Enable Developer Mode in `chrome://extensions/`
- Click reload (🔄) button on extension card
- Check browser console (F12) for errors

**Images/Videos failing to generate?**
- System uses **5 fallback images** automatically
- Check Google Cloud quota (Imagen API limit)
- Rate limiting: 3-second delay between requests

**Telegram bot not responding?**
- Verify bot is running: Check deployment logs
- Test with simple text message first
- Ensure bot has proper permissions

---

## 🎬 Branding

All generated content proudly displays **"Vishwas Netra"** watermark:
- ✅ Videos: Top-right text overlay with stroke effect
- ✅ Images: Embedded watermark on all AI-generated visuals
- ✅ Fallback Images: Professional gradients with branding
- ✅ Website: Header with full branding

This ensures all our verified content is easily identifiable and trustworthy.

---

## 📊 What Makes Us Different?

### **Traditional Fact-Checkers:**
❌ Detect after misinformation spreads  
❌ Manual, slow verification process  
❌ Limited to text-based claims  
❌ No real-time protection  

### **Vishwas Netra (Agentic AI):**
✅ **Prevents** exposure before viewing  
✅ **Real-time** AI-powered analysis  
✅ **Multi-modal** (text, image, video, audio)  
✅ **24/7 monitoring** for vulnerable users  
✅ **10+ specialized agents** working together  
✅ **Instant notifications** on suspicious content  
✅ **Telegram bot** for accessibility  
✅ **Browser integration** for seamless protection  

---

## 👨‍👩‍👧 Real-World Impact

**For Elderly Users:**
- 🛡️ Prevented from clicking fraudulent investment schemes
- 📱 Alerted about deepfake videos of government officials
- 💰 Protected from WhatsApp/Telegram financial scams
- 📧 Warned about phishing emails before opening

**For Parents:**
- 👶 Monitor children's exposure to misinformation
- 🎮 Identify fake viral challenges and dangerous trends
- 📚 Verify educational content authenticity
- 🔒 Safe browsing with automatic alerts

**For Everyone:**
- ✅ Verify news before sharing
- 🎭 Identify AI-generated content
- 🌐 Check source credibility instantly
- 📰 Access verified news reels daily

---

## 👥 Team & Contribution

Built with ❤️ by passionate developers committed to fighting misinformation and protecting vulnerable internet users.

**Mumbai Hacks Hackathon Submission**

### Want to Contribute?
- 🐛 Report bugs via GitHub Issues
- 💡 Suggest features and improvements
- 🔧 Submit pull requests
- 📖 Improve documentation

---

## 📜 License

This project is part of Mumbai Hacks hackathon submission.

---

<div align="center">

### **🛡️ Stay Safe. Stay Informed. Stay Vishwas Netra. 🛡️**

**विश्वास का नेत्र - Your Guardian Against Misinformation**

---

**[Download Extension](#) • [Try Telegram Bot](https://t.me/VishwasNetra_bot) • [View Demo](#) • [Documentation](#)**

</div>

