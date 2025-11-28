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

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Initialize orchestrator
orchestrator = OrchestratorTool()

# Ensure upload directory exists
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start is issued."""
    welcome_text = """
🛡️ **Welcome to Vishwas Netra Bot!**

*विश्वास का नेत्र - Your Truth Guardian*

I can analyze ANY content for misinformation:

📝 **Text Messages**
   • Fact-check claims with 30+ web sources
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
    
    # Send thinking message with progress
    thinking_msg = await update.message.reply_text(
        "🔍 **Fact-Checking Your Claim...**\n\n"
        "⏳ Step 1/3: Searching Google News...\n"
        "⏳ Step 2/3: Checking 30+ web sources...\n"
        "⏳ Step 3/3: Analyzing social media...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
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
            'original_content': text
        }
        
        # Save to reports directory
        REPORTS_DIR = Path("data/reports")
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(REPORTS_DIR / f"{report_id}.json", 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Format response with detailed context (same as API server)
        response = format_text_result(result)
        
        # Create inline keyboard for detailed report
        report_url = f"http://localhost:8000/report/{report_id}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📊 View Detailed Report", url=report_url)
        ]])
        
        # Delete thinking message and send result
        await thinking_msg.delete()
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
        await thinking_msg.edit_text(error_msg, parse_mode=ParseMode.MARKDOWN)


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
        
        # Create inline keyboard
        report_url = f"http://localhost:8000/report/{report_id}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📊 View Detailed Report", url=report_url)
        ]])
        
        # Send result
        await thinking_msg.delete()
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
            
    except Exception as e:
        await thinking_msg.edit_text(f"❌ Error analyzing image: {str(e)}")


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
        
        # Create inline keyboard
        report_url = f"http://localhost:8000/report/{report_id}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📊 View Detailed Report", url=report_url)
        ]])
        
        await thinking_msg.delete()
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
            
    except Exception as e:
        await thinking_msg.edit_text(f"❌ Error analyzing video: {str(e)}")


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
        
        # Create inline keyboard
        report_url = f"http://localhost:8000/report/{report_id}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📊 View Detailed Report", url=report_url)
        ]])
        
        await thinking_msg.delete()
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
            
    except Exception as e:
        await thinking_msg.edit_text(f"❌ Error analyzing audio: {str(e)}")


def format_text_result(result: dict) -> str:
    """Format text fact-checking result for Telegram with full context (API server logic)."""
    # Extract fact-check data (same structure as API server)
    fact_check = result.get("stages", {}).get("fact_check", {})
    
    verdict = fact_check.get("verdict", "UNCERTAIN")
    confidence = fact_check.get("confidence", 0.0)
    temporal_status = fact_check.get("temporal_status", "UNCLEAR")
    time_verification = fact_check.get("time_verification", "")
    explanation = fact_check.get("explanation", "No explanation available.")
    key_evidence = fact_check.get("key_evidence", [])
    sources = fact_check.get("sources", [])
    warnings = fact_check.get("warnings", [])
    web_sources = fact_check.get("web_sources_found", 0)
    news_articles = fact_check.get("news_articles_found", 0)
    social_perspective = fact_check.get("social_media_perspective", "")
    
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
    
    # Build comprehensive response
    response = f"**{emoji} FACT-CHECK RESULT**\n\n"
    response += f"**Verdict:** {verdict.replace('_', ' ')}\n"
    response += f"**Confidence:** {confidence:.0%}\n\n"
    
    # Warnings (if any)
    if warnings:
        response += "⚠️ **Warnings:**\n"
        for warning in warnings[:2]:  # Limit to 2 warnings
            response += f"• {warning}\n"
        response += "\n"
    
    # Temporal status
    if temporal_status != "UNCLEAR":
        temporal_emoji = {"CURRENT": "🕒", "OUTDATED": "⏰", "HISTORICAL": "📜"}.get(temporal_status, "⏰")
        response += f"{temporal_emoji} **Time Status:** {temporal_status}\n"
        if time_verification:
            response += f"_{time_verification[:150]}_\n\n"
    
    # Main explanation
    response += f"📝 **Analysis:**\n{explanation[:600]}\n\n"  # Limit to 600 chars
    
    # Key evidence (top 3)
    if key_evidence:
        response += "🔍 **Key Evidence:**\n"
        for i, evidence in enumerate(key_evidence[:3], 1):
            response += f"{i}. {evidence[:120]}\n"
        response += "\n"
    
    # Sources summary
    if sources or web_sources > 0:
        response += "📚 **Sources Checked:**\n"
        if news_articles > 0:
            response += f"• {news_articles} Google News articles\n"
        if web_sources > 0:
            response += f"• {web_sources} web sources verified\n"
        if sources:
            response += f"• Top sources: {', '.join(sources[:3])}\n"
        response += "\n"
    
    # Social media perspective
    if social_perspective:
        response += f"🐦 **Social Media:**\n{social_perspective[:200]}\n\n"
    
    response += "💡 _Tap 'View Detailed Report' for complete analysis with all sources_"
    
    return response


