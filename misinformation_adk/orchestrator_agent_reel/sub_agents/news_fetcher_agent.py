"""
News Fetcher Agent - Fetches and summarizes popular news from Google News API
"""

import logging
import requests
from typing import List, Dict
import vertexai
from vertexai.preview.generative_models import GenerativeModel

logger = logging.getLogger(__name__)

class NewsFetcherAgent:
    """Agent that fetches popular news and summarizes them"""
    
    def __init__(self, project_id: str, location: str = "us-central1", news_api_key: str = None):
        """
        Initialize the News Fetcher Agent
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
            news_api_key: NewsAPI.org API key (optional, can use Google News RSS)
        """
        self.project_id = project_id
        self.location = location
        self.news_api_key = news_api_key
        self.model_name = "gemini-2.0-flash-exp"
        
        # Initialize Vertex AI for summarization
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel(self.model_name)
        
        logger.info(f"📰 News Fetcher Agent initialized - Model: {self.model_name}")
    
    def fetch_top_news(self, category: str = "general", country: str = "us", max_articles: int = 10) -> List[Dict]:
        """
        Fetch top news articles from Google News RSS or NewsAPI
        
        Args:
            category: News category (general, business, technology, entertainment, sports, science, health)
            country: Country code (us, in, gb, etc.)
            max_articles: Maximum number of articles to fetch
            
        Returns:
            List of news article dictionaries
        """
        logger.info(f"🌐 Fetching top {max_articles} news articles - Category: {category}, Country: {country}")
        
        try:
            if self.news_api_key:
                # Use NewsAPI.org if API key is available
                return self._fetch_from_newsapi(category, country, max_articles)
            else:
                # Use Google News RSS feed (free, no API key needed)
                return self._fetch_from_google_news_rss(category, country, max_articles)
                
        except Exception as e:
            logger.error(f"❌ Error fetching news: {str(e)}")
            return []
    
    def _fetch_from_newsapi(self, category: str, country: str, max_articles: int) -> List[Dict]:
        """Fetch news from NewsAPI.org"""
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            'country': country,
            'category': category,
            'pageSize': max_articles,
            'apiKey': self.news_api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        articles = []
        
        for article in data.get('articles', []):
            articles.append({
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'content': article.get('content', ''),
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'published_at': article.get('publishedAt', ''),
                'image_url': article.get('urlToImage', '')
            })
        
        logger.info(f"✅ Fetched {len(articles)} articles from NewsAPI")
        return articles
    
    def _fetch_from_google_news_rss(self, category: str, country: str, max_articles: int) -> List[Dict]:
        """Fetch news from Google News RSS feed (free alternative)"""
        import feedparser
        
        # Google News RSS URL
        # Format: https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB
        category_codes = {
            'general': 'CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB',
            'business': 'CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en',
            'technology': 'CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB',
            'entertainment': 'CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB',
            'sports': 'CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB',
            'science': 'CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtVnVHZ0pWVXlnQVAB',
            'health': 'CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtVnVLQUFQAQ'
        }
        
        # Use general news RSS feed
        rss_url = f"https://news.google.com/rss?hl=en-{country.upper()}&gl={country.upper()}&ceid={country.upper()}:en"
        
        logger.info(f"📡 Fetching from Google News RSS: {rss_url}")
        
        feed = feedparser.parse(rss_url)
        articles = []
        
        for entry in feed.entries[:max_articles]:
            articles.append({
                'title': entry.get('title', ''),
                'description': entry.get('summary', ''),
                'content': entry.get('summary', ''),
                'url': entry.get('link', ''),
                'source': entry.get('source', {}).get('title', 'Google News'),
                'published_at': entry.get('published', ''),
                'image_url': ''
            })
        
        logger.info(f"✅ Fetched {len(articles)} articles from Google News RSS")
        return articles
    
    def summarize_article(self, article: Dict, max_words: int = 100) -> str:
        """
        Summarize a news article using Gemini
        
        Args:
            article: Article dictionary with 'title', 'description', 'content'
            max_words: Maximum words in summary
            
        Returns:
            Summarized text suitable for video generation
        """
        logger.info(f"📝 Summarizing article: {article.get('title', 'Untitled')[:50]}...")
        
        try:
            # Combine title, description, and content
            full_text = f"""
Title: {article.get('title', '')}

{article.get('description', '')}

{article.get('content', '')}
"""
            
            prompt = f"""Summarize the following news article in approximately {max_words} words. 
Make it engaging, informative, and suitable for a short video reel. Focus on the key facts and important details.

Article:
{full_text}

Summary:"""
            
            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            
            logger.info(f"✅ Article summarized: {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error summarizing article: {str(e)}")
            # Fallback to title + description
            return f"{article.get('title', '')}. {article.get('description', '')}"
    
    def fetch_and_summarize_news(self, 
                                 category: str = "general", 
                                 country: str = "us", 
                                 max_articles: int = 5,
                                 summary_words: int = 100) -> List[Dict]:
        """
        Fetch top news and summarize each article
        
        Args:
            category: News category
            country: Country code
            max_articles: Maximum number of articles
            summary_words: Maximum words per summary
            
        Returns:
            List of dictionaries with 'original' article and 'summary'
        """
        logger.info("=" * 60)
        logger.info("🚀 FETCHING AND SUMMARIZING NEWS")
        logger.info("=" * 60)
        
        # Fetch articles
        articles = self.fetch_top_news(category, country, max_articles)
        
        if not articles:
            logger.warning("⚠️ No articles fetched")
            return []
        
        # Summarize each article
        results = []
        for i, article in enumerate(articles, 1):
            logger.info(f"\n📰 Processing article {i}/{len(articles)}")
            summary = self.summarize_article(article, summary_words)
            
            results.append({
                'original': article,
                'summary': summary,
                'article_id': f"news_{i}_{article.get('title', 'untitled')[:30].replace(' ', '_')}"
            })
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ COMPLETED: Processed {len(results)} news articles")
        logger.info("=" * 60)
        
        return results
