"""
Utility functions for the misinformation detection system.
"""

import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_logger(name: str):
    """Get a logger instance for a module."""
    return logging.getLogger(name)

def format_response(agent_name: str, result: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Format agent response in a consistent structure."""
    response = {
        "agent": agent_name,
        "result": result,
    }
    if metadata:
        response["metadata"] = metadata
    return response

def validate_url(url: str) -> bool:
    """Validate if a string is a proper URL."""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None
