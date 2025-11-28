from google.adk.agents.llm_agent import Agent
from .domain_reputation_tool import DomainReputationTool
from .newsguard_tool import NewsGuardTool
from .whois_tool import WhoisTool

root_agent = Agent(
    model='gemini-2.5-flash',
    name='source_credibility_agent',
    description='Multi-source credibility evaluation agent that assesses information sources using domain reputation, NewsGuard ratings, and WHOIS data.',
    instruction='Evaluate source credibility using domain reputation databases, NewsGuard ratings, and WHOIS information. Provide comprehensive credibility scores with supporting evidence.',
    tools=[
        DomainReputationTool(),
        NewsGuardTool(),
        WhoisTool()
    ],
)
