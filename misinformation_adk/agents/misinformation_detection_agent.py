from google.adk.agents.llm_agent import Agent
from ..tools.misinformation_detection_tool import MisinformationDetectionTool

root_agent = Agent(
    model='gemini-2.5-flash',
    name='misinformation_detection_agent',
    description='An agent that detects misinformation, fake news, and misleading content.',
    instruction='Detect misinformation patterns using the detect_misinformation tool. Identify fake news, deepfakes, manipulated media, and misleading narratives.',
    tools=[MisinformationDetectionTool()],
)
