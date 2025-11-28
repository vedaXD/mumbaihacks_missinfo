# 🛡️ Misinformation Detection System

A comprehensive Google ADK-based multi-agent system for detecting and analyzing misinformation using AI, deepfake detection, and multi-source verification.

## 🎯 Features

- **🎬 Deepfake Detection**: Pre-trained Hugging Face models for images, videos, and audio
  - Image/Video: `prithivMLmods/deepfake-detector-model-v1`
  - Audio: `mo-thecreator/Deepfake-audio-detection`
- **✓ Multi-Source Fact-Checking**: Gemini AI with web grounding, web search, and Twitter consensus
- **⏰ Temporal Verification**: Timeline checking like X/Twitter's Grok (detects outdated news)
- **📝 OCR & Transcription**: EasyOCR for text extraction, Speech Recognition for audio
- **💾 Claim Database**: Store uncertain claims for periodic re-verification
- **📚 User Education**: Contextual advice on misinformation awareness
- **🔄 Sequential Pipeline**: Automated multi-stage analysis workflow

## 🏗️ System Architecture

```
ROOT ORCHESTRATOR (SequentialAgent)
│
├─→ 1. Content Intake Agent
│   └─→ Analyzes: Text, Image, Video, Audio
│
├─→ 2. Media Analysis Agent
│   ├─→ Image Deepfake Detection (ML)
│   ├─→ Video Deepfake Detection (ML)
│   ├─→ Audio Deepfake Detection (ML)
│   ├─→ OCR (Tesseract)
│   └─→ Transcription (Speech Recognition)
│
├─→ 3. Fact Check Agent
│   ├─→ Gemini AI with Web Grounding
│   ├─→ Web Search (Multi-source)
│   ├─→ Twitter Consensus Analysis
│   └─→ Claim Database Management
│
└─→ 4. Knowledge Agent
    └─→ Educational content & recommendations
```

## 📁 Project Structure

```
mumbaihax try/
├── orchestrator_agent/
│   ├── __init__.py
│   ├── agent.py                      # Sequential orchestrator
│   └── orchestrator_tool.py          # Pipeline coordinator
│
├── sub_agents/
│   ├── content_intake_agent/
│   │   ├── agent.py
│   │   └── content_analyzer_tool.py
│   │
│   ├── media_analysis_agent/
│   │   ├── agent.py
│   │   ├── image_deepfake_tool.py    # TensorFlow-based
│   │   ├── video_deepfake_tool.py    # Frame-by-frame analysis
│   │   ├── audio_deepfake_tool.py    # Acoustic analysis
│   │   ├── ocr_tool.py               # Tesseract OCR
│   │   └── transcription_tool.py     # Speech-to-text
│   │
│   ├── fact_check_agent/
│   │   ├── agent.py
│   │   ├── gemini_fact_checker_tool.py  # Gemini 2.0
│   │   ├── web_search_tool.py           # DuckDuckGo
│   │   ├── twitter_search_tool.py       # Twitter API v2
│   │   └── claim_database_tool.py       # JSON database
│   │
│   └── knowledge_agent/
│       ├── agent.py
│       └── education_tool.py         # Media literacy content
│
├── utils/
│   ├── __init__.py
│   └── pending_claims_checker.py     # Periodic re-verification
│
├── data/
│   └── claims_db.json                # Claims database (auto-created)
│
├── main.py                           # Interactive CLI
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🚀 Setup

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

**Additional Requirements:**
- **FFmpeg**: For audio processing (optional but recommended)

**Note:** EasyOCR and pre-trained models will be downloaded automatically on first use.

### 2. Configure API Keys

Copy `.env.example` to `.env` and add your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
GOOGLE_API_KEY=your_google_api_key_here
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
```

