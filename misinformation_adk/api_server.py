"""
FastAPI Server for Misinformation Detection API
Provides endpoints for fact-checking and shareable reports
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Literal
import uvicorn
import json
import os
import hashlib
import shutil
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set HuggingFace cache to D drive if specified in .env (MUST be before importing transformers)
if os.getenv('TRANSFORMERS_CACHE'):
    os.environ['TRANSFORMERS_CACHE'] = os.getenv('TRANSFORMERS_CACHE')
if os.getenv('HF_HOME'):
    os.environ['HF_HOME'] = os.getenv('HF_HOME')
if os.getenv('HF_HUB_CACHE'):
    os.environ['HF_HUB_CACHE'] = os.getenv('HF_HUB_CACHE')

# Import orchestrator
from orchestrator_agent.orchestrator_tool import OrchestratorTool

app = FastAPI(
    title="Misinformation Detection API",
    description="AI-powered fact-checking with deepfake detection and shareable reports",
    version="2.0.0"
)

# Enable CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = OrchestratorTool()

# Reports and uploads directories
REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'data', 'reports')
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), 'data', 'uploads')
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)


class FactCheckRequest(BaseModel):
    """Fact-check request from Chrome extension"""
    content: str
    content_type: Literal["text", "image", "video", "audio", "url"]
    file_path: Optional[str] = None
    url: Optional[str] = None  # For YouTube links


class FactCheckResponse(BaseModel):
    """Fact-check response with report ID"""
    report_id: str
    share_url: str
    verdict: str
    confidence: float
    summary: str


@app.get("/", response_class=HTMLResponse)
async def root():
    """API homepage"""
    return """
    <html>
        <head><title>Misinformation Detection API</title></head>
        <body style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1>🛡️ Misinformation Detection API</h1>
            <p>Active and running! Use the following endpoints:</p>
            <ul>
                <li><code>POST /api/fact-check</code> - Submit content for analysis</li>
                <li><code>GET /api/report/{report_id}</code> - View report (JSON)</li>
                <li><code>GET /report/{report_id}</code> - View report (HTML)</li>
                <li><code>GET /health</code> - Health check</li>
            </ul>
            <p><a href="/docs">📚 API Documentation</a></p>
        </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/api/fact-check", response_model=FactCheckResponse)
async def fact_check(request: FactCheckRequest):
    """
    Main fact-checking endpoint for Chrome extension
    
    Accepts content with pre-determined type to skip content intake stage
    """
    try:
        print(f"\n[API] Received fact-check request:")
        print(f"  Content Type: {request.content_type}")
        print(f"  Content: {request.content[:100]}..." if len(request.content) > 100 else f"  Content: {request.content}")
        
        # Handle YouTube URLs
        if request.content_type == "url" and request.url:
            if "youtube.com" in request.url or "youtu.be" in request.url:
                transcript = await extract_youtube_transcript(request.url)
                if transcript:
                    request.content = f"YouTube Video Transcript:\n{transcript}"
                    request.content_type = "text"
                else:
                    raise HTTPException(status_code=400, detail="Could not extract YouTube transcript")
        
        # Run orchestrator with content_type hint
        result = orchestrator.run(
            user_input=request.content,
            file_path=request.file_path,
            content_type=request.content_type
        )
        
        # Generate report ID
        report_id = generate_report_id(request.content)
        
        # Save report
        save_report(report_id, result)
        
        # Generate share URL
        share_url = f"http://localhost:8000/report/{report_id}"
        
        # Extract summary
        fact_check = result.get("stages", {}).get("fact_check", {})
        summary = generate_summary(result)
        
        return FactCheckResponse(
            report_id=report_id,
            share_url=share_url,
            verdict=fact_check.get("verdict", "UNCERTAIN"),
            confidence=fact_check.get("confidence", 0.0),
            summary=summary
        )
        
    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/report/{report_id}")
async def get_report_json(report_id: str):
    """Get report in JSON format"""
    report_path = os.path.join(REPORTS_DIR, f"{report_id}.json")
    
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    return JSONResponse(content=report)


