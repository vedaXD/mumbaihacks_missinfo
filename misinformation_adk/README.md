# Misinformation Detection ADK Project

A multi-agent system built with Google ADK for detecting and analyzing misinformation using a pipeline approach.

## Project Structure

```
misinformation_adk/
├── agents/                               # Agent definitions and tools
│   ├── orchestrator_agent.py            # Main orchestrator
│   ├── orchestrator_tool.py             # Orchestration logic
│   │
│   ├── fact_check_agent.py              # Multi-source fact-checking
│   ├── gemini_fact_checker_tool.py      # Gemini AI verification
│   ├── web_search_tool.py               # Web search verification
│   ├── twitter_search_tool.py           # Social media consensus
│   ├── claim_database_tool.py           # Claim tracking & storage
│   │
│   ├── source_credibility_agent.py      # Source credibility analysis
│   ├── domain_reputation_tool.py        # Domain reputation check
│   ├── newsguard_tool.py                # NewsGuard ratings
│   ├── whois_tool.py                    # WHOIS lookup
│   │
│   ├── sentiment_analysis_agent.py      # Sentiment & bias detection
│   ├── emotion_detection_tool.py        # Emotion analysis
│   ├── bias_detector_tool.py            # Political bias detection
│   ├── manipulation_detector_tool.py    # Manipulation tactics
│   │
│   ├── misinformation_detection_agent.py # Pattern detection
│   ├── pattern_detector_tool.py         # Misinformation patterns
│   ├── deepfake_detector_tool.py        # Deepfake detection
│   └── clickbait_detector_tool.py       # Clickbait detection
│
├── tools/                                # Legacy tools (deprecated)
├── config/                               # Configuration files
│   └── settings.py
├── utils/                                # Utility functions
│   └── helpers.py
└── data/                                 # Data storage
    └── claims_db.json                   # Claims database
```

## Pipeline Architecture

The orchestrator processes submissions through a sequential pipeline:

1. **Content Intake** - Analyzes content type (text/media)
2. **Media Analysis** - Checks for deepfakes, performs OCR/transcription
3. **Fact Checking** - Multi-source verification (Gemini AI, web search, Twitter)
4. **Source Credibility** - Evaluates source reliability
5. **Sentiment Analysis** - Detects bias and emotional manipulation
6. **Knowledge** - Educates users about misinformation awareness

## Agents

### 1. Orchestrator Agent
Coordinates the entire misinformation detection pipeline. Routes content through sequential analysis stages and coordinates all sub-agents.

**Tool:** `OrchestratorTool` - Manages pipeline execution

### 2. Fact Check Agent (Multi-Source)
Verifies claims using multiple sources for comprehensive fact-checking.

**Tools:**
- `GeminiFactCheckerTool` - Gemini AI reasoning and analysis
- `WebSearchTool` - Web search across fact-checking sites
- `TwitterSearchTool` - Social media consensus and expert opinions
- `ClaimDatabaseTool` - Tracks claims for re-verification

### 3. Source Credibility Agent
Evaluates information source reliability using multiple metrics.

**Tools:**
- `DomainReputationTool` - Domain safety and reputation
- `NewsGuardTool` - NewsGuard credibility ratings
- `WhoisTool` - Domain registration information

### 4. Sentiment Analysis Agent
Analyzes content for bias, emotions, and manipulation tactics.

**Tools:**
- `EmotionDetectionTool` - Emotional language analysis
- `BiasDetectorTool` - Political bias and ideological slant
- `ManipulationDetectorTool` - Persuasion and manipulation tactics

### 5. Misinformation Detection Agent
Detects misinformation patterns, deepfakes, and clickbait.

**Tools:**
- `PatternDetectorTool` - Misinformation pattern recognition
- `DeepfakeDetectorTool` - AI-generated media detection
- `ClickbaitDetectorTool` - Clickbait headline detection

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API keys in `config/settings.py`

3. Import and use the orchestrator:
```python
from misinformation_adk.agents.orchestrator_agent import root_agent

# Process content through the pipeline
response = root_agent.run(
    content="Your text or media to analyze",
    content_type="text"  # or "image", "video", "audio"
)
```

4. Or use individual agents directly:
```python
from misinformation_adk.agents.fact_check_agent import root_agent as fact_checker

# Direct fact-checking
result = fact_checker.run("Claim to verify")
```

## TODO

- [ ] Implement actual fact-checking logic with APIs
- [ ] Add source credibility scoring algorithms
- [ ] Integrate sentiment analysis models
- [ ] Build misinformation detection ML models
- [ ] Add API endpoints for each agent
- [ ] Create comprehensive testing suite
- [ ] Add logging and monitoring

## Future Enhancements

You can expand this project by:
- Adding more specialized sub-agents
- Implementing advanced ML models
- Creating a web interface
- Adding real-time monitoring capabilities
- Integrating with social media APIs
