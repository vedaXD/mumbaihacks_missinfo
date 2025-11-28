from google.adk.agents.llm_agent import Agent
from .emotion_detection_tool import EmotionDetectionTool
from .bias_detector_tool import BiasDetectorTool
from .manipulation_detector_tool import ManipulationDetectorTool

root_agent = Agent(
    model='gemini-2.5-flash',
    name='sentiment_analysis_agent',
    description='Multi-dimensional sentiment and bias analysis agent that detects emotions, political bias, and manipulation tactics.',
    instruction='Analyze content for emotional manipulation, political bias, and persuasion techniques. Provide detailed breakdown of sentiment, bias direction, and manipulation tactics used.',
    tools=[
        EmotionDetectionTool(),
        BiasDetectorTool(),
        ManipulationDetectorTool()
    ],
)
