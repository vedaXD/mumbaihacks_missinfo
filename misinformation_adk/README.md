# Misinformation Detection ADK Project

A multi-agent system built with Google ADK for detecting and analyzing misinformation.

## Project Structure

```
misinformation_adk/
├── agents/                      # Agent definitions
│   ├── orchestrator_agent.py   # Main orchestrator that routes requests
│   ├── fact_check_agent.py     # Fact-checking agent
│   ├── source_credibility_agent.py  # Source credibility analysis
│   ├── sentiment_analysis_agent.py  # Sentiment and bias detection
│   └── misinformation_detection_agent.py  # Misinformation pattern detection
├── tools/                       # Agent tools
│   ├── fact_check_tool.py
│   ├── source_credibility_tool.py
│   ├── sentiment_analysis_tool.py
│   └── misinformation_detection_tool.py
├── config/                      # Configuration files
│   └── settings.py
└── utils/                       # Utility functions
    └── helpers.py
```

## Agents

### 1. Orchestrator Agent
Routes user queries to the appropriate sub-agent based on the request type:
- Fact-checking
- Source credibility analysis
- Sentiment/bias analysis
- Misinformation detection

### 2. Fact Check Agent
Verifies claims and checks facts against reliable sources.

### 3. Source Credibility Agent
Evaluates the credibility and reliability of information sources.

### 4. Sentiment Analysis Agent
Analyzes text for sentiment, bias, and potential emotional manipulation.

### 5. Misinformation Detection Agent
Detects misinformation patterns, fake news, and misleading content.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API keys in `config/settings.py`

3. Import and use agents:
```python
from misinformation_adk.agents.orchestrator_agent import root_agent

# Use the orchestrator to route queries
response = root_agent.run("Check if this claim is true: ...")
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
