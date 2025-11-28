from google.adk.agents.llm_agent import Agent
from .gemini_fact_checker_tool import GeminiFactCheckerTool
from .web_search_tool import WebSearchTool
from .google_news_tool import GoogleNewsTool
from .twitter_search_tool import TwitterSearchTool
from .claim_database_tool import ClaimDatabaseTool

root_agent = Agent(
    model='gemini-2.0-flash-exp',  # Latest Gemini model with web search
    name='fact_check_agent',
    description='Multi-source fact-checking agent with Google News integration for verified news sources.',
    instruction='Verify claims using multiple sources: Gemini AI analysis, Google News articles, web search results, and social media. Prioritize recent news articles from credible sources. Provide confidence scores and sources.',
    tools=[
        GeminiFactCheckerTool(),
        GoogleNewsTool(),
        WebSearchTool(),
        TwitterSearchTool(),
        ClaimDatabaseTool()
    ],
)