def format_image_result(result: dict) -> str:
    """Format image analysis result for Telegram with full context (API server logic)."""
    # Extract media analysis (same as API server)
    media_analysis = result.get('stages', {}).get('media_analysis', {})
    fact_check = result.get('stages', {}).get('fact_check', {})
    
    # Deepfake detection
    image_deepfake = media_analysis.get('image_deepfake', {})
    is_deepfake = image_deepfake.get('is_manipulated', False)
    deepfake_confidence = image_deepfake.get('confidence', 0.0)
    deepfake_explanation = image_deepfake.get('explanation', 'No analysis available')
    
    # OCR results
    ocr_data = media_analysis.get('ocr', {})
    ocr_text = ocr_data.get('extracted_text', '')
    
    # Content fact-check (if OCR text was analyzed)
    content_verdict = fact_check.get('verdict', 'UNCERTAIN')
    content_confidence = fact_check.get('confidence', 0.0)
    content_explanation = fact_check.get('explanation', '')
    
    # Build response
    emoji = '❌' if is_deepfake else '✅'
    status = 'AI-GENERATED / DEEPFAKE' if is_deepfake else 'AUTHENTIC IMAGE'
    
    response = f"**{emoji} IMAGE ANALYSIS REPORT**\n\n"
    
    # Overall assessment
    if is_deepfake and content_verdict == 'FALSE':
        response += "⚠️ **DOUBLE ALERT:** Image is AI-GENERATED and content is FALSE!\n\n"
    elif is_deepfake and content_verdict == 'TRUE':
        response += "⚠️ **MIXED RESULT:** Image is fake but claims are TRUE.\n\n"
    elif is_deepfake:
        response += "⚠️ **DEEPFAKE DETECTED:** Image authenticity questionable.\n\n"
    elif content_verdict == 'FALSE':
        response += "❌ **FALSE CONTENT:** Image is real but claims are FALSE.\n\n"
    else:
        response += "✅ **VERIFIED:** Image appears authentic.\n\n"
    
    # Deepfake analysis
    response += f"🎨 **Media Authenticity:**\n"
    response += f"Status: {status}\n"
    response += f"Confidence: {deepfake_confidence:.0%}\n"
    response += f"_{deepfake_explanation[:200]}_\n\n"
    
    # OCR extracted text
    if ocr_text:
        word_count = len(ocr_text.split())
        response += f"📝 **Extracted Text:** ({word_count} words)\n"
        response += f"_{ocr_text[:300]}..._\n\n" if len(ocr_text) > 300 else f"_{ocr_text}_\n\n"
        
        # Content fact-check
        if word_count >= 10 and content_explanation:
            content_emoji = {'TRUE': '✅', 'FALSE': '❌', 'PARTIALLY_TRUE': '⚠️'}.get(content_verdict, '🤔')
            response += f"{content_emoji} **Text Content Verdict:** {content_verdict}\n"
            response += f"Confidence: {content_confidence:.0%}\n"
            response += f"_{content_explanation[:250]}_\n\n"
    
    response += "💡 _Tap 'View Detailed Report' for complete analysis_"
    
    return response


