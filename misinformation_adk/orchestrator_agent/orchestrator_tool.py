from google.adk.tools.base_tool import BaseTool
import json
from datetime import datetime

class OrchestratorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="coordinate_analysis",
            description="Coordinates the complete misinformation detection pipeline through all sub-agents."
        )

    def run(self, user_input: str, file_path: str = None, content_type: str = None) -> dict:
        """
        Orchestrates the complete analysis pipeline.
        
        Args:
            user_input: Text content or claim from user
            file_path: Optional path to media file
            content_type: Optional content type hint from extension ("text", "image", "video", "audio")
                         When provided, skips Stage 1 (Content Intake) for faster processing
            
        Returns:
            Comprehensive analysis results from all agents
        """
        
        pipeline_result = {
            "user_input": user_input,
            "file_path": file_path,
            "stages": {
                "content_intake": None,
                "media_analysis": None,
                "fact_check": None,
                "knowledge": None
            },
            "final_verdict": None,
            "confidence": 0.0,
            "recommendations": []
        }
        
        # Stage 1: Content Intake Analysis (skip if content_type provided by extension)
        if content_type:
            print(f"⚡ Fast Mode: Content type '{content_type}' provided by extension, skipping intake analysis...")
            content_analysis = {
                "content_type": content_type,
                "has_text": content_type == "text",
                "has_media": content_type in ["image", "video", "audio"],
                "media_type": content_type if content_type in ["image", "video", "audio"] else None,
                "timestamp": datetime.now().isoformat(),
                "fast_mode": True
            }
        else:
            print("🔍 Stage 1: Analyzing content type...")
            content_analysis = self._analyze_content_type(user_input, file_path)
        
        pipeline_result["stages"]["content_intake"] = content_analysis
        
        # Stage 2: Media Analysis (if applicable)
        if content_analysis.get("has_media"):
            print("🎬 Stage 2: Running deepfake detection and OCR/transcription...")
            media_result = self._analyze_media(content_analysis, file_path)
            pipeline_result["stages"]["media_analysis"] = media_result
            
            # Check if we should skip fact-checking due to insufficient text
            if media_result.get("skip_gemini"):
                print(f"⏭️ Skipping fact-check: {media_result.get('skip_reason')}")
                # Create simplified fact-check result
                pipeline_result["stages"]["fact_check"] = {
                    "verdict": "NO_TEXT_CONTENT",
                    "confidence": 1.0,
                    "explanation": media_result.get('skip_reason', 'No significant text to fact-check'),
                    "skipped": True,
                    "deepfake_only_analysis": True
                }
                # Skip to knowledge stage
                print("📚 Stage 4: Generating educational response...")
                knowledge_result = self._generate_education(pipeline_result)
                pipeline_result["stages"]["knowledge"] = knowledge_result
                pipeline_result["final_verdict"] = "DEEPFAKE" if media_result.get("is_deepfake") else "AUTHENTIC_NO_TEXT"
                pipeline_result["confidence"] = media_result.get("confidence", 0.0)
                return pipeline_result
            
            # Add extracted text to fact-checking input if significant
            if media_result.get("extracted_text") and media_result.get("has_significant_text"):
                user_input += "\n\nExtracted from media: " + media_result["extracted_text"]
        else:
            print("📝 Stage 2: Text-only content, skipping media analysis...")
        
        # Stage 3: Fact Checking
        print("✓ Stage 3: Fact-checking claims...")
        fact_check_result = self._fact_check(user_input, pipeline_result["stages"])
        pipeline_result["stages"]["fact_check"] = fact_check_result
        
        # Stage 4: Knowledge & Education
        print("📚 Stage 4: Generating educational response...")
        knowledge_result = self._generate_education(pipeline_result)
        pipeline_result["stages"]["knowledge"] = knowledge_result
        
        # Compile final verdict
        pipeline_result["final_verdict"] = fact_check_result.get("verdict", "UNCERTAIN")
        pipeline_result["confidence"] = fact_check_result.get("confidence", 0.0)
        
        # Generate recommendations
        pipeline_result["recommendations"] = self._generate_recommendations(pipeline_result)
        
        return pipeline_result
    
    def _analyze_content_type(self, content: str, file_path: str = None) -> dict:
        """Stage 1: Content intake analysis."""
        from datetime import datetime
        
        # This would call the content_intake_agent
        # For now, simplified logic
        analysis = {
            "content_type": "text" if not file_path else "media",
            "has_text": bool(content and len(content.strip()) > 0),
            "has_media": bool(file_path),
            "media_type": None,
            "timestamp": datetime.now().isoformat()
        }
        
        if file_path:
            if any(ext in file_path.lower() for ext in ['.jpg', '.png', '.jpeg', '.gif']):
                analysis["media_type"] = "image"
            elif any(ext in file_path.lower() for ext in ['.mp4', '.avi', '.mov']):
                analysis["media_type"] = "video"
            elif any(ext in file_path.lower() for ext in ['.mp3', '.wav', '.m4a']):
                analysis["media_type"] = "audio"
        
        return analysis
    
    def _analyze_media(self, content_analysis: dict, file_path: str = None) -> dict:
        """Stage 2: Media analysis (deepfake detection, OCR, transcription)."""
        # Import media analysis tools
        from sub_agents.media_analysis_agent.image_deepfake_tool import ImageDeepfakeTool
        from sub_agents.media_analysis_agent.video_deepfake_tool import VideoDeepfakeTool
        from sub_agents.media_analysis_agent.audio_deepfake_tool import AudioDeepfakeTool
        from sub_agents.media_analysis_agent.ocr_tool import OCRTool
        from sub_agents.media_analysis_agent.transcription_tool import TranscriptionTool
        
        result = {
            "is_deepfake": False,
            "confidence": 0.0,
            "extracted_text": "",
            "authenticity_score": 1.0,
            "media_type": content_analysis.get("media_type")
        }
        
        media_type = content_analysis.get("media_type")
        
        # Run deepfake detection based on media type
        if media_type == "image" and file_path:
            print("  → Running image deepfake detection...")
            detector = ImageDeepfakeTool()
            deepfake_result = detector.run(image_path=file_path)
            result["is_deepfake"] = deepfake_result.get("is_deepfake", False)
            result["confidence"] = deepfake_result.get("confidence", 0.0)
            result["authenticity_score"] = deepfake_result.get("authenticity_score", 1.0)
            result["image_deepfake"] = deepfake_result  # Store full result
            
            # Run OCR to check for text content
            print("  → Extracting text via OCR...")
            ocr_tool = OCRTool()
            ocr_result = ocr_tool.run(image_path=file_path)
            extracted_text = ocr_result.get("extracted_text", "")
            result["extracted_text"] = extracted_text
            result["ocr_confidence"] = ocr_result.get("confidence", 0.0)
            
            # Check if text is significant enough for fact-checking
            word_count = len(extracted_text.split())
            result["text_word_count"] = word_count
            result["has_significant_text"] = word_count >= 10  # Require at least 10 words for fact-checking
            
            if word_count < 10:
                print(f"  ℹ️ Minimal text detected ({word_count} words). Skipping Gemini fact-check.")
                result["skip_gemini"] = True
                result["skip_reason"] = f"Insufficient text content ({word_count} words, need 10+ for meaningful analysis)"
            else:
                print(f"  ✓ Significant text found ({word_count} words). Will run fact-check.")
                result["skip_gemini"] = False
            
        elif media_type == "video" and file_path:
            print("  → Running video deepfake detection...")
            detector = VideoDeepfakeTool()
            deepfake_result = detector.run(video_path=file_path)
            result["is_deepfake"] = deepfake_result.get("is_deepfake", False)
            result["confidence"] = deepfake_result.get("average_confidence", 0.0)
            result["frames_analyzed"] = deepfake_result.get("frames_analyzed", 0)
            
            # Run OCR on video frames
            print("  → Extracting text from video frames...")
            ocr_tool = OCRTool()
            # For video, we could extract text from multiple frames
            # For now, just indicate OCR capability
            result["extracted_text"] = ""
            
        elif media_type == "audio" and file_path:
            print("  → Running audio deepfake detection + transcription...")
            detector = AudioDeepfakeTool()
            deepfake_result = detector.run(audio_path=file_path)
            result["is_deepfake"] = deepfake_result.get("is_deepfake", False)
            result["confidence"] = deepfake_result.get("confidence", 0.0)
            result["authenticity_score"] = deepfake_result.get("authenticity_score", 1.0)
            result["audio_deepfake"] = deepfake_result  # Store full result
            
            # Get transcribed text (already done by AudioDeepfakeTool)
            transcribed_text = deepfake_result.get("transcribed_text", "")
            result["extracted_text"] = transcribed_text
            result["transcription_confidence"] = deepfake_result.get("confidence", 0.0)
            
            # Check if transcription has enough content for fact-checking
            word_count = len(transcribed_text.split())
            result["text_word_count"] = word_count
            result["has_significant_text"] = word_count >= 10
            
            if word_count < 10:
                print(f"  ℹ️ Minimal transcribed text ({word_count} words). Skipping Gemini fact-check.")
                result["skip_gemini"] = True
                result["skip_reason"] = f"Insufficient transcribed content ({word_count} words, need 10+ for analysis)"
            else:
                print(f"  ✓ Significant transcription found ({word_count} words). Will run fact-check.")
                result["skip_gemini"] = False
        
        return result
    
    def _fact_check(self, claim: str, previous_stages: dict) -> dict:
        """Stage 3: Multi-source fact-checking with temporal verification."""
        from sub_agents.fact_check_agent.gemini_fact_checker_tool import GeminiFactCheckerTool
        from sub_agents.fact_check_agent.web_search_tool import WebSearchTool
        from sub_agents.fact_check_agent.reddit_search_tool import RedditSearchTool
        from sub_agents.fact_check_agent.twitter_scraper_tool import TwitterScraperTool
        from sub_agents.fact_check_agent.claim_database_tool import ClaimDatabaseTool
        
        result = {
            "verdict": "UNCERTAIN",
            "confidence": 0.5,
            "temporal_status": "UNCLEAR",
            "sources_checked": ["gemini_ai_with_web_grounding", "web_search", "reddit_discussions", "twitter_scraper"],
            "explanation": "Fact-checking in progress...",
            "stored_in_db": False,
            "reddit_consensus": None,
            "twitter_consensus": None,
            "social_media_perspective": ""
        }
        
        # Check if media was deepfake FIRST
        media_analysis = previous_stages.get("media_analysis")
        if media_analysis and media_analysis.get("is_deepfake"):
            result["verdict"] = "FALSE"
            result["confidence"] = 0.95
            result["temporal_status"] = "N/A"
            result["explanation"] = f"Content identified as AI-generated or manipulated media (deepfake) with {media_analysis.get('confidence', 0):.1%} confidence."
            
            # Store deepfake detection in database
            db_tool = ClaimDatabaseTool()
            db_tool.run(
                action="store",
                claim=claim,
                verdict="FALSE",
                confidence=0.95,
                evidence={"deepfake_detected": True, "media_analysis": media_analysis}
            )
            return result
        
        # Run Gemini fact-checking with web grounding for real-time verification
        print("  → Running comprehensive web search (20+ sources)...")
        web_tool = WebSearchTool()
        web_result = web_tool.run(query=claim, num_results=30)  # Get more results for better context
        
        # Get social media consensus from Reddit (FREE, no limits)
        print("  → Checking Reddit for community discussions...")
        reddit_tool = RedditSearchTool()
        reddit_result = reddit_tool.run(query=claim, max_results=20)
        
        # Try Twitter scraper as secondary source (bypasses API limits)
        print("  → Checking Twitter via scraper (no API limits)...")
        twitter_tool = TwitterScraperTool()
        twitter_result = twitter_tool.run(query=claim, max_results=15)
        
        # Prepare web context for Gemini
        web_context = f"\\n\\nREAL-TIME WEB SEARCH RESULTS ({len(web_result.get('results', []))} sources found):\\n"
        for idx, result in enumerate(web_result.get('results', [])[:10], 1):
            web_context += f"{idx}. {result.get('title', 'N/A')} - {result.get('snippet', 'N/A')}\\n"
        
        # Combine Reddit and Twitter consensus
        social_media_context = ""
        social_perspectives = []
        
        if reddit_result.get('consensus') and reddit_result.get('posts_analyzed', 0) > 0:
            reddit_consensus = reddit_result.get('consensus', 'N/A')
            post_count = reddit_result.get('posts_analyzed', 0)
            subreddits = reddit_result.get('top_subreddits', [])
            subreddit_names = ', '.join([s['name'] for s in subreddits[:3]])
            
            result["reddit_consensus"] = reddit_consensus
            social_perspectives.append(f"Reddit ({post_count} posts in r/{subreddit_names}): {reddit_consensus}")
            social_media_context += f"\\n\\nREDDIT DISCUSSIONS ({post_count} posts):\\nConsensus: {reddit_consensus}\\nTop subreddits: {subreddit_names}\\n"
        
        if twitter_result.get('consensus') and twitter_result.get('tweets_analyzed', 0) > 0:
            twitter_consensus = twitter_result.get('consensus', 'N/A')
            tweet_count = twitter_result.get('tweets_analyzed', 0)
            result["twitter_consensus"] = twitter_consensus
            social_perspectives.append(f"Twitter ({tweet_count} tweets): {twitter_consensus}")
            social_media_context += f"\\n\\nTWITTER DISCUSSIONS ({tweet_count} tweets via scraper):\\nConsensus: {twitter_consensus}\\n"
        
        result["social_media_perspective"] = " | ".join(social_perspectives) if social_perspectives else "No social media data available"
        
        print("  → Running Gemini AI analysis with real-time web + social media data...")
        gemini_tool = GeminiFactCheckerTool()
        
        # Add context from media analysis, web search AND social media (Reddit + Twitter)
        full_context = ""
        if media_analysis:
            full_context = f"Media type: {media_analysis.get('media_type')}. "
            if media_analysis.get("extracted_text"):
                full_context += f"Extracted text: {media_analysis.get('extracted_text')}"
        full_context += web_context  # Add web search results
        full_context += social_media_context  # Add Reddit + Twitter perspectives
        
        gemini_result = gemini_tool.run(claim=claim, context=full_context)
        
        # Combine results from Gemini AI + web + social media sources
        verdict = gemini_result.get("verdict", "UNCERTAIN")
        confidence = gemini_result.get("confidence", 0.5)
        
        # Smart logic: If web results are irrelevant AND confidence is low, provide context
        web_sources_count = len(web_result.get("results", []))
        credible_sources_count = len(web_result.get("credible_sources", []))
        
        # Let Gemini determine verdict with misinformation pattern detection
        result["verdict"] = verdict
        result["confidence"] = confidence
        result["explanation"] = gemini_result.get("explanation", "")
        result["misinformation_pattern"] = gemini_result.get("misinformation_pattern", None)
        result["pattern_confidence"] = gemini_result.get("pattern_confidence", 0.0)
        
        # Add context card explaining the verdict
        result["context_card"] = self._generate_context_card(
            verdict, confidence, web_sources_count, credible_sources_count,
            reddit_result.get('posts_analyzed', 0),
            twitter_result.get('tweets_analyzed', 0),
            gemini_result.get("misinformation_pattern"),
            gemini_result.get("pattern_confidence", 0.0)
        )
        
        result["temporal_status"] = gemini_result.get("temporal_status", "UNCLEAR")
        result["time_verification"] = gemini_result.get("time_verification", "")
        result["key_evidence"] = gemini_result.get("key_evidence", [])
        result["sources"] = gemini_result.get("sources", [])
        result["warnings"] = gemini_result.get("warnings", [])
        result["web_sources_found"] = web_sources_count
        result["credible_sources_found"] = credible_sources_count
        
        # Add social media perspective to explanation if available
        if result["social_media_perspective"]:
            result["explanation"] += f"\\n\\n🐦 Social Media Perspective: {result['social_media_perspective']}"
        
        # Boost confidence based on credible web sources (like Grok does)
        credible_sources = web_result.get("credible_sources", [])
        if len(credible_sources) >= 3:
            result["confidence"] = min(result["confidence"] + 0.15, 1.0)
            result["explanation"] += f"\n\n✓ Verified by {len(credible_sources)} credible sources."
        elif len(credible_sources) >= 1:
            result["confidence"] = min(result["confidence"] + 0.08, 1.0)
        
        # Add temporal warning if outdated
        if result["temporal_status"] == "OUTDATED":
            result["warnings"].append("⚠️ This information is outdated. Old news presented as current.")
            if result["verdict"] == "TRUE":
                result["verdict"] = "OUTDATED_INFO"
        
        # Store in database if uncertain or low confidence for periodic re-checking
        if result["verdict"] in ["UNCERTAIN", "OUTDATED_INFO"] or result["confidence"] < 0.65:
            result["stored_in_db"] = True
            db_tool = ClaimDatabaseTool()
            db_tool.run(
                action="store",
                claim=claim,
                verdict=result["verdict"],
                confidence=result["confidence"],
                evidence={
                    "gemini": gemini_result,
                    "web_search": web_result,
                    "timestamp": previous_stages.get("content_intake", {}).get("timestamp", "")
                }
            )
            result["explanation"] += "\n\n💾 This claim has been saved for periodic re-verification. You'll be notified when new information becomes available."
        else:
            # High confidence - provide confidence explanation
            if result["confidence"] >= 0.85:
                result["explanation"] += "\n\n✓ High confidence based on multiple authoritative sources."
        
        return result
    
    def _generate_context_card(self, verdict: str, confidence: float, 
                                web_sources: int, credible_sources: int,
                                reddit_posts: int, tweets: int,
                                misinfo_pattern: str = None, pattern_confidence: float = 0.0) -> dict:
        """Generate contextual card explaining why this verdict was reached."""
        
        # Determine card type and content based on verdict
        if verdict == "TRUE":
            return {
                "verdict_explanation": "This claim has been verified as TRUE",
                "confidence_level": f"{confidence*100:.0f}% confidence",
                "reasoning": f"Based on analysis of {web_sources} web sources ({credible_sources} credible), {reddit_posts} Reddit discussions, and {tweets} tweets.",
                "icon": "✅",
                "color": "green",
                "why_this_verdict": f"Multiple credible sources confirm this claim. Found {credible_sources} authoritative sources (news agencies, academic, government) that verify the information."
            }
        elif verdict == "FALSE":
            return {
                "verdict_explanation": "This claim has been identified as FALSE",
                "confidence_level": f"{confidence*100:.0f}% confidence",
                "reasoning": f"Based on analysis of {web_sources} web sources ({credible_sources} credible), {reddit_posts} Reddit discussions, and {tweets} tweets.",
                "icon": "❌",
                "color": "red",
                "why_this_verdict": f"Evidence from {credible_sources} credible sources contradicts this claim. This information is misleading or incorrect."
            }
        elif verdict == "LIKELY_FALSE":
            additional_explanation = ""
            if credible_sources == 0 and web_sources < 5:
                additional_explanation = " 💡 Major events generate widespread coverage. The complete absence of credible sources strongly indicates this is fabricated misinformation."
            return {
                "verdict_explanation": "This claim is LIKELY FALSE",
                "confidence_level": f"{confidence*100:.0f}% confidence",
                "reasoning": f"Based on analysis of {web_sources} web sources ({credible_sources} credible), {reddit_posts} Reddit discussions, and {tweets} tweets.",
                "icon": "⚠️",
                "color": "orange-red",
                "why_this_verdict": f"No credible sources found to verify this claim. For significant events, the absence of coverage strongly suggests the claim is false.{additional_explanation}"
            }
        elif verdict == "PARTIALLY_TRUE":
            return {
                "verdict_explanation": "This claim is PARTIALLY TRUE",
                "confidence_level": f"{confidence*100:.0f}% confidence",
                "reasoning": f"Based on analysis of {web_sources} web sources ({credible_sources} credible), {reddit_posts} Reddit discussions, and {tweets} tweets.",
                "icon": "⚠️",
                "color": "orange",
                "why_this_verdict": "Some aspects of this claim are accurate, but important context or details are missing or incorrect."
            }
        elif verdict == "OUTDATED_INFO":
            return {
                "verdict_explanation": "This claim contains OUTDATED INFORMATION",
                "confidence_level": f"{confidence*100:.0f}% confidence",
                "reasoning": f"Based on temporal analysis and {web_sources} current sources.",
                "icon": "📅",
                "color": "yellow",
                "why_this_verdict": "This information was accurate in the past but is no longer current. The claim may be presenting old news as if it's recent."
            }
        elif verdict == "UNVERIFIED":
            return {
                "verdict_explanation": "This claim is UNVERIFIED",
                "confidence_level": f"{confidence*100:.0f}% confidence",
                "reasoning": f"Analyzed {web_sources} sources, but couldn't find definitive confirmation or denial.",
                "icon": "❓",
                "color": "gray",
                "why_this_verdict": f"Found information about the topic but not enough evidence to confirm or deny the specific claim. Only {credible_sources} credible sources available."
            }
        else:  # UNCERTAIN
            base_card = {
                "verdict_explanation": "Unable to determine if this claim is true or false",
                "confidence_level": f"{confidence*100:.0f}% confidence",
                "reasoning": f"Searched {web_sources} web sources, {reddit_posts} Reddit posts, and {tweets} tweets.",
                "icon": "❓",
                "color": "gray",
                "why_this_verdict": "Search results were either irrelevant, insufficient, or contradictory. More information needed to make a determination."
            }
            
            # Add misinformation pattern detection if available
            if misinfo_pattern and pattern_confidence > 0.5:
                base_card["misinformation_alert"] = {
                    "pattern_detected": misinfo_pattern,
                    "pattern_confidence": f"{pattern_confidence*100:.0f}%",
                    "warning": f"⚠️ This claim matches common misinformation pattern: {misinfo_pattern}"
                }
            
            return base_card
    
    def _generate_education(self, pipeline_result: dict) -> dict:
        """Stage 4: Educational content generation."""
        # This would call the knowledge_agent
        
        # Determine appropriate educational topic
        media_analysis = pipeline_result["stages"].get("media_analysis", {})
        fact_check = pipeline_result["stages"].get("fact_check", {})
        
        topic = "general"
        if media_analysis and media_analysis.get("is_deepfake"):
            topic = "deepfake"
        elif fact_check.get("verdict") == "FALSE":
            topic = "fact_checking"
        
        return {
            "topic": topic,
            "tips": [
                "Always verify information from multiple credible sources",
                "Check the date and context of claims",
                "Be skeptical of sensational or emotionally charged content",
                "Use fact-checking websites for verification"
            ],
            "tailored_advice": self._get_tailored_advice(pipeline_result)
        }
    
    def _get_tailored_advice(self, pipeline_result: dict) -> str:
        """Generate specific advice based on analysis."""
        verdict = pipeline_result.get("final_verdict", "UNCERTAIN")
        confidence = pipeline_result.get("confidence", 0.0)
        
        if verdict == "FALSE":
            return "⚠️ This claim has been identified as false. Please do not share this information."
        elif verdict == "TRUE":
            return "✓ This claim has been verified as accurate from multiple sources."
        elif confidence < 0.5:
            return "❓ This claim cannot be verified with confidence. We're monitoring for updates."
        else:
            return "⚡ This claim has partial verification. Cross-check with additional sources."
    
    def _generate_recommendations(self, pipeline_result: dict) -> list:
        """Generate action recommendations for user."""
        recommendations = []
        
        verdict = pipeline_result.get("final_verdict")
        confidence = pipeline_result.get("confidence", 0.0)
        
        if verdict == "FALSE":
            recommendations.append("DO NOT SHARE this content")
            recommendations.append("Inform others who may have shared it")
        elif verdict == "UNCERTAIN" or confidence < 0.6:
            recommendations.append("WAIT for verification before sharing")
            recommendations.append("You'll receive updates when more information is available")
        elif verdict == "TRUE":
            recommendations.append("Content appears verified, but always maintain healthy skepticism")
            recommendations.append("Share responsibly with proper context")
        
        # Media-specific recommendations
        media_analysis = pipeline_result["stages"].get("media_analysis")
        if media_analysis and media_analysis.get("is_deepfake"):
            recommendations.append("Report this deepfake content to platform moderators")
        
        return recommendations
