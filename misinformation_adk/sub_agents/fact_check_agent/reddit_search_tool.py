from google.adk.tools.base_tool import BaseTool
import requests
from bs4 import BeautifulSoup
import json
import os

class RedditSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="reddit_search",
            description="Searches Reddit for discussions and opinions about claims (FREE, no API key needed)."
        )
        print("[INFO] Reddit Search Tool initialized - using free JSON API")
    
    def run(self, query: str, max_results: int = 20) -> dict:
        """
        Searches Reddit for posts and comments related to a claim.
        Uses Reddit's free JSON API (no authentication required).
        
        Args:
            query: Search query
            max_results: Maximum number of posts to analyze
            
        Returns:
            Dictionary with Reddit analysis and consensus
        """
        try:
            # Search Reddit posts
            posts = self._search_reddit(query, max_results)
            
            if not posts:
                return {
                    "query": query,
                    "posts_analyzed": 0,
                    "consensus": "NO_DATA",
                    "sentiment": "neutral",
                    "message": "No Reddit posts found for this query"
                }
            
            # Analyze sentiment and consensus
            analysis = self._analyze_posts(posts)
            
            return {
                "query": query,
                "posts_analyzed": len(posts),
                "consensus": analysis['consensus'],
                "sentiment": analysis['sentiment'],
                "top_subreddits": analysis['top_subreddits'],
                "sample_posts": posts[:5],  # Return sample
                "metrics": analysis['metrics']
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "query": query,
                "posts_analyzed": 0,
                "consensus": "ERROR"
            }
    
    def _search_reddit(self, query: str, max_results: int) -> list:
        """Search Reddit using free JSON API."""
        try:
            # Reddit's free JSON API endpoint
            url = f"https://www.reddit.com/search.json"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            params = {
                'q': query,
                'limit': min(max_results, 100),
                'sort': 'relevance',
                't': 'month'  # Last month
            }
            
            print(f"[REDDIT] Searching for: '{query}'")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"[REDDIT ERROR] API error: {response.status_code}")
                return []
            
            data = response.json()
            posts_data = data.get('data', {}).get('children', [])
            
            if not posts_data:
                print(f"[REDDIT] No posts found")
                return []
            
            posts = []
            for post in posts_data:
                post_data = post.get('data', {})
                posts.append({
                    'title': post_data.get('title', ''),
                    'text': post_data.get('selftext', ''),
                    'subreddit': post_data.get('subreddit', ''),
                    'score': post_data.get('score', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'url': f"https://reddit.com{post_data.get('permalink', '')}",
                    'created_utc': post_data.get('created_utc', 0)
                })
            
            print(f"[REDDIT] Found {len(posts)} posts")
            return posts
            
        except Exception as e:
            print(f"[REDDIT ERROR] Search failed: {e}")
            return []
    
    def _analyze_posts(self, posts: list) -> dict:
        """Analyze Reddit posts for sentiment and consensus."""
        if not posts:
            return {
                'consensus': 'NO_DATA',
                'sentiment': 'neutral',
                'top_subreddits': [],
                'metrics': {}
            }
        
        # Keywords for sentiment analysis
        positive_keywords = ['true', 'confirmed', 'verified', 'accurate', 'correct', 'factual', 'legit', 'real']
        negative_keywords = ['false', 'fake', 'misinformation', 'debunked', 'incorrect', 'hoax', 'bs', 'lie', 'misleading']
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        subreddits = {}
        
        for post in posts:
            # Combine title and text for analysis
            text = (post.get('title', '') + ' ' + post.get('text', '')).lower()
            subreddit = post.get('subreddit', 'unknown')
            
            # Count subreddits
            subreddits[subreddit] = subreddits.get(subreddit, 0) + 1
            
            has_positive = any(kw in text for kw in positive_keywords)
            has_negative = any(kw in text for kw in negative_keywords)
            
            if has_positive and not has_negative:
                positive_count += 1
            elif has_negative and not has_positive:
                negative_count += 1
            else:
                neutral_count += 1
        
        total = len(posts)
        
        # Determine consensus
        if positive_count > negative_count * 2:
            consensus = "LIKELY_TRUE"
        elif negative_count > positive_count * 2:
            consensus = "LIKELY_FALSE"
        else:
            consensus = "MIXED"
        
        # Determine sentiment
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Top subreddits
        top_subreddits = sorted(subreddits.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'consensus': consensus,
            'sentiment': sentiment,
            'top_subreddits': [{'name': name, 'posts': count} for name, count in top_subreddits],
            'metrics': {
                'total_posts': total,
                'positive': positive_count,
                'negative': negative_count,
                'neutral': neutral_count
            }
        }