**Get API Keys:**
- **Google Gemini**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Twitter API**: [Twitter Developer Portal](https://developer.twitter.com/)

### 3. Pre-trained Models

The system uses pre-trained Hugging Face models that download automatically:

- **Image/Video Deepfake**: `prithivMLmods/deepfake-detector-model-v1`
- **Audio Deepfake**: `mo-thecreator/Deepfake-audio-detection`
- **OCR**: EasyOCR (English by default, multi-language supported)

Models are cached locally after first download (~500MB total).

## 💻 Usage

### Interactive Mode (Default)

```powershell
python main.py
```

**Examples:**
```
📝 Enter claim: "Breaking: Major earthquake hits California"
📝 Enter claim: file:C:\images\suspicious_post.jpg
```

### Batch Processing

Create a text file with claims (one per line):
```powershell
python main.py --batch claims.txt
```

### Periodic Claim Checking

Check pending claims once:
```powershell
python utils/pending_claims_checker.py
```

Run continuous monitoring:
```powershell
python utils/pending_claims_checker.py --continuous
```

## 📊 How It Works

### 1️⃣ Content Analysis
- Determines if input is text, image, video, or audio
- Routes to appropriate analysis pipeline

### 2️⃣ Media Verification
- **Images/Videos**: Deepfake detection + OCR text extraction
- **Audio**: Voice manipulation detection + transcription
- Combines media authenticity with textual claims

### 3️⃣ Fact Checking
- **Gemini AI**: Latest model (gemini-2.0-flash-exp) with web grounding
- **Temporal Verification**: Like X/Twitter's Grok - detects outdated news presented as current
- **Web Search**: Multi-source credibility analysis from authoritative sites
- **Twitter**: Social consensus and verified user opinions
- **Timeline Analysis**: Verifies dates, events, and temporal consistency
- **Database**: Stores uncertain claims for later verification

### 4️⃣ User Education
- Tailored advice based on analysis results
- Media literacy tips
- Specific guidance on deepfakes, fact-checking, etc.

## 🔧 Customization

### Add New Sub-Agent

```python
sub_agents/
└── your_agent/
    ├── __init__.py
    ├── agent.py
    └── your_tool.py
```

### Extend Orchestrator

Edit `orchestrator_agent/orchestrator_tool.py` to add new pipeline stages.

### Custom ML Models

Replace placeholder models in media analysis tools with your trained models.

## 📝 API Configuration

**Gemini Models Supported:**
- `gemini-2.0-flash-exp` (Fact-checking - latest with web search)
- `gemini-2.5-flash` (Other agents)

**Twitter API Features:**
- Recent search endpoint
- Verified user detection
- Sentiment analysis
- Consensus calculation

## 🎓 Educational Topics

The system provides guidance on:
- Deepfake identification
- Fact-checking best practices
- Media literacy
- Social media awareness
- Cognitive biases

## ⚠️ Important Notes

1. **API Keys Required**: Gemini and Twitter APIs need valid credentials
2. **Rate Limits**: Be mindful of API rate limits (especially Twitter)
3. **ML Models**: Deepfake detection requires pre-trained models (not included)
4. **Tesseract**: Must be installed separately for OCR functionality
5. **Database**: Claims stored locally in JSON (consider PostgreSQL for production)

## 🛠️ Troubleshooting

**Import Errors:**
```powershell
pip install --upgrade -r requirements.txt
```

**Model Download Issues:**
- Ensure stable internet connection for first-time model downloads
- Models cached in `~/.cache/huggingface/`
- For GPU acceleration, install CUDA-enabled PyTorch

**API Errors:**
- Verify API keys in `.env`
- Check rate limits
- Ensure network connectivity

## 📈 Future Enhancements

- [ ] REST API endpoint (Flask/FastAPI)
- [ ] PostgreSQL database integration
- [ ] User notification system (email/SMS)
- [ ] Web UI dashboard
- [ ] Advanced ML models (BERT, RoBERTa)
- [ ] Multi-language support
- [ ] Real-time monitoring
- [ ] Blockchain verification

## 📄 License

This project is for educational and research purposes.

## 🤝 Contributing

Contributions welcome! Please ensure all agents follow the established code structure.

---

**Built with Google ADK, Gemini AI, TensorFlow, and ❤️**
