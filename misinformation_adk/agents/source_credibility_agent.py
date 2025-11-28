from google.adk.agents.llm_agent import Agent
from ..tools.source_credibility_tool import SourceCredibilityTool

root_agent = Agent(
    model='gemini-2.5-flash',
    name='source_credibility_agent',
    description='An agent that evaluates the credibility and reliability of information sources.',
    instruction='Analyze the credibility of sources using the check_source_credibility tool. Provide ratings and insights on source trustworthiness.',
    tools=[SourceCredibilityTool()],
)
