"""
Flask API Server for News Reel Generation
Orchestrates AI agents to create video reels from news summaries
"""

import os
import logging
import uuid
from datetime import datetime, timezone
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pathlib import Path
import sys

# Add orchestrator_agent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator_agent_reel import OrchestratorAgent
from orchestrator_agent_reel.utils.gcs_storage import GCSStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
LOCATION = os.getenv('LOCATION', 'us-central1')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')  # Optional

# Initialize orchestrator and storage
try:
    orchestrator = OrchestratorAgent(
        project_id=GCP_PROJECT_ID,
        location=LOCATION,
        news_api_key=NEWS_API_KEY
    )
    logger.info("✅ Orchestrator initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize orchestrator: {e}")
    orchestrator = None

try:
    gcs_storage = GCSStorage(bucket_name=GCS_BUCKET_NAME)
    logger.info("✅ GCS Storage initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize GCS storage: {e}")
    gcs_storage = None

# Job tracking (in-memory for simplicity)
jobs = {}
# News reels cache
news_reels = []

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'news-reel-generator',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@app.route('/api/generate_reel', methods=['POST'])
def generate_reel():
    """
    Generate a news reel from a summary
    
    Request body:
    {
        "news_summary": "Your news text...",
        "num_scenes": 5  // optional, default 5
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'news_summary' not in data:
            return jsonify({'error': 'Missing news_summary in request body'}), 400
        
        news_summary = data['news_summary']
        num_scenes = data.get('num_scenes', 5)
        
        # Validate inputs
        if not isinstance(news_summary, str) or len(news_summary.strip()) == 0:
            return jsonify({'error': 'news_summary must be a non-empty string'}), 400
        
        if not isinstance(num_scenes, int) or num_scenes < 1 or num_scenes > 10:
            return jsonify({'error': 'num_scenes must be an integer between 1 and 10'}), 400
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        jobs[job_id] = {
            'job_id': job_id,
            'status': 'processing',
            'progress': 0,
            'current_step': 'Initializing...',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'news_summary': news_summary[:100] + '...' if len(news_summary) > 100 else news_summary,
            'num_scenes': num_scenes
        }
        
        logger.info(f"🎬 Starting reel generation job {job_id}")
        logger.info(f"📰 Summary: {news_summary[:100]}...")
        logger.info(f"🎞️ Scenes: {num_scenes}")
        
        # Start generation in background (for now, synchronous - we'll make it async later)
        import threading
        thread = threading.Thread(
            target=process_reel_generation,
            args=(job_id, news_summary, num_scenes)
        )
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'processing',
            'message': 'Reel generation started'
        }), 202
        
    except Exception as e:
        logger.error(f"❌ Error in generate_reel endpoint: {e}")
        return jsonify({'error': str(e)}), 500

def process_reel_generation(job_id: str, news_summary: str, num_scenes: int):
    """Background process for reel generation"""
    try:
        # Update job status - Script Generation
        jobs[job_id].update({
            'status': 'processing',
            'progress': 10,
            'current_step': 'Generating script with Gemini...'
        })
        
        # Generate reel using orchestrator
        result = orchestrator.generate_reel(
            news_summary=news_summary,
            num_scenes=num_scenes
        )
        
        if not result.get('success'):
            jobs[job_id].update({
                'status': 'failed',
                'progress': 0,
                'error': result.get('error', 'Unknown error'),
                'current_step': 'Failed'
            })
            return
        
        # Update progress - Video Generated
        jobs[job_id].update({
            'progress': 80,
            'current_step': 'Uploading to Cloud Storage...'
        })
        
        # Upload to GCS (with fallback to local path if GCS fails)
        video_path = result['video_path']
        video_url = None
        
        if gcs_storage:
            try:
                video_filename = f"reels/reel_{job_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.mp4"
                
                with open(video_path, 'rb') as video_file:
                    video_data = video_file.read()
                
                video_url = gcs_storage.upload_video(video_data, video_filename)
                logger.info(f"✅ Uploaded to GCS: {video_url}")
                
                # Clean up local file after successful upload
                try:
                    os.remove(video_path)
                except Exception as cleanup_err:
                    logger.warning(f"⚠️ Failed to delete local file: {cleanup_err}")
                    
            except Exception as upload_err:
                logger.error(f"❌ GCS upload failed: {upload_err}")
                # Fallback: use local file path
                video_url = f"file://{video_path}"
                logger.info(f"⚠️ Using local file path: {video_url}")
        else:
            # No GCS configured, use local path
            video_url = f"file://{video_path}"
            logger.info(f"⚠️ GCS not configured, using local file: {video_url}")
        
        # Update job status - Complete
        jobs[job_id].update({
            'status': 'completed',
            'progress': 100,
            'current_step': 'Completed',
            'video_url': video_url,
            'scenes': result['scenes'],
            'completed_at': datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"✅ Job {job_id} completed successfully")
        logger.info(f"📹 Video URL: {video_url}")
        
    except Exception as e:
        logger.error(f"❌ Error processing job {job_id}: {e}")
        jobs[job_id].update({
            'status': 'failed',
            'progress': 0,
            'error': str(e),
            'current_step': 'Failed'
        })

@app.route('/api/job_status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get the status of a generation job"""
    job = jobs.get(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job)

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs"""
    return jsonify({
        'jobs': list(jobs.values()),
        'total': len(jobs)
    })

@app.route('/api/fetch_news', methods=['GET'])
def fetch_news():
    """
    Fetch popular news articles
    
    Query parameters:
    - category: News category (general, business, technology, etc.)
    - country: Country code (us, in, gb, etc.)
    - max_articles: Maximum number of articles (default: 5)
    """
    try:
        if not orchestrator:
            return jsonify({'error': 'Orchestrator not initialized. Check server configuration.'}), 503
            
        category = request.args.get('category', 'general')
        country = request.args.get('country', 'us')
        max_articles = int(request.args.get('max_articles', 5))
        
        logger.info(f"📰 Fetching news: category={category}, country={country}, max={max_articles}")
        
        # Fetch and summarize news
        news_articles = orchestrator.news_fetcher.fetch_and_summarize_news(
            category=category,
            country=country,
            max_articles=max_articles,
            summary_words=100
        )
        
        if not news_articles:
            return jsonify({'error': 'No news articles found'}), 404
        
        logger.info(f"✅ Fetched {len(news_articles)} news articles")
        
        return jsonify({
            'success': True,
            'articles': news_articles,
            'total': len(news_articles)
        })
        
    except Exception as e:
        logger.error(f"❌ Error fetching news: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto_generate_news_reels', methods=['POST'])
def auto_generate_news_reels():
    """
    Automatically fetch news and generate reels for all articles
    
    Request body:
    {
        "category": "general",
        "country": "us",
        "max_articles": 5,
        "num_scenes": 8
    }
    """
    try:
        data = request.get_json() or {}
        
        category = data.get('category', 'general')
        country = data.get('country', 'us')
        max_articles = data.get('max_articles', 5)
        num_scenes = data.get('num_scenes', 8)
        
        logger.info(f"🚀 Auto-generating reels for {max_articles} news articles (ONE AT A TIME)")
        
        # Fetch and summarize news
        news_articles = orchestrator.news_fetcher.fetch_and_summarize_news(
            category=category,
            country=country,
            max_articles=max_articles,
            summary_words=100
        )
        
        if not news_articles:
            return jsonify({'error': 'No news articles found'}), 404
        
        # Create job for FIRST article only (sequential processing)
        first_article = news_articles[0]
        job_id = str(uuid.uuid4())
        article_id = first_article.get('article_id', job_id)
        
        jobs[job_id] = {
            'job_id': job_id,
            'article_id': article_id,
            'status': 'processing',
            'progress': 0,
            'current_step': 'Queued...',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'news_summary': first_article['summary'][:100] + '...',
            'num_scenes': num_scenes,
            'article_title': first_article['original']['title'],
            'article_source': first_article['original']['source'],
            'remaining_articles': news_articles[1:],  # Store remaining for sequential processing
            'current_index': 0,
            'total_articles': len(news_articles)
        }
        
        # Start generation for FIRST article only
        import threading
        thread = threading.Thread(
            target=process_news_reel_generation,
            args=(job_id, first_article, num_scenes, news_articles[1:])  # Pass remaining articles
        )
        thread.start()
        
        logger.info(f"✅ Started generating reel 1 of {len(news_articles)}")
        
        return jsonify({
            'success': True,
            'message': f'Generating reel 1 of {len(news_articles)}',
            'job_ids': [job_id],  # Only return first job ID
            'total_articles': len(news_articles)
        }), 202
        
    except Exception as e:
        logger.error(f"❌ Error in auto_generate_news_reels: {e}")
        return jsonify({'error': str(e)}), 500

def process_news_reel_generation(job_id: str, article_data: dict, num_scenes: int, remaining_articles: list = None):
    """Background process for news reel generation (sequential)"""
    try:
        news_summary = article_data['summary']
        article_info = article_data['original']
        
        # Update job status
        jobs[job_id].update({
            'status': 'processing',
            'progress': 10,
            'current_step': 'Generating script with Gemini...'
        })
        
        # Generate reel
        result = orchestrator.generate_reel(
            news_summary=news_summary,
            num_scenes=num_scenes
        )
        
        if not result.get('success'):
            jobs[job_id].update({
                'status': 'failed',
                'progress': 0,
                'error': result.get('error', 'Unknown error'),
                'current_step': 'Failed'
            })
            return
        
        # Upload to GCS (with fallback)
        jobs[job_id].update({
            'progress': 80,
            'current_step': 'Uploading to Cloud Storage...'
        })
        
        video_path = result['video_path']
        video_url = None
        
        if gcs_storage:
            try:
                video_filename = f"news_reels/reel_{job_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.mp4"
                
                with open(video_path, 'rb') as video_file:
                    video_data = video_file.read()
                
                video_url = gcs_storage.upload_video(video_data, video_filename)
                logger.info(f"✅ News reel uploaded to GCS: {video_url}")
                
                # Clean up local file after successful upload
                try:
                    os.remove(video_path)
                except Exception as cleanup_err:
                    logger.warning(f"⚠️ Failed to delete local file: {cleanup_err}")
                    
            except Exception as upload_err:
                logger.error(f"❌ GCS upload failed: {upload_err}")
                # Fallback: use local file path
                video_url = f"file://{video_path}"
                logger.info(f"⚠️ Using local file path: {video_url}")
        else:
            # No GCS configured, use local path
            video_url = f"file://{video_path}"
            logger.info(f"⚠️ GCS not configured, using local file: {video_url}")
            pass
        
        # Update job status
        jobs[job_id].update({
            'status': 'completed',
            'progress': 100,
            'current_step': 'Completed',
            'video_url': video_url,
            'scenes': result['scenes'],
            'completed_at': datetime.now(timezone.utc).isoformat()
        })
        
        # Add to news reels cache
        news_reels.append({
            'job_id': job_id,
            'article_id': article_data.get('article_id'),
            'title': article_info.get('title'),
            'source': article_info.get('source'),
            'video_url': video_url,
            'summary': news_summary,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'url': article_info.get('url')
        })
        
        logger.info(f"✅ News reel {job_id} completed successfully")
        
        # Process next article if any remaining
        if remaining_articles and len(remaining_articles) > 0:
            next_article = remaining_articles[0]
            next_remaining = remaining_articles[1:]
            
            logger.info(f"🎬 Starting next reel ({len(remaining_articles)} remaining)...")
            
            # Create new job for next article
            next_job_id = str(uuid.uuid4())
            jobs[next_job_id] = {
                'job_id': next_job_id,
                'article_id': next_article.get('article_id'),
                'status': 'processing',
                'progress': 0,
                'current_step': 'Queued...',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'news_summary': next_article['summary'][:100] + '...',
                'num_scenes': num_scenes,
                'article_title': next_article['original']['title'],
                'article_source': next_article['original']['source']
            }
            
            # Start next generation
            import threading
            thread = threading.Thread(
                target=process_news_reel_generation,
                args=(next_job_id, next_article, num_scenes, next_remaining)
            )
            thread.start()
        
    except Exception as e:
        logger.error(f"❌ Error processing news reel {job_id}: {e}")
        jobs[job_id].update({
            'status': 'failed',
            'progress': 0,
            'error': str(e),
            'current_step': 'Failed'
        })

@app.route('/api/news_reels', methods=['GET'])
def get_news_reels():
    """Get all generated news reels"""
    try:
        return jsonify({
            'success': True,
            'reels': news_reels,
            'total': len(news_reels)
        })
    except Exception as e:
        logger.error(f"❌ Error getting news reels: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'reels': [],
            'total': 0
        }), 500

if __name__ == '__main__':
    logger.info("🚀 Starting News Reel Generator API...")
    logger.info(f"📦 Project ID: {GCP_PROJECT_ID}")
    logger.info(f"🪣 GCS Bucket: {GCS_BUCKET_NAME}")
    logger.info(f"🌍 Location: {LOCATION}")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
