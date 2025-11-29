"""
Sub-agents for the orchestrator
"""

from .script_generator_agent import ScriptGeneratorAgent
from .image_generator_agent import ImageGeneratorAgent
from .video_composer_agent import VideoComposerAgent
from .news_fetcher_agent import NewsFetcherAgent

__all__ = ['ScriptGeneratorAgent', 'ImageGeneratorAgent', 'VideoComposerAgent', 'NewsFetcherAgent']
