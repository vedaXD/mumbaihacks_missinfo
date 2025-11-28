# Misinformation Detection ADK

> A multi-agent system for detecting and analyzing misinformation, built with Google ADK

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google ADK
- API keys (configure in `config/settings.py`)

### Installation

```bash
# Clone the repository
git clone https://github.com/vedaXD/mumbaihacks_missinfo.git
cd mumbaihacks_missinfo/misinformation_adk

# Install dependencies
pip install -r requirements.txt

# Configure your API keys
# Edit config/settings.py with your credentials
```

### Basic Usage

```python
from misinformation_adk.agents.orchestrator_agent import root_agent

# Analyze text content
response = root_agent.run(
    content="Your text or claim to analyze",
    content_type="text"
)

print(response)
```

## 🏗️ Architecture

This project uses a **pipeline-based multi-agent system** that processes content through specialized agents:

```
┌─────────────────────────────────────────────────────────┐
│                   Orchestrator Agent                    │
│            (Coordinates the entire pipeline)            │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌──────────────┐  ┌──────────────────┐
│  Fact Check   │  │    Source    │  │   Sentiment      │
│     Agent     │  │ Credibility  │  │    Analysis      │
│               │  │    Agent     │  │     Agent        │
└───────────────┘  └──────────────┘  └──────────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────────────────────────────────────────────┐
│         Misinformation Detection Agent                │
└───────────────────────────────────────────────────────┘
```

### Agents & Tools

| Agent | Purpose | Key Tools |
|-------|---------|-----------|
| **Orchestrator** | Coordinates pipeline execution | OrchestratorTool |
| **Fact Check** | Multi-source claim verification | Gemini AI, Web Search, Twitter Search, Claim Database |
| **Source Credibility** | Evaluates source reliability | Domain Reputation, NewsGuard, WHOIS |
| **Sentiment Analysis** | Detects bias & manipulation | Emotion Detection, Bias Detector, Manipulation Detector |
| **Misinformation Detection** | Pattern & deepfake detection | Pattern Detector, Deepfake Detector, Clickbait Detector |

## 📁 Project Structure

```
misinformation_adk/
├── agents/          # Agent implementations & specialized tools
├── config/          # Configuration and settings
├── data/            # Claims database and storage
├── tools/           # Standalone tools
└── utils/           # Helper functions
```

## 🔧 Configuration

Edit `config/settings.py` to add your API keys:

```python
# Add your API keys here
GOOGLE_API_KEY = "your-key-here"
NEWSGUARD_API_KEY = "your-key-here"
# ... other keys
```

## 📝 Examples

### Fact-Check a Claim
```python
from misinformation_adk.agents.fact_check_agent import root_agent

result = root_agent.run("The Earth is flat")
```

### Analyze Source Credibility
```python
from misinformation_adk.agents.source_credibility_agent import root_agent

result = root_agent.run("https://example-news-site.com")
```

### Detect Sentiment & Bias
```python
from misinformation_adk.agents.sentiment_analysis_agent import root_agent

result = root_agent.run("Your content text here")
```

## 🛣️ Roadmap

- [ ] Implement live API integrations
- [ ] Add ML-based pattern detection models
- [ ] Build web interface/dashboard
- [ ] Add comprehensive test suite
- [ ] Implement logging and monitoring
- [ ] Support multi-language detection
- [ ] Add real-time social media monitoring

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project was created for Mumbai Hacks.

## 🙏 Acknowledgments

Built with Google ADK for the Mumbai Hacks hackathon.
