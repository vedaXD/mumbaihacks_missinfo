"""
Script Generator Agent - Uses Gemini to generate image scripts from news summary
"""

import logging
import json
import vertexai
from vertexai.preview.generative_models import GenerativeModel

logger = logging.getLogger(__name__)

class ScriptGeneratorAgent:
    """Agent that generates structured scripts for individual images from news summary"""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        """
        Initialize the Script Generator Agent
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
        """
        self.project_id = project_id
        self.location = location
        self.model_name = "gemini-2.0-flash-exp"
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # Initialize the Gemini model
        self.model = GenerativeModel(self.model_name)
        
        logger.info(f"🎬 Script Generator initialized - Model: {self.model_name}")
    
    def generate_script(self, news_summary: str, num_scenes: int = 8) -> list:
        """
        Generate structured script for individual images
        
        Args:
            news_summary: The news summary text
            num_scenes: Number of scenes/images to generate (default: 8)
            
        Returns:
            List of scene dictionaries with 'image_prompt', 'narration', 'duration'
        """
        logger.info(f"📝 Generating script for {num_scenes} scenes from news summary...")
        
        try:
            # Create detailed prompt for script generation
            prompt = f"""You are a professional news reel scriptwriter. Given a news summary, create {num_scenes} scenes for a vertical video reel (9:16 aspect ratio).

For each scene, provide:
1. image_prompt: A detailed visual description for AI image generation (describe colors, composition, subjects, mood)
2. narration: The exact text to be spoken for this scene (concise, news-style)
3. duration: How long this scene should appear (in seconds, typically 3-5 seconds)

Make sure the total narration covers the entire news summary and each image_prompt creates visually distinct, compelling imagery suitable for news.

News Summary:
{news_summary}

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "scene_number": 1,
    "image_prompt": "detailed visual description",
    "narration": "text to be spoken",
    "duration": 4
  }}
]

JSON Output:"""
            
            # Generate content with Gemini
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                }
            )
            
            # Extract JSON from response
            if response and response.text:
                logger.info("✅ Script generated successfully")
                
                # Try to parse JSON from response
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                if response_text.startswith("```json"):
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif response_text.startswith("```"):
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                scenes = json.loads(response_text)
                
                logger.info(f"📋 Generated {len(scenes)} scenes")
                for i, scene in enumerate(scenes, 1):
                    logger.info(f"  Scene {i}: {scene.get('narration', '')[:50]}...")
                
                return scenes
            else:
                logger.error("❌ No response from Gemini")
                return self._generate_fallback_script(news_summary, num_scenes)
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON from Gemini response: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return self._generate_fallback_script(news_summary, num_scenes)
            
        except Exception as e:
            logger.error(f"❌ Error generating script: {type(e).__name__}: {e}")
            return self._generate_fallback_script(news_summary, num_scenes)
    
    def _generate_fallback_script(self, news_summary: str, num_scenes: int) -> list:
        """Generate a simple fallback script if AI generation fails"""
        logger.warning("⚠️ Using fallback script generation")
        
        # Split news summary into sentences
        sentences = [s.strip() + '.' for s in news_summary.split('.') if s.strip()]
        
        scenes = []
        for i in range(min(num_scenes, len(sentences))):
            scenes.append({
                "scene_number": i + 1,
                "image_prompt": f"News scene showing {sentences[i][:100]}",
                "narration": sentences[i],
                "duration": 4
            })
        
        return scenes
