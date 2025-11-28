"""
Orchestrator Agent - Main orchestration logic
"""

import logging
from .sub_agents import ScriptGeneratorAgent, ImageGeneratorAgent, VideoComposerAgent, NewsFetcherAgent

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """Main orchestrator that coordinates all sub-agents"""
    
    def __init__(self, project_id: str, location: str = "us-central1", news_api_key: str = None):
        """
        Initialize the Orchestrator Agent
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
            news_api_key: Optional NewsAPI.org API key
        """
        self.project_id = project_id
        self.location = location
        
        # Initialize all sub-agents
        logger.info("🎯 Initializing Orchestrator Agent...")
        
        self.script_generator = ScriptGeneratorAgent(project_id, location)
        self.image_generator = ImageGeneratorAgent(project_id, location)
        self.video_composer = VideoComposerAgent(project_id)
        self.news_fetcher = NewsFetcherAgent(project_id, location, news_api_key)
        
        logger.info("✅ Orchestrator Agent ready")
    
    def generate_reel(self, news_summary: str, num_scenes: int = 8, output_path: str = None) -> dict:
        """
        Generate a complete news reel from a summary
        
        Args:
            news_summary: The news summary text
            num_scenes: Number of scenes to generate (default: 8)
            output_path: Optional output path for video
            
        Returns:
            Dictionary with 'success', 'video_path', 'scenes', and 'error' keys
        """
        logger.info("=" * 60)
        logger.info("🚀 STARTING NEWS REEL GENERATION")
        logger.info("=" * 60)
        logger.info(f"📰 News Summary: {news_summary[:100]}...")
        logger.info(f"🎬 Target Scenes: {num_scenes}")
        
        try:
            # Step 1: Generate script with Gemini
            logger.info("\n" + "=" * 60)
            logger.info("STEP 1: SCRIPT GENERATION")
            logger.info("=" * 60)
            
            scenes = self.script_generator.generate_script(news_summary, num_scenes)
            
            if not scenes:
                raise Exception("Script generation failed - no scenes generated")
            
            logger.info(f"✅ Script generated with {len(scenes)} scenes")
            
            # Step 2: Generate images with Imagen
            logger.info("\n" + "=" * 60)
            logger.info("STEP 2: IMAGE GENERATION")
            logger.info("=" * 60)
            
            scene_data = self.image_generator.generate_images_batch(scenes)
            
            if not scene_data:
                raise Exception("Image generation failed - no images generated")
            
            logger.info(f"✅ Generated {len(scene_data)} images")
            
            # Step 3: Compose video with TTS audio
            logger.info("\n" + "=" * 60)
            logger.info("STEP 3: VIDEO COMPOSITION")
            logger.info("=" * 60)
            
            video_path = self.video_composer.compose_video(scene_data, output_path)
            
            logger.info("\n" + "=" * 60)
            logger.info("🎉 NEWS REEL GENERATION COMPLETE")
            logger.info("=" * 60)
            logger.info(f"📹 Video Path: {video_path}")
            logger.info(f"🎬 Total Scenes: {len(scenes)}")
            logger.info("=" * 60 + "\n")
            
            return {
                'success': True,
                'video_path': video_path,
                'scenes': scenes,
                'num_scenes': len(scenes)
            }
            
        except Exception as e:
            logger.error("\n" + "=" * 60)
            logger.error("❌ NEWS REEL GENERATION FAILED")
            logger.error("=" * 60)
            logger.error(f"Error: {type(e).__name__}: {e}")
            logger.error("=" * 60 + "\n")
            
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
