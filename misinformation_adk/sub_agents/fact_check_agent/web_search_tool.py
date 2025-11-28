from google.adk.tools.base_tool import BaseTool
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

class WebSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Searches the web for real-time information to verify claims."
        )
    
    def run(self, query: str, num_results: int = 5) -> dict:
        """
        Searches the web for information related to a claim.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            Dictionary with search results and analysis
        """
        try:
            # Use DuckDuckGo API (no API key required)
            search_results = self._duckduckgo_search(query, num_results)
            
            # Analyze credibility of sources
            credible_sources = self._analyze_source_credibility(search_results)
            
            # Extract common facts
            consensus = self._extract_consensus(search_results)
            
            return {
                "query": query,
                "results": search_results,
                "credible_sources": credible_sources,
                "consensus": consensus,
                "total_results": len(search_results)
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "query": query,
                "results": [],
                "total_results": 0
            }
    
    def _duckduckgo_search(self, query: str, num_results: int) -> list:
        """Perform DuckDuckGo search using official library with retry logic."""
        try:
            # Try new library name first
            try:
                from ddgs import DDGS
            except ImportError:
                # Fall back to old name
                from duckduckgo_search import DDGS
            
            results = []
            
            # Retry logic for rate limiting
            for attempt in range(3):
                try:
                    with DDGS() as ddgs:
                        # Search WITHOUT time filter for better results
                        search_results = ddgs.text(
                            query,
                            max_results=num_results * 2  # Get more to filter
                        )
                        
                        for result in search_results:
                            if len(results) >= num_results:
                                break
                            results.append({
                                'title': result.get('title', ''),
                                'url': result.get('link', result.get('href', '')),
                                'snippet': result.get('body', result.get('description', '')),
                                'date': datetime.now().strftime('%Y-%m-%d')
                            })
                    
                    if results:
                        break  # Success!
                    
                except Exception as e:
                    if attempt < 2:
                        import time
                        time.sleep(1)  # Wait before retry
                        continue
                    else:
                        raise e
            
            print(f"[WEB SEARCH] Found {len(results)} results for: {query}")
            return results
            
        except Exception as e:
            print(f"[WEB SEARCH ERROR] DuckDuckGo search failed: {e}")
            # Fallback to scraping method
            return self._duckduckgo_search_fallback(query, num_results)
    
    def _duckduckgo_search_fallback(self, query: str, num_results: int) -> list:
        """Fallback DuckDuckGo search using HTML scraping."""
        try:
            # Using DuckDuckGo's HTML search (no API key needed)
            url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            result_divs = soup.find_all('div', class_='result')[:num_results]
            
            for div in result_divs:
                title_elem = div.find('a', class_='result__a')
                snippet_elem = div.find('a', class_='result__snippet')
                
                if title_elem:
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'url': title_elem.get('href', ''),
                        'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                    })
            
            return results
            
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []
    
    def _analyze_source_credibility(self, results: list) -> list:
        """Analyze credibility of sources."""
        credible_domains = [
            'wikipedia.org', 'reuters.com', 'apnews.com', 'bbc.com',
            'nytimes.com', 'theguardian.com', 'npr.org', 'factcheck.org',
            'snopes.com', 'politifact.com', 'gov', 'edu', 'nature.com',
            'science.org', 'nih.gov', 'cdc.gov'
        ]
        
        credible = []
        for result in results:
            url = result.get('url', '').lower()
            if any(domain in url for domain in credible_domains):
                credible.append(result)
        
        return credible
    
    def _extract_consensus(self, results: list) -> str:
        """Extract common themes from search results."""
        if not results:
            return "No consensus found - insufficient search results."
        
        # Combine all snippets
        all_text = ' '.join([r.get('snippet', '') for r in results])
        
        # Simple consensus based on snippet content
        if len(all_text) < 50:
            return "Insufficient information for consensus."
        
        return f"Based on {len(results)} sources, analysis suggests reviewing detailed results."
