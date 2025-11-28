from google.adk.agents.llm_agent import Agent
from ..tools.sentiment_analysis_tool import SentimentAnalysisTool

root_agent = Agent(
    model='gemini-2.5-flash',
    name='sentiment_analysis_agent',
    description='An agent that analyzes text for sentiment, bias, and potential emotional manipulation.',
    instruction='Analyze text sentiment and bias using the analyze_sentiment tool. Identify emotional language, political bias, and manipulative content.',
    tools=[SentimentAnalysisTool()],
)
