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
🔍 **Welcome to Misinformation Detector Bot!**

I'm like Grok on Twitter, but for Telegram. I can analyze:

📝 **Text** - Send me any claim to fact-check
🖼️ **Images** - Check if AI-generated or deepfake
🎥 **Videos** - Detect manipulated content
🎵 **Audio** - Identify AI voice clones & transcribe

**How to use:**
1. Send me text, image, video, or audio
2. I'll analyze it using AI + web search + social media
3. Get instant verdict with detailed report

**Features:**
✅ Gemini AI fact-checking
✅ Web search (15+ sources)
✅ Twitter consensus
✅ AI-generated media detection
✅ OCR & transcription
✅ Educational explanations

Try sending me something to check! 🚀
"""
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for fact-checking."""
    text = update.message.text
    
    # Send thinking message
    thinking_msg = await update.message.reply_text("🔍 Analyzing your claim...\n⏳ This may take a few moments...")
    
    try:
        # Run orchestrator
        result = orchestrator.run(
            user_input=text,
            content_type="text"
        )
        
        # Format response
        response = format_text_result(result)
        
        # Create inline keyboard for detailed report
        keyboard = None
        if result.get('report_id'):
            report_url = f"http://localhost:8000/report/{result['report_id']}"
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
        await thinking_msg.edit_text(f"❌ Error analyzing text: {str(e)}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image messages for AI detection and OCR."""
    # Send thinking message
    thinking_msg = await update.message.reply_text("🖼️ Analyzing image...\n⏳ Running AI detection + OCR...")
    
    try:
        # Get largest photo size
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Download to temp file
        temp_path = UPLOAD_DIR / f"telegram_{photo.file_id}.jpg"
        await file.download_to_drive(temp_path)
        
        # Run orchestrator
        result = orchestrator.run(
            user_input="Image analysis",
            file_path=str(temp_path),
            content_type="image"
        )
        
        # Format response
        response = format_image_result(result)
        
        # Create inline keyboard
        keyboard = None
        if result.get('report_id'):
            report_url = f"http://localhost:8000/report/{result['report_id']}"
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
        
        # Run orchestrator
        result = orchestrator.run(
            user_input="Video analysis",
            file_path=str(temp_path),
            content_type="video"
        )
        
        # Format response
        response = format_video_result(result)
        
        # Create inline keyboard
        keyboard = None
        if result.get('report_id'):
            report_url = f"http://localhost:8000/report/{result['report_id']}"
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
        "🎵 Analyzing audio...\n⏳ Running AI voice detection + transcription..."
    )
    
    try:
        file = await context.bot.get_file(audio_obj.file_id)
        
        # Download to temp file
        ext = ".ogg" if is_voice else ".mp3"
        temp_path = UPLOAD_DIR / f"telegram_{audio_obj.file_id}{ext}"
        await file.download_to_drive(temp_path)
        
        # Run orchestrator
        result = orchestrator.run(
            user_input="Audio analysis",
            file_path=str(temp_path),
            content_type="audio"
        )
        
        # Format response
        response = format_audio_result(result)
        
        # Create inline keyboard
        keyboard = None
        if result.get('report_id'):
            report_url = f"http://localhost:8000/report/{result['report_id']}"
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
    """Format text fact-checking result for Telegram."""
    verdict = result.get('verdict', 'UNCERTAIN')
    confidence = result.get('confidence', 0)
    
    # Emoji based on verdict
    emoji_map = {
        'TRUE': '✅',
        'FALSE': '❌',
        'MISLEADING': '⚠️',
        'UNCERTAIN': '🤔',
        'UNVERIFIABLE': '❓'
    }
    emoji = emoji_map.get(verdict, '🤔')
    
    response = f"**{emoji} Fact-Check Result**\n\n"
    response += f"**Verdict:** {verdict}\n"
    response += f"**Confidence:** {confidence:.0%}\n\n"
    
    # Add explanation
    if result.get('explanation'):
        explanation = result['explanation'][:500]  # Limit length
        response += f"**Analysis:**\n{explanation}\n\n"
    
    # Add sources count
    fact_check = result.get('fact_check', {})
    if fact_check.get('sources'):
        source_count = len(fact_check['sources'])
        response += f"📚 Checked against {source_count} sources\n"
    
    # Add Twitter consensus
    if result.get('twitter_consensus'):
        response += f"🐦 Social Media: {result['twitter_consensus']}\n"
    
    response += f"\n💡 _Tap 'View Detailed Report' for full analysis_"
    
    return response


