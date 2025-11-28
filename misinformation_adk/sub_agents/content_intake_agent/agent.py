from google.adk.agents.llm_agent import Agent
from .content_analyzer_tool import ContentAnalyzerTool

root_agent = Agent(
    model='gemini-2.5-flash',
    name='content_intake_agent',
    description='Analyzes incoming content and determines its type (text, image, video, audio, or mixed media).',
    instruction='Analyze the input content and classify it into appropriate categories. Route media content to deepfake detection and text content to claim extraction.',
    tools=[ContentAnalyzerTool()],
)
