from google.adk.agents.llm_agent import Agent
from .gemini_fact_checker_tool import GeminiFactCheckerTool
from .web_search_tool import WebSearchTool
from .twitter_search_tool import TwitterSearchTool
from .claim_database_tool import ClaimDatabaseTool

root_agent = Agent(
    model='gemini-2.0-flash-exp',  # Latest Gemini model with web search
    name='fact_check_agent',
    description='Multi-source fact-checking agent that verifies claims using Gemini AI, web search, and social media analysis.',
    instruction='Verify claims using multiple sources: Gemini AI analysis, web search results, and Twitter consensus. Store uncertain claims for periodic re-checking. Provide confidence scores and sources.',
    tools=[
        GeminiFactCheckerTool(),
        WebSearchTool(),
        TwitterSearchTool(),
        ClaimDatabaseTool()
    ],
)
