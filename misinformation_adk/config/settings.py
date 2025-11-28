"""
Configuration settings for the misinformation detection system.
"""

# API Configuration
API_CONFIG = {
    "fact_check_api_key": "YOUR_API_KEY_HERE",  # e.g., ClaimBuster, Google Fact Check API
    "news_api_key": "YOUR_API_KEY_HERE",  # e.g., NewsAPI
    "nlp_api_key": "YOUR_API_KEY_HERE",  # e.g., for sentiment analysis
}

# Agent Ports (for future API deployment)
AGENT_PORTS = {
    "orchestrator": 8000,
    "fact_check": 8001,
    "source_credibility": 8002,
    "sentiment_analysis": 8003,
    "misinformation_detection": 8004,
}

# Model Configuration
MODEL_CONFIG = {
    "default_model": "gemini-2.5-flash",
    "temperature": 0.7,
    "max_tokens": 1000,
}

# Credibility Thresholds
CREDIBILITY_THRESHOLDS = {
    "high": 0.8,
    "medium": 0.5,
    "low": 0.3,
}