@app.post("/api/analyze-media")
async def analyze_media(
    file: UploadFile = File(...),
    media_type: str = Form(...)
):
    """
    Analyze uploaded media file (image/video/audio) for:
    1. Deepfake detection
    2. Content verification (even if media is fake, content might be true)
    
    Returns both analyses with overall verdict
    """
    try:
        print(f"\n[API] Received media analysis request:")
        print(f"  Media Type: {media_type}")
        print(f"  Filename: {file.filename}")
        print(f"  Content Type: {file.content_type}")
        
        # Save uploaded file temporarily
        file_ext = os.path.splitext(file.filename)[1]
        temp_filename = f"{hashlib.md5(file.filename.encode()).hexdigest()}{file_ext}"
        temp_filepath = os.path.join(UPLOADS_DIR, temp_filename)
        
        with open(temp_filepath, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"  Saved to: {temp_filepath}")
        
        # Run orchestrator with media file
        print(f"\n⚡ Running deepfake detection + content verification...")
        result = orchestrator.run(
            user_input=f"Analyze this {media_type} for deepfakes and verify content accuracy",
            file_path=temp_filepath,
            content_type=media_type
        )
        
        # Extract deepfake and fact-check results
        deepfake_analysis = result.get('media_analysis', {})
        fact_check = result.get('fact_check', {})
        
        # Determine overall verdict
        is_deepfake = False
        content_verdict = "UNCERTAIN"
        
        if media_type == 'image':
            deepfake_data = deepfake_analysis.get('image_deepfake', {})
            is_deepfake = deepfake_data.get('is_manipulated', False)
        elif media_type == 'video':
            deepfake_data = deepfake_analysis.get('video_deepfake', {})
            is_deepfake = deepfake_data.get('is_deepfake', False)
        elif media_type == 'audio':
            deepfake_data = deepfake_analysis.get('audio_deepfake', {})
            is_deepfake = deepfake_data.get('is_deepfake', False)
        else:
            deepfake_data = {}
        
        content_verdict = fact_check.get('verdict', 'UNCERTAIN')
        content_confidence = fact_check.get('confidence', 0.5)
        
        # Create overall verdict message
        if is_deepfake and content_verdict == 'FALSE':
            overall_verdict = "⚠️ DOUBLE ALERT: Media is a DEEPFAKE and the content is FALSE. This is deliberate misinformation."
        elif is_deepfake and content_verdict == 'TRUE':
            overall_verdict = "⚠️ MIXED RESULT: Media is a DEEPFAKE but the content/claims are actually TRUE. The fake media is being used to spread true information."
        elif is_deepfake:
            overall_verdict = "⚠️ DEEPFAKE DETECTED: Media is manipulated/fabricated, but content accuracy is uncertain."
        elif content_verdict == 'FALSE':
            overall_verdict = "❌ FALSE CONTENT: Media appears authentic but the claims/content are FALSE."
        elif content_verdict == 'TRUE':
            overall_verdict = "✅ VERIFIED: Media is authentic and content is TRUE."
        else:
            overall_verdict = "❓ UNCERTAIN: Unable to definitively verify media authenticity or content accuracy."
        
        # Create combined report
        combined_result = {
            'media_type': media_type,
            'filename': file.filename,
            'deepfake_analysis': {
                'is_deepfake': is_deepfake,
                'confidence': deepfake_data.get('confidence', 0.0),
                'explanation': deepfake_data.get('explanation', 'Analysis not available'),
                'technical_details': deepfake_data.get('technical_details', {})
            },
            'content_analysis': {
                'verdict': content_verdict,
                'confidence': content_confidence,
                'summary': fact_check.get('summary', ''),
                'explanation': fact_check.get('explanation', ''),
                'sources': fact_check.get('sources', [])
            },
            'overall_verdict': overall_verdict,
            'timestamp': datetime.now().isoformat()
        }
        
        # Generate report ID and save
        report_id = hashlib.md5(f"{temp_filepath}{datetime.now().timestamp()}".encode()).hexdigest()
        save_report(report_id, combined_result)
        share_url = f"http://localhost:8000/report/{report_id}"
        
        print(f"\n✅ Media analysis complete!")
        print(f"  Deepfake: {'YES ⚠️' if is_deepfake else 'NO ✅'}")
        print(f"  Content: {content_verdict}")
        print(f"  Report: {share_url}")
        
        return {
            **combined_result,
            'report_id': report_id,
            'share_url': share_url
        }
        
    except Exception as e:
        print(f"\n[API ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp file
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except:
                pass


@app.get("/report/{report_id}", response_class=HTMLResponse)
async def get_report_html(report_id: str):
    """Get shareable report in HTML format"""
    report_path = os.path.join(REPORTS_DIR, f"{report_id}.json")
    
    if not os.path.exists(report_path):
        return """
        <html>
            <body style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
                <h1>❌ Report Not Found</h1>
                <p>The report you're looking for doesn't exist or has been removed.</p>
            </body>
        </html>
        """
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    return generate_html_report(report)


async def extract_youtube_transcript(url: str) -> Optional[str]:
    """Extract transcript from YouTube video"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        import re
        
        # Extract video ID
        video_id = None
        if "youtube.com/watch?v=" in url:
            video_id = url.split("watch?v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        
        if not video_id:
            return None
        
        # Get transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([t['text'] for t in transcript_list])
        
        return transcript
        
    except Exception as e:
        print(f"[YouTube] Transcript extraction failed: {e}")
        return None


def generate_report_id(content: str) -> str:
    """Generate unique report ID"""
    timestamp = datetime.now().isoformat()
    hash_input = f"{content}{timestamp}".encode('utf-8')
    return hashlib.sha256(hash_input).hexdigest()[:16]


def save_report(report_id: str, result: dict):
    """Save report to file"""
    report_path = os.path.join(REPORTS_DIR, f"{report_id}.json")
    
    # Add metadata
    result["report_id"] = report_id
    result["generated_at"] = datetime.now().isoformat()
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


def generate_summary(result: dict) -> str:
    """Generate concise summary for quick view"""
    fact_check = result.get("stages", {}).get("fact_check", {})
    verdict = fact_check.get("verdict", "UNCERTAIN")
    confidence = fact_check.get("confidence", 0.0)
    explanation = fact_check.get("explanation", "")
    
    # Extract first sentence or first 150 chars
    if explanation:
        first_sentence = explanation.split('.')[0] + '.'
        summary = first_sentence[:150] + "..." if len(first_sentence) > 150 else first_sentence
    else:
        summary = "Analysis completed."
    
    return summary


def generate_html_report(report: dict) -> str:
    """Generate beautiful HTML report for sharing (text or media)"""
    
    # Check if this is a media report
    if 'media_type' in report:
        return generate_media_html_report(report)
    
    # Otherwise, generate text fact-check report
    fact_check = report.get("stages", {}).get("fact_check", {})
    media_analysis = report.get("stages", {}).get("media_analysis", {})
    
    verdict = fact_check.get("verdict", "UNCERTAIN")
    confidence = fact_check.get("confidence", 0.0)
    temporal_status = fact_check.get("temporal_status", "UNCLEAR")
    time_verification = fact_check.get("time_verification", "")
    explanation = fact_check.get("explanation", "")
    key_evidence = fact_check.get("key_evidence", [])
    sources = fact_check.get("sources", [])
    warnings = fact_check.get("warnings", [])
    web_sources = fact_check.get("web_sources_found", 0)
    
    # Verdict styling
    verdict_colors = {
        "TRUE": "#10b981",
        "FALSE": "#ef4444",
        "PARTIALLY_TRUE": "#f59e0b",
        "UNCERTAIN": "#6b7280",
        "OUTDATED_INFO": "#8b5cf6"
    }
    verdict_color = verdict_colors.get(verdict, "#6b7280")
    
    verdict_icons = {
        "TRUE": "✅",
        "FALSE": "❌",
        "PARTIALLY_TRUE": "⚠️",
        "UNCERTAIN": "❓",
        "OUTDATED_INFO": "⏰"
    }


def generate_media_html_report(report: dict) -> str:
    """Generate HTML report for media analysis (deepfake + content)"""
    media_type = report.get('media_type', 'media')
    filename = report.get('filename', 'Unknown')
    deepfake = report.get('deepfake_analysis', {})
    content = report.get('content_analysis', {})
    overall = report.get('overall_verdict', '')
    timestamp = report.get('timestamp', '')
    
    is_deepfake = deepfake.get('is_deepfake', False)
    deepfake_confidence = deepfake.get('confidence', 0.0) * 100
    deepfake_explanation = deepfake.get('explanation', '')
    
    content_verdict = content.get('verdict', 'UNCERTAIN')
    content_confidence = content.get('confidence', 0.0) * 100
    content_summary = content.get('summary', content.get('explanation', ''))
    content_sources = content.get('sources', [])
    
    # Colors
    deepfake_color = "#ef4444" if is_deepfake else "#10b981"
    
    verdict_colors = {
        "TRUE": "#10b981",
        "FALSE": "#ef4444",
        "PARTIALLY_TRUE": "#f59e0b",
        "UNCERTAIN": "#6b7280"
    }
    content_color = verdict_colors.get(content_verdict, "#6b7280")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Media Analysis Report - {filename}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            .header h1 {{
                font-size: 32px;
                margin-bottom: 10px;
            }}
            .header p {{
                font-size: 16px;
                opacity: 0.9;
            }}
            .content {{
                padding: 40px;
            }}
            .section {{
                margin-bottom: 40px;
                padding: 30px;
                border-radius: 12px;
                border-left: 5px solid;
            }}
            .deepfake-section {{
                background: {deepfake_color}15;
                border-color: {deepfake_color};
            }}
            .content-section {{
                background: {content_color}15;
                border-color: {content_color};
            }}
            .overall-section {{
                background: #f9fafb;
                border-color: #667eea;
            }}
            .section h2 {{
                font-size: 24px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .section h3 {{
                font-size: 18px;
                margin: 20px 0 10px;
                color: #374151;
            }}
            .verdict-badge {{
                display: inline-block;
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: 600;
                font-size: 14px;
                margin-top: 10px;
            }}
            .confidence {{
                font-size: 16px;
                color: #6b7280;
                margin-top: 10px;
            }}
            .explanation {{
                line-height: 1.8;
                color: #374151;
                margin-top: 15px;
            }}
            .sources {{
                list-style: none;
                margin-top: 15px;
            }}
            .sources li {{
                padding: 10px;
                background: #f9fafb;
                border-left: 3px solid #667eea;
                margin-bottom: 8px;
                border-radius: 4px;
                font-size: 14px;
            }}
            .footer {{
                padding: 30px 40px;
                background: #f9fafb;
                text-align: center;
                color: #6b7280;
                font-size: 14px;
            }}
            .timestamp {{
                color: #9ca3af;
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ Media Analysis Report</h1>
                <p>Deepfake Detection + Content Verification</p>
                <p style="margin-top: 10px; font-size: 14px; opacity: 0.8;">
                    {media_type.upper()} • {filename}
                </p>
            </div>
            
            <div class="content">
                <!-- Overall Verdict -->
                <div class="section overall-section">
                    <h2>📊 Overall Assessment</h2>
                    <p class="explanation">{overall}</p>
                </div>
                
                <!-- Deepfake Analysis -->
                <div class="section deepfake-section">
                    <h2>{'⚠️ Deepfake Detection' if is_deepfake else '✅ Authenticity Check'}</h2>
                    <div class="verdict-badge" style="background: {deepfake_color}20; color: {deepfake_color};">
                        {'DEEPFAKE DETECTED' if is_deepfake else 'AUTHENTIC MEDIA'}
                    </div>
                    <div class="confidence">Confidence: {deepfake_confidence:.1f}%</div>
                    <p class="explanation">{deepfake_explanation}</p>
                </div>
                
                <!-- Content Fact-Check -->
                <div class="section content-section">
                    <h2>🔍 Content Verification</h2>
                    <div class="verdict-badge" style="background: {content_color}20; color: {content_color};">
                        {content_verdict.replace('_', ' ')}
                    </div>
                    <div class="confidence">Confidence: {content_confidence:.1f}%</div>
                    <p class="explanation">{content_summary}</p>
                    
                    {'<h3>📚 Sources:</h3><ul class="sources">' + ''.join([f'<li>{source}</li>' for source in content_sources[:5]]) + '</ul>' if content_sources else ''}
                </div>
            </div>
            
            <div class="footer">
                <p>🛡️ AI-Powered Misinformation Detection System</p>
                <p class="timestamp">Generated: {timestamp}</p>
                <p style="margin-top: 10px; font-size: 12px;">
                    This report combines deepfake detection with content fact-checking.<br>
                    Even if media is fake, the claims within may be true (or vice versa).
                </p>
            </div>
        </div>
    </body>
    </html>
    """


def generate_html_report(report: dict) -> str:
    """Generate beautiful HTML report for sharing (text fact-check)."""
    
    # Check if this is a media report
    if 'media_type' in report:
        return generate_media_html_report(report)
    
    # Text fact-check report
    fact_check = report.get("stages", {}).get("fact_check", {})
    media_analysis = report.get("stages", {}).get("media_analysis", {})
    
    verdict = fact_check.get("verdict", "UNCERTAIN")
    confidence = fact_check.get("confidence", 0.0)
    temporal_status = fact_check.get("temporal_status", "UNCLEAR")
    time_verification = fact_check.get("time_verification", "")
    explanation = fact_check.get("explanation", "")
    key_evidence = fact_check.get("key_evidence", [])
    sources = fact_check.get("sources", [])
    warnings = fact_check.get("warnings", [])
    web_sources = fact_check.get("web_sources_found", 0)
    twitter_consensus = fact_check.get("twitter_consensus", "")
    social_perspective = fact_check.get("social_media_perspective", "")
    
    # Verdict styling
    verdict_colors = {
        "TRUE": "#10b981",
        "FALSE": "#ef4444",
        "PARTIALLY_TRUE": "#f59e0b",
        "UNCERTAIN": "#6b7280",
        "OUTDATED_INFO": "#8b5cf6"
    }
    verdict_color = verdict_colors.get(verdict, "#6b7280")
    
    verdict_icons = {
        "TRUE": "✅",
        "FALSE": "❌",
        "PARTIALLY_TRUE": "⚠️",
        "UNCERTAIN": "❓",
        "OUTDATED_INFO": "⏰"
    }
    verdict_icon = verdict_icons.get(verdict, "❓")
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>विश्वास नेत्र - Fact-Check Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #faf5f0 0%, #e8dfd6 100%);
            padding: 20px;
            min-height: 100vh;
            position: relative;
        }}
        
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 24px;
            box-shadow: 0 25px 80px rgba(139, 92, 64, 0.15);
            overflow: hidden;
            animation: fadeInUp 0.6s ease-out;
        }}
        
        .watermark {{
            position: absolute;
            top: 20px;
            right: 30px;
            background: rgba(255, 255, 255, 0.95);
            padding: 12px 24px;
            border-radius: 50px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 600;
            color: #6b4423;
            font-size: 16px;
            backdrop-filter: blur(10px);
            z-index: 1000;
        }}
        
        .watermark::before {{
            content: '👁️';
            font-size: 24px;
            animation: pulse 2s infinite;
        }}
        
        .brand-text {{
            font-family: 'Inter', sans-serif;
            letter-spacing: 0.5px;
        }}
        
        .hindi-name {{
            font-size: 14px;
            color: #8b5c40;
            opacity: 0.9;
        }}
        
        .header {{
            background: linear-gradient(135deg, {verdict_color} 0%, {verdict_color}dd 100%);
            color: white;
            padding: 50px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: rotate 20s linear infinite;
        }}
        
        @keyframes rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        
        .verdict-icon {{
            font-size: 64px;
            margin-bottom: 15px;
            animation: pulse 2s infinite;
            position: relative;
            z-index: 1;
        }}
        
        .verdict-text {{
            font-size: 40px;
            font-weight: 700;
            margin-bottom: 12px;
            position: relative;
            z-index: 1;
            text-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .confidence {{
            font-size: 20px;
            opacity: 0.95;
            position: relative;
            z-index: 1;
            font-weight: 400;
        }}
        
        .content {{
            padding: 45px;
            background: #fefdfb;
        }}
        
        .section {{
            margin-bottom: 35px;
            animation: fadeInUp 0.6s ease-out;
            animation-fill-mode: both;
        }}
        
        .section:nth-child(1) {{ animation-delay: 0.1s; }}
        .section:nth-child(2) {{ animation-delay: 0.2s; }}
        .section:nth-child(3) {{ animation-delay: 0.3s; }}
        .section:nth-child(4) {{ animation-delay: 0.4s; }}
        
        .section-title {{
            font-size: 20px;
            font-weight: 700;
            color: #6b4423;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            letter-spacing: -0.5px;
        }}
        
        .explanation {{
            background: linear-gradient(135deg, #faf8f5 0%, #f5f2ed 100%);
            padding: 28px;
            border-radius: 16px;
            border-left: 5px solid {verdict_color};
            line-height: 1.8;
            color: #4a3826;
            box-shadow: 0 4px 15px rgba(139, 92, 64, 0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .explanation:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(139, 92, 64, 0.12);
        }}
        
        .evidence-list, .sources-list {{
            list-style: none;
        }}
        
        .evidence-list li, .sources-list li {{
            padding: 16px 20px;
            background: linear-gradient(135deg, #fff 0%, #faf8f5 100%);
            margin-bottom: 12px;
            border-radius: 12px;
            border-left: 4px solid #d4a574;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            transition: all 0.3s ease;
            color: #4a3826;
            line-height: 1.6;
        }}
        
        .evidence-list li:hover, .sources-list li:hover {{
            transform: translateX(4px);
            box-shadow: 0 4px 12px rgba(139, 92, 64, 0.12);
        }}
        
        .warning {{
            background: linear-gradient(135deg, #fff4e6 0%, #ffe8cc 100%);
            border-left: 5px solid #f59e0b;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(245, 158, 11, 0.15);
            animation: pulse 2s infinite;
        }}
        
        .social-media {{
            background: linear-gradient(135deg, #f0f4ff 0%, #e0e9ff 100%);
            border-left: 5px solid #6366f1;
            padding: 20px;
            border-radius: 12px;
            margin-top: 20px;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.15);
            color: #3730a3;
        }}
        
        .meta {{
            background: linear-gradient(135deg, #faf8f5 0%, #f0ede8 100%);
            padding: 30px;
            border-top: 3px solid #d4a574;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 25px;
        }}
        
        .meta-item {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        
        .meta-label {{
            font-size: 12px;
            color: #8b5c40;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}
        
        .meta-value {{
            font-size: 16px;
            font-weight: 700;
            color: #6b4423;
        }}
        
        .share-button {{
            display: block;
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #8b5c40 0%, #6b4423 100%);
            color: white;
            text-align: center;
            border: none;
            border-radius: 12px;
            font-size: 17px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 6px 20px rgba(139, 92, 64, 0.3);
            letter-spacing: 0.5px;
        }}
        
        .share-button:hover {{
            background: linear-gradient(135deg, #6b4423 0%, #5a3820 100%);
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(139, 92, 64, 0.4);
        }}
        
        .share-button:active {{
            transform: translateY(0);
        }}
        
        .badge {{
            display: inline-block;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }}
        
        .badge-current {{ background: #d1fae5; color: #065f46; }}
        .badge-outdated {{ background: #fee2e2; color: #991b1b; }}
        .badge-timeless {{ background: #e0e9ff; color: #3730a3; }}
        
        .footer {{
            padding: 30px;
            text-align: center;
            background: linear-gradient(135deg, #faf8f5 0%, #f0ede8 100%);
            color: #8b5c40;
            font-size: 14px;
            border-top: 2px solid #e8dfd6;
        }}
        
        .footer-brand {{
            font-size: 18px;
            font-weight: 700;
            color: #6b4423;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }}
        
        .footer-tagline {{
            font-size: 13px;
            color: #a67c52;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="watermark">
        <span class="brand-text">Vishwas Netra</span>
        <span class="hindi-name">विश्वास नेत्र</span>
    </div>
    
    <div class="container">
        <div class="header">
            <div class="verdict-icon">{verdict_icon}</div>
            <div class="verdict-text">{verdict.replace('_', ' ')}</div>
            <div class="confidence">Confidence: {confidence:.1%}</div>
        </div>
        
        <div class="content">
            <!-- Warnings -->
            {"".join([f'<div class="warning">⚠️ {w}</div>' for w in warnings])}
            
            <!-- Explanation -->
            <div class="section">
                <div class="section-title">📝 Analysis</div>
                <div class="explanation">{explanation}</div>
            </div>
            
            <!-- Temporal Status -->
            {f'''
            <div class="section">
                <div class="section-title">⏰ Time Verification</div>
                <p><span class="badge badge-{temporal_status.lower()}">{temporal_status}</span></p>
                {f'<p style="margin-top: 10px; color: #374151;">{time_verification}</p>' if time_verification else ''}
            </div>
            ''' if temporal_status != "UNCLEAR" else ''}
            
            <!-- Key Evidence -->
            {f'''
            <div class="section">
                <div class="section-title">🔍 Key Evidence</div>
                <ul class="evidence-list">
                    {"".join([f"<li>{ev}</li>" for ev in key_evidence[:5]])}
                </ul>
            </div>
            ''' if key_evidence else ''}
            
            <!-- Sources -->
            {f'''
            <div class="section">
                <div class="section-title">📚 Sources</div>
                <ul class="sources-list">
                    {"".join([f"<li>{src}</li>" for src in sources[:5]])}
                </ul>
            </div>
            ''' if sources else ''}
            
            <!-- Social Media Perspective -->
            {f'''
            <div class="section">
                <div class="section-title">🐦 Social Media Consensus</div>
                <div class="social-media">
                    {social_perspective}
                </div>
            </div>
            ''' if social_perspective else ''}
            
            <!-- Deepfake Detection -->
            {f'''
            <div class="section">
                <div class="section-title">🎬 Media Analysis</div>
                <div class="explanation">
                    <strong>Deepfake Detected:</strong> {'Yes ⚠️' if media_analysis.get('is_deepfake') else 'No ✓'}<br>
                    <strong>Authenticity Score:</strong> {media_analysis.get('authenticity_score', 0):.1%}
                </div>
            </div>
            ''' if media_analysis else ''}
        </div>
        
        <div class="meta">
            <div class="meta-item">
                <span class="meta-label">Report ID</span>
                <span class="meta-value">{report.get('report_id', 'N/A')}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Generated</span>
                <span class="meta-value">{datetime.fromisoformat(report.get('generated_at', datetime.now().isoformat())).strftime('%b %d, %Y %H:%M')}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Web Sources</span>
                <span class="meta-value">{web_sources} verified</span>
            </div>
        </div>
        
        <div class="footer">
            <button class="share-button" onclick="copyLink()">📋 Copy Share Link</button>
            <div class="footer-brand" style="margin-top: 20px;">
                <span>👁️</span>
                <span>Vishwas Netra</span>
                <span style="color: #a67c52;">विश्वास नेत्र</span>
            </div>
            <p class="footer-tagline">Empowering Truth, Exposing Falsehood</p>
        </div>
    </div>
    
    <script>
        function copyLink() {{
            navigator.clipboard.writeText(window.location.href).then(() => {{
                const btn = document.querySelector('.share-button');
                btn.textContent = '✅ Link Copied!';
                setTimeout(() => {{
                    btn.textContent = '📋 Copy Share Link';
                }}, 2000);
            }});
        }}
    </script>
</body>
</html>
    """
    
    return html


if __name__ == "__main__":
    print("🚀 Starting Misinformation Detection API Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
