from google.adk.agents.llm_agent import Agent
from .pattern_detector_tool import PatternDetectorTool
from .deepfake_detector_tool import DeepfakeDetectorTool
from .clickbait_detector_tool import ClickbaitDetectorTool

root_agent = Agent(
    model='gemini-2.5-flash',
    name='misinformation_detection_agent',
    description='Multi-method misinformation detection agent that identifies fake news patterns, deepfakes, and clickbait.',
    instruction='Detect misinformation using pattern recognition, deepfake detection, and clickbait identification. Provide detailed analysis of manipulation techniques and content authenticity.',
    tools=[
        PatternDetectorTool(),
        DeepfakeDetectorTool(),
        ClickbaitDetectorTool()
    ],
)
