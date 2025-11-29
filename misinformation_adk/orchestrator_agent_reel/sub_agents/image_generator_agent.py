"""
Image Generator Agent - Uses Imagen 3.0 to generate 9:16 images
"""

import logging
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)

class ImageGeneratorAgent:
    """Agent that generates images using Imagen 3.0"""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        """
        Initialize the Image Generator Agent
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
        """
        self.project_id = project_id
        self.location = location
        self.model_name = "imagen-3.0-generate-001"  # Using working stable version
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # Setup fallback images directory
        self.fallback_dir = Path(__file__).parent.parent / "fallback_images"
        self._ensure_fallback_images()
        
        logger.info(f"🖼️ Image Generator initialized - Model: {self.model_name}")
    
    def _ensure_fallback_images(self):
        """Create fallback images directory with pre-built images"""
        self.fallback_dir.mkdir(exist_ok=True)
        
        # Create multiple fallback images if they don't exist
        fallback_count = 5
        for i in range(fallback_count):
            fallback_path = self.fallback_dir / f"fallback_{i+1}.png"
            if not fallback_path.exists():
                self._create_fallback_image(fallback_path, i+1)
    
    def _create_fallback_image(self, path: Path, image_num: int):
        """Create a professional-looking fallback image"""
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a 1080x1920 image (9:16 aspect ratio)
        colors = [
            (45, 55, 72),    # Dark blue-gray
            (26, 32, 44),    # Darker gray
            (49, 46, 129),   # Purple
            (17, 24, 39),    # Almost black
            (31, 41, 55),    # Dark slate
        ]
        
        color = colors[image_num - 1]
        img = Image.new('RGB', (1080, 1920), color=color)
        draw = ImageDraw.Draw(img)
        
        # Add gradient effect
        for i in range(1920):
            alpha = int((i / 1920) * 50)
            darker_color = tuple(max(0, c - alpha) for c in color)
            draw.rectangle([(0, i), (1080, i+1)], fill=darker_color)
        
        # Add decorative elements
        draw.ellipse([200, 700, 880, 1380], fill=(255, 255, 255, 20))
        
        # Add main text
        text = "📰 News Image"
        
        try:
            font_large = ImageFont.truetype("arial.ttf", 80)
            font_small = ImageFont.truetype("arial.ttf", 40)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), text, font=font_large)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        y = 900
        
        # Draw main text with shadow
        draw.text((x+3, y+3), text, fill=(0, 0, 0, 128), font=font_large)
        draw.text((x, y), text, fill=(255, 255, 255), font=font_large)
        
        # Add "Vishwas Netra" watermark at top right
        watermark_text = "Vishwas Netra"
        try:
            wm_bbox = draw.textbbox((0, 0), watermark_text, font=font_small)
            wm_width = wm_bbox[2] - wm_bbox[0]
            wm_x = 1080 - wm_width - 30
            wm_y = 30
            
            # Draw watermark with shadow
            draw.text((wm_x+2, wm_y+2), watermark_text, fill=(0, 0, 0, 150), font=font_small)
            draw.text((wm_x, wm_y), watermark_text, fill=(255, 255, 255, 230), font=font_small)
        except Exception as e:
            logger.warning(f"Could not add watermark to fallback image: {e}")
        
        img.save(path, 'PNG')
        logger.info(f"✅ Created fallback image: {path.name}")
    
    def _get_fallback_image(self, scene_number: int) -> bytes:
        """Get a pre-built fallback image"""
        fallback_files = sorted(self.fallback_dir.glob("fallback_*.png"))
        
        if fallback_files:
            # Cycle through available fallback images
            fallback_path = fallback_files[(scene_number - 1) % len(fallback_files)]
            logger.warning(f"⚠️ Using fallback image: {fallback_path.name}")
            return fallback_path.read_bytes()
        else:
            # Last resort: generate on the fly
            logger.warning(f"⚠️ No fallback images found, generating placeholder")
            return self._generate_placeholder_image(scene_number)
    
    def generate_image(self, prompt: str, scene_number: int) -> bytes:
        """
        Generate a single 9:16 image from prompt
        
        Args:
            prompt: The image description
            scene_number: Scene number for logging
            
        Returns:
            Image bytes (JPEG format)
        """
        logger.info(f"🎨 Generating image {scene_number}: {prompt[:60]}...")
        
        try:
            # Load model fresh each time to avoid state issues
            model = ImageGenerationModel.from_pretrained(self.model_name)
            
            # Generate image (aspect ratio handled differently in different versions)
            try:
                # Try with aspect_ratio parameter first
                response = model.generate_images(
                    prompt=prompt,
                    number_of_images=1,
                    aspect_ratio="9:16",  # Vertical format for reels
                )
            except TypeError:
                # Fallback: generate without aspect_ratio parameter
                logger.warning(f"⚠️ aspect_ratio not supported, using default generation")
                response = model.generate_images(
                    prompt=prompt,
                    number_of_images=1,
                )
            
            if response.images and len(response.images) > 0:
                # Get image bytes from PIL image
                import io
                image = response.images[0]._pil_image
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                image_bytes = img_byte_arr.getvalue()
                
                logger.info(f"✅ Image {scene_number} generated ({len(image_bytes)} bytes, size: {image.size})")
                return image_bytes
            else:
                logger.error(f"❌ No image generated for scene {scene_number}")
                return self._get_fallback_image(scene_number)
                
        except Exception as e:
            logger.error(f"❌ Error generating image {scene_number}: {type(e).__name__}: {e}")
            return self._get_fallback_image(scene_number)
    
    def generate_images_batch(self, scene_scripts: list) -> list:
        """
        Generate multiple images from scene scripts with rate limiting
        
        Args:
            scene_scripts: List of scene dictionaries with 'image_prompt'
            
        Returns:
            List of dictionaries with 'scene_number', 'image_bytes', 'narration', 'duration'
        """
        logger.info(f"🎨 Generating {len(scene_scripts)} images...")
        
        results = []
        for idx, scene in enumerate(scene_scripts):
            scene_number = scene.get('scene_number', 1)
            prompt = scene.get('image_prompt', '')
            
            # Add delay between requests to avoid quota exhaustion (except first image)
            if idx > 0:
                delay = 3  # 3 seconds delay between requests
                logger.info(f"⏳ Waiting {delay}s before next image generation...")
                time.sleep(delay)
            
            image_bytes = self.generate_image(prompt, scene_number)
            
            results.append({
                'scene_number': scene_number,
                'image_bytes': image_bytes,
                'narration': scene.get('narration', ''),
                'duration': scene.get('duration', 4)
            })
        
        logger.info(f"✅ Generated {len(results)} images successfully")
        return results
    
    def _generate_placeholder_image(self, scene_number: int) -> bytes:
        """Generate a simple placeholder image if generation fails"""
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        logger.warning(f"⚠️ Generating placeholder image for scene {scene_number}")
        
        # Create a 1080x1920 image (9:16 aspect ratio)
        img = Image.new('RGB', (1080, 1920), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        
        # Add main text
        text = f"Scene {scene_number}\nNews Image"
        
        # Use default font
        try:
            font_large = ImageFont.truetype("arial.ttf", 60)
            font_small = ImageFont.truetype("arial.ttf", 40)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Get text bounding box and center it
        bbox = draw.textbbox((0, 0), text, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (1080 - text_width) // 2
        y = (1920 - text_height) // 2
        
        draw.text((x, y), text, fill=(255, 255, 255), font=font_large)
        
        # Add "Vishwas Netra" watermark at top right
        watermark_text = "Vishwas Netra"
        try:
            wm_bbox = draw.textbbox((0, 0), watermark_text, font=font_small)
            wm_width = wm_bbox[2] - wm_bbox[0]
            wm_x = 1080 - wm_width - 30
            wm_y = 30
            
            # Draw watermark
            draw.text((wm_x+2, wm_y+2), watermark_text, fill=(0, 0, 0), font=font_small)
            draw.text((wm_x, wm_y), watermark_text, fill=(200, 200, 200), font=font_small)
        except Exception as e:
            logger.warning(f"Could not add watermark to placeholder: {e}")
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
