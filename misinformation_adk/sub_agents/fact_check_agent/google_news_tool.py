from google.adk.tools.base_tool import BaseTool
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta
import json

class GoogleNewsTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="google_news_search",
            description="Searches Google News for recent news articles to verify claims with trusted sources."
        )
        # Google Custom Search API (News focused)
        self.api_key = os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')
        print("[INFO] Google News Tool initialized")
    
    def run(self, query: str, num_results: int = 10) -> dict:
        """
        Searches Google News for articles related to a claim.
        
        Args:
            query: Search query
            num_results: Number of news articles to return
            
        Returns:
            Dictionary with news articles and analysis
        """
        try:
            # Try Google Custom Search first (if API key available)
            if self.api_key and self.search_engine_id:
                results = self._google_custom_search(query, num_results)
            else:
                # Fallback to RSS feed method (free, no API key)
                results = self._google_news_rss(query, num_results)
            
            # Analyze news credibility
            credible_news = self._analyze_news_credibility(results)
            
            # Extract date patterns
            temporal_info = self._analyze_temporal_patterns(results)
            
            return {
                "query": query,
                "news_articles": results,
                "credible_news": credible_news,
                "temporal_info": temporal_info,
                "total_articles": len(results),
                "source": "Google News"
            }
            
        except Exception as e:
            print(f"[GOOGLE NEWS ERROR] {e}")
            return {
                "error": str(e),
                "query": query,
                "news_articles": [],
                "total_articles": 0
            }
    
    def _google_custom_search(self, query: str, num_results: int) -> list:
        """Use Google Custom Search API with News focus."""
        try:
            # Google Custom Search API endpoint
            base_url = "https://www.googleapis.com/customsearch/v1"
            
            results = []
            
            # Fetch results (max 10 per request)
            for start in range(1, num_results + 1, 10):
                params = {
                    'key': self.api_key,
                    'cx': self.search_engine_id,
                    'q': query,
                    'num': min(10, num_results - len(results)),
                    'start': start,
                    'dateRestrict': 'm6',  # Last 6 months
                    'sort': 'date',  # Sort by date
                    'siteSearch': 'news.google.com OR reuters.com OR apnews.com OR bbc.com',
                    'siteSearchFilter': 'i'  # Include these sites
                }
                
                response = requests.get(base_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data.get('items', []):
                        results.append({
                            'title': item.get('title', ''),
                            'url': item.get('link', ''),
                            'snippet': item.get('snippet', ''),
                            'source': item.get('displayLink', ''),
                            'date': item.get('pagemap', {}).get('metatags', [{}])[0].get('article:published_time', 'Unknown'),
                            'type': 'news'
                        })
                        
                        if len(results) >= num_results:
                            break
                    
                    if len(results) >= num_results:
                        break
                else:
                    print(f"[GOOGLE NEWS] API returned status {response.status_code}")
                    break
            
            print(f"[GOOGLE NEWS] Found {len(results)} articles via Custom Search API")
            return results
            
        except Exception as e:
            print(f"[GOOGLE NEWS] Custom Search API failed: {e}")
            # Fallback to RSS
            return self._google_news_rss(query, num_results)
    
    def _google_news_rss(self, query: str, num_results: int) -> list:
        """Use Google News RSS feeds (FREE, no API key needed)."""
        try:
            # Google News RSS URL
            rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(rss_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"[GOOGLE NEWS RSS] Failed with status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:num_results]
            
            results = []
            for item in items:
                title = item.find('title')
                link = item.find('link')
                description = item.find('description')
                pub_date = item.find('pubDate')
                source = item.find('source')
                
                results.append({
                    'title': title.text if title else '',
                    'url': link.text if link else '',
                    'snippet': BeautifulSoup(description.text if description else '', 'html.parser').get_text(strip=True),
                    'source': source.text if source else 'Google News',
                    'date': pub_date.text if pub_date else '',
                    'type': 'news'
                })
            
            print(f"[GOOGLE NEWS RSS] Found {len(results)} articles for: {query}")
            return results
            
        except Exception as e:
            print(f"[GOOGLE NEWS RSS ERROR] {e}")
            return []
    
    def _analyze_news_credibility(self, articles: list) -> list:
        """Filter for credible news sources."""
        trusted_sources = [
            'reuters', 'apnews', 'bbc', 'nytimes', 'theguardian', 'washingtonpost',
            'npr', 'cnn', 'bloomberg', 'economist', 'forbes', 'wired',
            'thehindu', 'indianexpress', 'timeofindia', 'ndtv', 'hindustantimes',
            'aljazeera', 'france24', 'dw.com'
        ]
        
        credible = []
        for article in articles:
            url = article.get('url', '').lower()
            source = article.get('source', '').lower()
            
            if any(trusted in url or trusted in source for trusted in trusted_sources):
                credible.append(article)
        
        return credible
    
    def _analyze_temporal_patterns(self, articles: list) -> dict:
        """Analyze when articles were published."""
        if not articles:
            return {"recent_articles": 0, "old_articles": 0, "pattern": "No data"}
        
        recent_count = 0
        old_count = 0
        
        # Simple date analysis
        for article in articles:
            date_str = article.get('date', '')
            if date_str and date_str != 'Unknown':
                try:
                    # Try parsing date
                    if '2024' in date_str or '2025' in date_str:
                        recent_count += 1
                    else:
                        old_count += 1
                except:
                    pass
        
        pattern = "RECENT" if recent_count > old_count else "OLDER" if old_count > 0 else "UNCLEAR"
        
        return {
            "recent_articles": recent_count,
            "old_articles": old_count,
            "total_dated": recent_count + old_count,
            "pattern": pattern
        }
