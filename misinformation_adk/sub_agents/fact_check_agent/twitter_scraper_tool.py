from google.adk.tools.base_tool import BaseTool
import requests
from bs4 import BeautifulSoup
import json
import re

class TwitterScraperTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="twitter_scraper",
            description="Scrapes Twitter/X for tweets without API limits (FREE alternative to Twitter API)."
        )
        print("[INFO] Twitter Scraper initialized - bypasses API rate limits")
    
    def run(self, query: str, max_results: int = 20) -> dict:
        """
        Scrapes Twitter for tweets related to a claim using Nitter instances.
        
        Args:
            query: Search query
            max_results: Maximum number of tweets to analyze
            
        Returns:
            Dictionary with tweet analysis and consensus
        """
        try:
            # Use Nitter (Twitter frontend without rate limits)
            tweets = self._scrape_nitter(query, max_results)
            
            if not tweets:
                # Fallback: Try scraping Twitter directly
                print("[TWITTER SCRAPER] Nitter failed, trying direct scrape...")
                tweets = self._scrape_twitter_direct(query, max_results)
            
            if not tweets:
                return {
                    "query": query,
                    "tweets_analyzed": 0,
                    "consensus": "NO_DATA",
                    "sentiment": "neutral",
                    "message": "No tweets found. Twitter scraping may be blocked or query returned no results."
                }
            
            # Analyze sentiment and consensus
            analysis = self._analyze_tweets(tweets)
            
            return {
                "query": query,
                "tweets_analyzed": len(tweets),
                "consensus": analysis['consensus'],
                "sentiment": analysis['sentiment'],
                "sample_tweets": tweets[:5],
                "metrics": analysis['metrics'],
                "source": "twitter_scraper"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "query": query,
                "tweets_analyzed": 0,
                "consensus": "ERROR"
            }
    
    def _scrape_nitter(self, query: str, max_results: int) -> list:
        """Scrape Twitter via Nitter instance (no rate limits)."""
        # List of Nitter instances (Twitter frontends)
        nitter_instances = [
            'https://nitter.net',
            'https://nitter.poast.org',
            'https://nitter.privacydev.net',
            'https://nitter.cz'
        ]
        
        for instance in nitter_instances:
            try:
                url = f"{instance}/search"
                params = {'f': 'tweets', 'q': query}
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                print(f"[TWITTER SCRAPER] Trying {instance}...")
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                tweet_divs = soup.find_all('div', class_='timeline-item')
                
                if not tweet_divs:
                    continue
                
                tweets = []
                for div in tweet_divs[:max_results]:
                    # Extract tweet content
                    content_div = div.find('div', class_='tweet-content')
                    username_link = div.find('a', class_='username')
                    
                    if content_div and username_link:
                        tweets.append({
                            'text': content_div.get_text(strip=True),
                            'username': username_link.get_text(strip=True),
                            'source': f'{instance}/scraper'
                        })
                
                if tweets:
                    print(f"[TWITTER SCRAPER] Found {len(tweets)} tweets from {instance}")
                    return tweets
                    
            except Exception as e:
                print(f"[TWITTER SCRAPER] {instance} failed: {e}")
                continue
        
        return []
    
    def _scrape_twitter_direct(self, query: str, max_results: int) -> list:
        """
        Fallback: Try scraping Twitter directly (may be blocked).
        This is a placeholder - Twitter heavily blocks scrapers.
        """
        print("[TWITTER SCRAPER] Direct Twitter scraping not reliable, returning empty")
        return []
    
    def _analyze_tweets(self, tweets: list) -> dict:
        """Analyze scraped tweets for sentiment and consensus."""
        if not tweets:
            return {
                'consensus': 'NO_DATA',
                'sentiment': 'neutral',
                'metrics': {}
            }
        
        # Keywords for sentiment analysis
        positive_keywords = ['true', 'confirmed', 'verified', 'accurate', 'correct', 'factual']
        negative_keywords = ['false', 'fake', 'misinformation', 'debunked', 'incorrect', 'hoax']
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for tweet in tweets:
            text = tweet.get('text', '').lower()
            
            has_positive = any(kw in text for kw in positive_keywords)
            has_negative = any(kw in text for kw in negative_keywords)
            
            if has_positive and not has_negative:
                positive_count += 1
            elif has_negative and not has_positive:
                negative_count += 1
            else:
                neutral_count += 1
        
        total = len(tweets)
        
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
        
        return {
            'consensus': consensus,
            'sentiment': sentiment,
            'metrics': {
                'total_tweets': total,
                'positive': positive_count,
                'negative': negative_count,
                'neutral': neutral_count
            }
        }
