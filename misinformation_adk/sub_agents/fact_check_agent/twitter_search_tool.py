from google.adk.tools.base_tool import BaseTool
import requests
import os

class TwitterSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="twitter_search",
            description="Searches Twitter/X for information about claims and analyzes social consensus."
        )
        # TODO: Set your Twitter API credentials
        # self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.bearer_token = None
    
    def run(self, query: str, max_results: int = 20) -> dict:
        """
        Searches Twitter for tweets related to a claim.
        
        Args:
            query: Search query
            max_results: Maximum number of tweets to analyze
            
        Returns:
            Dictionary with tweet analysis and consensus
        """
        try:
            if not self.bearer_token:
                return {
                    "error": "Twitter API not configured. Set TWITTER_BEARER_TOKEN environment variable.",
                    "query": query,
                    "consensus": "UNAVAILABLE",
                    "tweets_analyzed": 0
                }
            
            # Search recent tweets
            tweets = self._search_tweets(query, max_results)
            
            if not tweets:
                return {
                    "query": query,
                    "tweets_analyzed": 0,
                    "consensus": "NO_DATA",
                    "sentiment": "neutral",
                    "message": "No tweets found for this query"
                }
            
            # Analyze sentiment and consensus
            analysis = self._analyze_tweets(tweets)
            
            return {
                "query": query,
                "tweets_analyzed": len(tweets),
                "consensus": analysis['consensus'],
                "sentiment": analysis['sentiment'],
                "verified_users_opinion": analysis['verified_opinion'],
                "sample_tweets": tweets[:5],  # Return sample
                "metrics": analysis['metrics']
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "query": query,
                "tweets_analyzed": 0,
                "consensus": "ERROR"
            }
    
    def _search_tweets(self, query: str, max_results: int) -> list:
        """Search tweets using Twitter API v2."""
        try:
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {
                "Authorization": f"Bearer {self.bearer_token}"
            }
            params = {
                "query": query,
                "max_results": min(max_results, 100),
                "tweet.fields": "author_id,created_at,public_metrics,entities",
                "expansions": "author_id",
                "user.fields": "verified,public_metrics"
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"Twitter API error: {response.status_code}")
                return []
            
            data = response.json()
            tweets = data.get('data', [])
            users = {user['id']: user for user in data.get('includes', {}).get('users', [])}
            
            # Enrich tweets with user data
            for tweet in tweets:
                tweet['user'] = users.get(tweet['author_id'], {})
            
            return tweets
            
        except Exception as e:
            print(f"Twitter search error: {e}")
            return []
    
    def _analyze_tweets(self, tweets: list) -> dict:
        """Analyze tweet sentiment and consensus."""
        if not tweets:
            return {
                'consensus': 'NO_DATA',
                'sentiment': 'neutral',
                'verified_opinion': 'UNKNOWN',
                'metrics': {}
            }
        
        # Simple sentiment analysis based on keywords
        positive_keywords = ['true', 'confirmed', 'verified', 'accurate', 'correct', 'factual']
        negative_keywords = ['false', 'fake', 'misinformation', 'debunked', 'incorrect', 'hoax']
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        verified_positive = 0
        verified_negative = 0
        
        for tweet in tweets:
            text = tweet.get('text', '').lower()
            is_verified = tweet.get('user', {}).get('verified', False)
            
            has_positive = any(kw in text for kw in positive_keywords)
            has_negative = any(kw in text for kw in negative_keywords)
            
            if has_positive and not has_negative:
                positive_count += 1
                if is_verified:
                    verified_positive += 1
            elif has_negative and not has_positive:
                negative_count += 1
                if is_verified:
                    verified_negative += 1
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
        
        # Verified users opinion
        if verified_positive > verified_negative:
            verified_opinion = "SUPPORTS_TRUE"
        elif verified_negative > verified_positive:
            verified_opinion = "SUPPORTS_FALSE"
        else:
            verified_opinion = "MIXED"
        
        return {
            'consensus': consensus,
            'sentiment': sentiment,
            'verified_opinion': verified_opinion,
            'metrics': {
                'total_tweets': total,
                'positive': positive_count,
                'negative': negative_count,
                'neutral': neutral_count,
                'verified_positive': verified_positive,
                'verified_negative': verified_negative
            }
        }
