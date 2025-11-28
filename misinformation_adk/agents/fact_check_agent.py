from google.adk.agents.llm_agent import Agent
from ..tools.fact_check_tool import FactCheckTool

root_agent = Agent(
    model='gemini-2.5-flash',
    name='fact_check_agent',
    description='A fact-checking agent that verifies claims and statements against reliable sources.',
    instruction='Verify the accuracy of user claims using the fact_check tool. Provide detailed analysis of whether claims are true, false, or partially true.',
    tools=[FactCheckTool()],
)
