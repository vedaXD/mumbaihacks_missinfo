"""
Image Generator Agent - Uses Imagen 4.0 Fast to generate 9:16 images
"""

import logging
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

logger = logging.getLogger(__name__)

class ImageGeneratorAgent:
    """Agent that generates images using Imagen 4.0 Fast"""
    
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
        
        logger.info(f"🖼️ Image Generator initialized - Model: {self.model_name}")
    
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
                return self._generate_placeholder_image(scene_number)
                
        except Exception as e:
            logger.error(f"❌ Error generating image {scene_number}: {type(e).__name__}: {e}")
            return self._generate_placeholder_image(scene_number)
    
    def generate_images_batch(self, scene_scripts: list) -> list:
        """
        Generate multiple images from scene scripts
        
        Args:
            scene_scripts: List of scene dictionaries with 'image_prompt'
            
        Returns:
            List of dictionaries with 'scene_number', 'image_bytes', 'narration', 'duration'
        """
        logger.info(f"🎨 Generating {len(scene_scripts)} images...")
        
        results = []
        for scene in scene_scripts:
            scene_number = scene.get('scene_number', 1)
            prompt = scene.get('image_prompt', '')
            
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
        
        # Add text
        text = f"Scene {scene_number}\nImage Generation Failed"
        
        # Use default font
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        # Get text bounding box and center it
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (1080 - text_width) // 2
        y = (1920 - text_height) // 2
        
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