def format_video_result(result: dict) -> str:
    """Format video analysis result for Telegram."""
    media_analysis = result.get('stages', {}).get('media_analysis', {})
    deepfake_result = media_analysis.get('deepfake_result', {})
    
    is_deepfake = deepfake_result.get('is_deepfake', False)
    confidence = deepfake_result.get('confidence', 0)
    
    emoji = '❌' if is_deepfake else '✅'
    status = 'DEEPFAKE DETECTED' if is_deepfake else 'AUTHENTIC'
    
    response = f"**{emoji} Video Analysis**\n\n"
    response += f"**Status:** {status}\n"
    response += f"**Confidence:** {confidence:.0%}\n\n"
    
    if deepfake_result.get('analysis'):
        response += f"**Details:** {deepfake_result['analysis']}\n"
    
    response += f"\n💡 _Tap 'View Detailed Report' for full analysis_"
    
    return response


def format_audio_result(result: dict) -> str:
    """Format audio analysis result for Telegram with full context (API server logic)."""
    # Extract analysis data
    media_analysis = result.get('stages', {}).get('media_analysis', {})
    fact_check = result.get('stages', {}).get('fact_check', {})
    
    # Audio deepfake detection
    audio_deepfake = media_analysis.get('audio_deepfake', {})
    is_ai_voice = audio_deepfake.get('is_deepfake', False)
    voice_confidence = audio_deepfake.get('confidence', 0.0)
    voice_explanation = audio_deepfake.get('explanation', 'No analysis available')
    
    # Transcription
    transcription_data = media_analysis.get('transcription', {})
    transcribed_text = transcription_data.get('transcribed_text', '')
    
    # Content fact-check (if transcription was analyzed)
    content_verdict = fact_check.get('verdict', 'UNCERTAIN')
    content_confidence = fact_check.get('confidence', 0.0)
    content_explanation = fact_check.get('explanation', '')
    
    # Build response
    emoji = '❌' if is_ai_voice else '✅'
    status = 'AI VOICE CLONE DETECTED' if is_ai_voice else 'AUTHENTIC HUMAN VOICE'
    
    response = f"**{emoji} AUDIO ANALYSIS REPORT**\n\n"
    
    # Overall assessment
    if is_ai_voice and content_verdict == 'FALSE':
        response += "⚠️ **DOUBLE ALERT:** AI voice AND false claims detected!\n\n"
    elif is_ai_voice and content_verdict == 'TRUE':
        response += "⚠️ **MIXED RESULT:** AI voice but claims are TRUE.\n\n"
    elif is_ai_voice:
        response += "⚠️ **AI VOICE DETECTED:** Voice authenticity questionable.\n\n"
    elif content_verdict == 'FALSE':
        response += "❌ **FALSE CONTENT:** Voice is real but claims are FALSE.\n\n"
    else:
        response += "✅ **VERIFIED:** Voice appears authentic.\n\n"
    
    # Voice authenticity
    response += f"🎙️ **Voice Authenticity:**\n"
    response += f"Status: {status}\n"
    response += f"Confidence: {voice_confidence:.0%}\n"
    response += f"_{voice_explanation[:200]}_\n\n"
    
    # Transcription
    if transcribed_text:
        word_count = len(transcribed_text.split())
        response += f"📝 **Transcription:** ({word_count} words)\n"
        response += f"_{transcribed_text[:400]}..._\n\n" if len(transcribed_text) > 400 else f"_{transcribed_text}_\n\n"
        
        # Content fact-check
        if word_count >= 10 and content_explanation:
            content_emoji = {'TRUE': '✅', 'FALSE': '❌', 'PARTIALLY_TRUE': '⚠️'}.get(content_verdict, '🤔')
            response += f"{content_emoji} **Content Verdict:** {content_verdict}\n"
            response += f"Confidence: {content_confidence:.0%}\n"
            response += f"_{content_explanation[:250]}_\n\n"
    
    response += "💡 _Tap 'View Detailed Report' for complete analysis_"
    
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