def format_image_result(result: dict) -> str:
    """Format image analysis result for Telegram."""
    media_analysis = result.get('stages', {}).get('media_analysis', {})
    deepfake_result = media_analysis.get('deepfake_result', {})
    
    is_deepfake = deepfake_result.get('is_deepfake', False)
    confidence = deepfake_result.get('confidence', 0)
    
    emoji = '❌' if is_deepfake else '✅'
    status = 'AI-GENERATED' if is_deepfake else 'AUTHENTIC'
    
    response = f"**{emoji} Image Analysis**\n\n"
    response += f"**Status:** {status}\n"
    response += f"**Confidence:** {confidence:.0%}\n\n"
    
    # Add OCR text if available
    ocr_text = deepfake_result.get('ocr_text', '')
    if ocr_text:
        word_count = len(ocr_text.split())
        response += f"**Extracted Text:** ({word_count} words)\n"
        response += f"_{ocr_text[:200]}..._\n\n" if len(ocr_text) > 200 else f"_{ocr_text}_\n\n"
        
        # Add fact-check if OCR had enough content
        if word_count >= 10 and result.get('verdict'):
            response += f"**Text Verdict:** {result['verdict']}\n"
    
    response += f"\n💡 _Tap 'View Detailed Report' for full analysis_"
    
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
    """Format audio analysis result for Telegram."""
    media_analysis = result.get('stages', {}).get('media_analysis', {})
    deepfake_result = media_analysis.get('deepfake_result', {})
    
    is_deepfake = deepfake_result.get('is_deepfake', False)
    confidence = deepfake_result.get('confidence', 0)
    
    emoji = '❌' if is_deepfake else '✅'
    status = 'AI VOICE DETECTED' if is_deepfake else 'AUTHENTIC'
    
    response = f"**{emoji} Audio Analysis**\n\n"
    response += f"**Status:** {status}\n"
    response += f"**Confidence:** {confidence:.0%}\n\n"
    
    # Add transcription
    transcribed_text = deepfake_result.get('transcribed_text', '')
    if transcribed_text:
        word_count = len(transcribed_text.split())
        response += f"**Transcription:** ({word_count} words)\n"
        response += f"_{transcribed_text[:300]}..._\n\n" if len(transcribed_text) > 300 else f"_{transcribed_text}_\n\n"
        
        # Add fact-check if transcription had enough content
        if word_count >= 10 and result.get('verdict'):
            response += f"**Fact-Check Verdict:** {result['verdict']}\n"
            if result.get('confidence'):
                response += f"**Confidence:** {result['confidence']:.0%}\n"
    
    response += f"\n💡 _Tap 'View Detailed Report' for full analysis_"
    
    return response


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    help_text = """
🔍 **How to Use This Bot**

**Send me:**
📝 Text - Any claim you want fact-checked
🖼️ Image - Check if AI-generated + extract text
🎥 Video - Detect deepfakes and manipulation
🎵 Audio/Voice - Detect AI voices + transcribe

**What I check:**
✅ AI-generated media detection
✅ Gemini AI fact-checking
✅ Web search across 15+ sources
✅ Twitter/social media consensus
✅ OCR text extraction
✅ Audio transcription
✅ Educational explanations

**Commands:**
/start - Show welcome message
/help - Show this help message

**Powered by:**
🤖 Google Gemini AI
🔍 Web Search
🐦 Twitter API
🎯 Custom ML models
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
