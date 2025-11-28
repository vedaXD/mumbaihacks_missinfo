from google.adk.agents.llm_agent import Agent
from .orchestrator_tool import OrchestratorTool

# Import sub-agents
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Note: Sub-agents are called directly through tools, not as sub_agents in ADK
# The orchestrator tool handles all routing and coordination

root_agent = Agent(
    model='gemini-2.5-flash',
    name='orchestrator_agent',
    description='Root orchestrator that coordinates misinformation detection through specialized sub-agents.',
    instruction='''Process user submissions through a sequential pipeline:
    1. Content Intake: Analyze content type (text/media)
    2. Media Analysis: Check for deepfakes, perform OCR/transcription if needed
    3. Fact Checking: Verify claims using multi-source verification
    4. Source Credibility: Evaluate information source reliability
    5. Sentiment Analysis: Detect bias and emotional manipulation
    6. Knowledge: Educate user about findings and misinformation awareness
    
    Route intelligently based on content type and coordinate all agents to provide comprehensive analysis.''',
    tools=[OrchestratorTool()],
)
