"""
Telegram Bot for Misinformation Detection
Like Grok on Twitter, but for Telegram - instant fact-checking and media analysis
"""
import os
import asyncio
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Import your existing backend
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orchestrator_agent.orchestrator_tool import OrchestratorTool
import re
from typing import Optional

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Base URL for reports (use ngrok/public URL in production, or None for local)
# Telegram doesn't accept localhost URLs in inline keyboards
BASE_URL = os.getenv('BASE_URL', None)  # Set BASE_URL in .env for production (e.g., https://your-domain.com)

# Initialize orchestrator
orchestrator = OrchestratorTool()

# Ensure upload directory exists
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def extract_youtube_transcript(url: str) -> Optional[str]:
    """Extract transcript from YouTube video"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start is issued."""
    welcome_text = """
🛡️ **Welcome to Vishwas Netra Bot!**

*विश्वास का नेत्र - Your Truth Guardian*

I can analyze ANY content for misinformation:

📝 **Text & YouTube URLs**
   • Fact-check claims with 30+ web sources
   • Extract & verify YouTube video transcripts
   • Google News + Reddit + Twitter consensus
   • Detect misinformation patterns

🖼️ **Images**
   • AI-generated image detection (deepfake)
   • OCR text extraction & fact-checking
   • Source verification

🎥 **Videos**
   • Deepfake video detection
   • Frame-by-frame analysis
   • Content fact-checking

🎵 **Audio & Voice Messages**
   • AI voice clone detection
   • Speech-to-text transcription
   • Fact-check transcribed content

**📊 What You Get:**
✅ Verdict: TRUE/FALSE/MISLEADING
✅ Confidence score (0-100%)
✅ Detailed explanation
✅ Source citations
✅ Shareable HTML report

**⚡ Quick Start:**
Just send me something - I'll figure out what to do!

*Powered by Gemini 2.0 + Advanced ML Models*
"""
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for fact-checking."""
    text = update.message.text
    
    # Ignore short messages
    if len(text) < 10:
        await update.message.reply_text("⚠️ Please send a longer claim (at least 10 characters) for fact-checking.")
        return
    
    # Check if it's a YouTube URL
    is_youtube = "youtube.com" in text or "youtu.be" in text
    
    if is_youtube:
        # Send thinking message for YouTube
        thinking_msg = await update.message.reply_text(
            "🎥 **Analyzing YouTube Video...**\n\n"
            "⏳ Step 1/3: Extracting transcript...\n"
            "⏳ Step 2/3: Checking 30+ sources...\n"
            "⏳ Step 3/3: Verifying claims...",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Send thinking message for text
        thinking_msg = await update.message.reply_text(
            "🔍 **Fact-Checking Your Claim...**\n\n"
            "⏳ Step 1/3: Searching Google News...\n"
            "⏳ Step 2/3: Checking 30+ web sources...\n"
            "⏳ Step 3/3: Analyzing social media...",
            parse_mode=ParseMode.MARKDOWN
        )
    
    try:
        # Handle YouTube URLs
        original_text = text
        if is_youtube:
            transcript = extract_youtube_transcript(text)
            if transcript:
                text = f"YouTube Video Transcript:\n{transcript}"
            else:
                await thinking_msg.edit_text(
                    "❌ **Could not extract YouTube transcript**\n\n"
                    "This might happen if:\n"
                    "• Video has no captions/subtitles\n"
                    "• Captions are disabled\n"
                    "• Video is private/restricted\n\n"
                    "Try sending the video title or description instead.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
        
        # Run orchestrator (same as API server)
        result = orchestrator.run(
            user_input=text,
            content_type="text"
        )
        
        # Generate report ID and save (same as API server)
        import hashlib
        report_id = hashlib.md5(text.encode()).hexdigest()[:16]
        
        # Save report
        from datetime import datetime
        import json
        report_data = {
            **result,
            'report_id': report_id,
            'generated_at': datetime.now().isoformat(),
            'original_content': text,
            'youtube_url': original_text if is_youtube else None
        }
        
        # Save to reports directory
        REPORTS_DIR = Path("data/reports")
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(REPORTS_DIR / f"{report_id}.json", 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Format response with detailed context (same as API server)
        response = format_text_result(result)
        
        # Add report link
        keyboard = None
        if BASE_URL:
            report_url = f"{BASE_URL}/report/{report_id}"
            response += f"\n\n📊 Detailed Report:\n`{report_url}`"
        else:
            response += f"\n\n📊 Report: `http://localhost:8000/report/{report_id}`\n_(Start API server to view)_"
        
        # Try to delete thinking message, but don't fail if it's already gone
        try:
            await thinking_msg.delete()
        except:
            pass  # Message might already be deleted or too old
        
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        
    except Exception as e:
        error_msg = f"❌ **Error Analyzing Text**\n\n"
        error_msg += f"Details: {str(e)[:200]}\n\n"
        error_msg += "💡 *Try:*\n"
        error_msg += "• Simplifying your claim\n"
        error_msg += "• Sending it again\n"
        error_msg += "• Using /help for guidance"
        try:
            await thinking_msg.edit_text(error_msg, parse_mode=ParseMode.MARKDOWN)
        except:
            await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image messages for AI detection and OCR."""
    # Send thinking message with progress
    thinking_msg = await update.message.reply_text(
        "🖼️ **Analyzing Image...**\n\n"
        "⏳ Step 1/3: Detecting AI-generated content...\n"
        "⏳ Step 2/3: Extracting text (OCR)...\n"
        "⏳ Step 3/3: Fact-checking content...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        # Get largest photo size
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Download to temp file
        temp_path = UPLOAD_DIR / f"telegram_{photo.file_id}.jpg"
        await file.download_to_drive(temp_path)
        
        # Run orchestrator (same as API server)
        result = orchestrator.run(
            user_input="Analyze this image for deepfakes and verify content accuracy",
            file_path=str(temp_path),
            content_type="image"
        )
        
        # Generate report ID and save
        import hashlib
        from datetime import datetime
        import json
        report_id = hashlib.md5(f"{photo.file_id}{datetime.now().timestamp()}".encode()).hexdigest()[:16]
        
        # Save report
        report_data = {
            **result,
            'report_id': report_id,
            'generated_at': datetime.now().isoformat(),
            'media_type': 'image',
            'filename': f"telegram_{photo.file_id}.jpg"
        }
        
        REPORTS_DIR = Path("data/reports")
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(REPORTS_DIR / f"{report_id}.json", 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Format response with detailed context
        response = format_image_result(result)
        
        # Add report link
        keyboard = None
        if BASE_URL:
            report_url = f"{BASE_URL}/report/{report_id}"
            response += f"\n\n📊 Detailed Report:\n`{report_url}`"
        else:
            response += f"\n\n📊 Report: `http://localhost:8000/report/{report_id}`\n_(Start API server to view)_"
        
        # Send result
        try:
            await thinking_msg.delete()
        except:
            pass
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
            
    except Exception as e:
        try:
            await thinking_msg.edit_text(f"❌ Error analyzing image: {str(e)}")
        except:
            await update.message.reply_text(f"❌ Error analyzing image: {str(e)}")


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video messages for deepfake detection."""
    thinking_msg = await update.message.reply_text("🎥 Analyzing video...\n⏳ Running deepfake detection...")
    
    try:
        video = update.message.video
        file = await context.bot.get_file(video.file_id)
        
        # Download to temp file
        temp_path = UPLOAD_DIR / f"telegram_{video.file_id}.mp4"
        await file.download_to_drive(temp_path)
        
        # Run orchestrator (same as API server)
        result = orchestrator.run(
            user_input="Analyze this video for deepfakes and verify content accuracy",
            file_path=str(temp_path),
            content_type="video"
        )
        
        # Generate report ID and save
        import hashlib
        from datetime import datetime
        import json
        report_id = hashlib.md5(f"{video.file_id}{datetime.now().timestamp()}".encode()).hexdigest()[:16]
        
        report_data = {
            **result,
            'report_id': report_id,
            'generated_at': datetime.now().isoformat(),
            'media_type': 'video',
            'filename': f"telegram_{video.file_id}.mp4"
        }
        
        REPORTS_DIR = Path("data/reports")
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(REPORTS_DIR / f"{report_id}.json", 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Format response
        response = format_video_result(result)
        
        # Add report link
        keyboard = None
        if BASE_URL:
            report_url = f"{BASE_URL}/report/{report_id}"
            response += f"\n\n📊 Detailed Report:\n`{report_url}`"
        else:
            response += f"\n\n📊 Report: `http://localhost:8000/report/{report_id}`\n_(Start API server to view)_"
        
        # Try to delete thinking message
        try:
            await thinking_msg.delete()
        except:
            pass
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
            
    except Exception as e:
        try:
            await thinking_msg.edit_text(f"❌ Error analyzing video: {str(e)}")
        except:
            await update.message.reply_text(f"❌ Error analyzing video: {str(e)}")


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio/voice messages for deepfake detection and transcription."""
    # Determine if it's voice or audio file
    is_voice = update.message.voice is not None
    audio_obj = update.message.voice if is_voice else update.message.audio
    
    thinking_msg = await update.message.reply_text(
        "🎵 **Analyzing Audio...**\n\n"
        "⏳ Step 1/3: Detecting AI voice cloning...\n"
        "⏳ Step 2/3: Transcribing speech...\n"
        "⏳ Step 3/3: Fact-checking content...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        file = await context.bot.get_file(audio_obj.file_id)
        
        # Download to temp file
        ext = ".ogg" if is_voice else ".mp3"
        temp_path = UPLOAD_DIR / f"telegram_{audio_obj.file_id}{ext}"
        await file.download_to_drive(temp_path)
        
        # Run orchestrator (same as API server)
        result = orchestrator.run(
            user_input="Analyze this audio for AI voice cloning and verify content accuracy",
            file_path=str(temp_path),
            content_type="audio"
        )
        
        # Generate report ID and save
        import hashlib
        from datetime import datetime
        import json
        
        audio_file = update.message.voice or update.message.audio
        file_id = audio_file.file_id
        report_id = hashlib.md5(f"{file_id}{datetime.now().timestamp()}".encode()).hexdigest()[:16]
        
        report_data = {
            **result,
            'report_id': report_id,
            'generated_at': datetime.now().isoformat(),
            'media_type': 'audio',
            'filename': f"telegram_{file_id}.ogg"
        }
        
        REPORTS_DIR = Path("data/reports")
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(REPORTS_DIR / f"{report_id}.json", 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Format response
        response = format_audio_result(result)
        
        # Add report link
        keyboard = None
        if BASE_URL:
            report_url = f"{BASE_URL}/report/{report_id}"
            response += f"\n\n📊 Detailed Report:\n`{report_url}`"
        else:
            response += f"\n\n📊 Report: `http://localhost:8000/report/{report_id}`\n_(Start API server to view)_"
        
        # Try to delete thinking message
        try:
            await thinking_msg.delete()
        except:
            pass
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
            
    except Exception as e:
        try:
            await thinking_msg.edit_text(f"❌ Error analyzing audio: {str(e)}")
        except:
            await update.message.reply_text(f"❌ Error analyzing audio: {str(e)}")


def format_text_result(result: dict) -> str:
    """Format text fact-checking result for Telegram - concise version."""
    fact_check = result.get("stages", {}).get("fact_check", {})
    
    verdict = fact_check.get("verdict", "UNCERTAIN")
    confidence = fact_check.get("confidence", 0.0)
    explanation = fact_check.get("explanation", "No explanation available.")
    sources = fact_check.get("sources", [])
    
    # Emoji based on verdict
    emoji_map = {
        'TRUE': '✅',
        'FALSE': '❌',
        'PARTIALLY_TRUE': '⚠️',
        'UNCERTAIN': '🤔',
        'OUTDATED_INFO': '⏰',
        'UNVERIFIABLE': '❓'
    }
    emoji = emoji_map.get(verdict, '🤔')
    
    # Build concise response
    response = f"{emoji} **{verdict.replace('_', ' ')}** ({confidence:.0%} confidence)\n\n"
    
    # Short explanation (max 250 chars)
    response += f"{explanation[:250]}{'...' if len(explanation) > 250 else ''}\n\n"
    
    # Sources summary
    if sources:
        response += f"📚 Sources: {', '.join(sources[:2])}{'...' if len(sources) > 2 else ''}\n"
    
    return response


def format_image_result(result: dict) -> str:
    """Format image analysis result for Telegram - concise version."""
    media_analysis = result.get('stages', {}).get('media_analysis', {})
    fact_check = result.get('stages', {}).get('fact_check', {})
    
    image_deepfake = media_analysis.get('image_deepfake', {})
    is_deepfake = image_deepfake.get('is_manipulated', False)
    deepfake_confidence = image_deepfake.get('confidence', 0.0)
    
    ocr_data = media_analysis.get('ocr', {})
    ocr_text = ocr_data.get('extracted_text', '')
    
    content_verdict = fact_check.get('verdict', 'UNCERTAIN')
    content_confidence = fact_check.get('confidence', 0.0)
    
    emoji = '❌' if is_deepfake else '✅'
    status = 'AI-GENERATED' if is_deepfake else 'AUTHENTIC'
    
    response = f"🖼️ {emoji} **{status}** ({deepfake_confidence:.0%})\n\n"
    
    # OCR text if available
    if ocr_text:
        response += f"📝 Text: _{ocr_text[:150]}..._\n\n" if len(ocr_text) > 150 else f"📝 Text: _{ocr_text}_\n\n"
        
        if len(ocr_text.split()) >= 10:
            verdict_emoji = {'TRUE': '✅', 'FALSE': '❌', 'PARTIALLY_TRUE': '⚠️'}.get(content_verdict, '🤔')
            response += f"{verdict_emoji} Content: **{content_verdict}** ({content_confidence:.0%})\n"
    
    return response


def format_video_result(result: dict) -> str:
    """Format video analysis result for Telegram - concise version."""
    media_analysis = result.get('stages', {}).get('media_analysis', {})
    deepfake_result = media_analysis.get('video_deepfake', {}) or media_analysis.get('deepfake_result', {})
    
    is_deepfake = deepfake_result.get('is_deepfake', False)
    confidence = deepfake_result.get('confidence', 0.0)
    
    emoji = '❌' if is_deepfake else '✅'
    status = 'DEEPFAKE' if is_deepfake else 'AUTHENTIC'
    
    response = f"🎥 {emoji} **{status}** ({confidence:.0%})\n"
    
    return response


def format_audio_result(result: dict) -> str:
    """Format audio analysis result for Telegram - concise version."""
    media_analysis = result.get('stages', {}).get('media_analysis', {})
    fact_check = result.get('stages', {}).get('fact_check', {})
    
    audio_deepfake = media_analysis.get('audio_deepfake', {})
    is_ai_voice = audio_deepfake.get('is_deepfake', False)
    voice_confidence = audio_deepfake.get('confidence', 0.0)
    
    transcription_data = media_analysis.get('transcription', {})
    transcribed_text = transcription_data.get('transcribed_text', '')
    
    content_verdict = fact_check.get('verdict', 'UNCERTAIN')
    content_confidence = fact_check.get('confidence', 0.0)
    
    emoji = '❌' if is_ai_voice else '✅'
    status = 'AI VOICE' if is_ai_voice else 'AUTHENTIC'
    
    response = f"🎙️ {emoji} **{status}** ({voice_confidence:.0%})\n\n"
    
    if transcribed_text:
        response += f"📝 _{transcribed_text[:200]}..._\n\n" if len(transcribed_text) > 200 else f"📝 _{transcribed_text}_\n\n"
        
        if len(transcribed_text.split()) >= 10:
            verdict_emoji = {'TRUE': '✅', 'FALSE': '❌', 'PARTIALLY_TRUE': '⚠️'}.get(content_verdict, '🤔')
            response += f"{verdict_emoji} Content: **{content_verdict}** ({content_confidence:.0%})\n"
    
    return response


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    help_text = """
🔍 **Vishwas Netra Bot - User Guide**

**📝 Text Fact-Checking**
Send any claim:
• "Modi banned 10 rupee notes"
• "COVID vaccine contains microchips"
• "Earth is flat"

I'll check 30+ sources and give you a verdict!

**🖼️ Image Analysis**
Send any image:
• Screenshots of viral posts
• Forwarded images
• Memes with text

I'll detect AI-generation & extract text for fact-checking!

**🎥 Video Analysis**
Send videos up to 50MB:
• Deepfake detection
• Content verification
• Frame analysis

**🎵 Audio/Voice Analysis**
Send audio or voice messages:
• AI voice clone detection
• Speech transcription
• Fact-check spoken claims

**📊 What You Get:**
✅ Verdict (TRUE/FALSE/MISLEADING)
✅ Confidence score
✅ Detailed explanation
✅ Multiple sources checked
✅ Social media consensus
✅ Shareable report link

**⚡ Commands:**
/start - Welcome message
/help - This help message

**🛠️ Tech Stack:**
• Gemini 2.0 Flash Exp AI
• Google News API
• Reddit + Twitter analysis
• Advanced ML models
• 30+ web sources

**💡 Tips:**
• Longer claims = better analysis
• Clear images work best
• Audio quality matters
• Wait for full analysis (10-30 sec)

*Built with ❤️ for truth*
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    print(f"Update {update} caused error {context.error}")


def main():
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file!")
        return
    
    print("🤖 Starting Telegram Misinformation Detector Bot...")
    print(f"📱 Bot Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, handle_audio))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    print("✅ Bot is running! Send messages to your bot on Telegram.")
    print("Press Ctrl+C to stop the bot")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
