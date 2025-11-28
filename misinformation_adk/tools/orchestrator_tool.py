import requests
from google.adk.tools.base_tool import BaseTool

class OrchestratorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="route_misinformation_request",
            description="Routes user requests to the appropriate misinformation detection agent based on the query type and returns the response."
        )

    def run(self, query: str) -> str:
        """
        Routes requests to appropriate agents based on content analysis.
        Supports: fact-checking, source verification, content analysis, social media monitoring
        """
        query_lower = query.lower()
        
        # Fact-checking agent routing
        if any(word in query_lower for word in [
            "fact", "check", "verify", "true", "false", "claim", "statement", "accurate"
        ]):
            return self._route_to_agent("fact_checking", query, 8002)
            
        # Source verification agent routing  
        elif any(word in query_lower for word in [
            "source", "origin", "website", "author", "credible", "reliable", "trustworthy"
        ]):
            return self._route_to_agent("source_verification", query, 8003)
            
        # Content analysis agent routing
        elif any(word in query_lower for word in [
            "analyze", "content", "text", "article", "post", "sentiment", "bias"
        ]):
            return self._route_to_agent("content_analysis", query, 8004)
            
        # Social media monitoring agent routing
        elif any(word in query_lower for word in [
            "social", "twitter", "facebook", "instagram", "viral", "trending", "spread"
        ]):
            return self._route_to_agent("social_media", query, 8005)
            
        # Image/video verification agent routing
        elif any(word in query_lower for word in [
            "image", "photo", "video", "deepfake", "manipulated", "edited", "visual"
        ]):
            return self._route_to_agent("media_verification", query, 8006)
            
        else:
            return "I can help you with:\n" \
                   "• Fact-checking claims and statements\n" \
                   "• Verifying sources and credibility\n" \
                   "• Analyzing content for bias or misinformation\n" \
                   "• Monitoring social media trends\n" \
                   "• Verifying images and videos\n" \
                   "Please specify what type of misinformation analysis you need."

    def _route_to_agent(self, agent_name: str, query: str, port: int) -> str:
        """Helper method to route requests to specific agents"""
        try:
            url = f"http://127.0.0.1:{port}/agent/ask"
            payload = {"query": query}
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json().get("response", f"No response from {agent_name} agent.")
                return f"[{agent_name.replace('_', ' ').title()} Agent]: {result}"
            else:
                return f"Error connecting to {agent_name} agent (HTTP {response.status_code})"
                
        except requests.exceptions.Timeout:
            return f"{agent_name.replace('_', ' ').title()} agent is currently unavailable (timeout)"
        except requests.exceptions.ConnectionError:
            return f"{agent_name.replace('_', ' ').title()} agent is currently offline"
        except Exception as e:
            return f"Error communicating with {agent_name} agent: {str(e)}"