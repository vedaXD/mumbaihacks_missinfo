from google.adk.agents.llm_agent import Agent
from .education_tool import EducationTool

root_agent = Agent(
    model='gemini-2.5-flash',
    name='knowledge_agent',
    description='Educates users about misinformation patterns, deepfakes, and critical thinking strategies.',
    instruction='Provide educational content about how misinformation spreads, how to identify it, and best practices for media literacy. Tailor explanations based on the specific case.',
    tools=[EducationTool()],
)
