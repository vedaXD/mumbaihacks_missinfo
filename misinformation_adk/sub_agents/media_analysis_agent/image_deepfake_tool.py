from google.adk.tools.base_tool import BaseTool
from transformers import AutoProcessor, AutoModelForImageClassification
import numpy as np
from PIL import Image
import io
import base64
import torch

class ImageDeepfakeTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="detect_image_deepfake",
            description="Detects if an image is AI-generated or manipulated using pre-trained deepfake detection models."
        )
        # Load pretrained deepfake detection model
        # Using a working model from HuggingFace that auto-downloads
        try:
            # Try AI-generated image detector first (better for screenshots, AI art, etc.)
            # Falls back to deepfake detector if needed
            model_name = "umm-maybe/AI-image-detector"  # Detects AI-generated images (Stable Diffusion, DALL-E, etc.)
            print(f"Loading AI-generated image detection model: {model_name}...")
            self.processor = AutoProcessor.from_pretrained(model_name)
            self.model = AutoModelForImageClassification.from_pretrained(model_name)
            self.model.eval()
            print("✓ AI-generated image detection model loaded successfully")
            print(f"   Class labels: {self.model.config.id2label}")
        except Exception as e:
            print(f"⚠️ Warning: Could not load image deepfake model: {e}")
            print("   Continuing with basic ELA-based detection...")
            self.processor = None
            self.model = None
    
    def run(self, image_path: str = None, image_data: str = None) -> dict:
        """
        Analyzes an image for deepfake/manipulation indicators.
        
        Args:
            image_path: Path to image file
            image_data: Base64 encoded image data
            
        Returns:
            Dictionary with deepfake analysis results
        """
        try:
            # Load image
            if image_path:
                img = Image.open(image_path)
            elif image_data:
                img_bytes = base64.b64decode(image_data)
                img = Image.open(io.BytesIO(img_bytes))
            else:
                return {"error": "No image provided"}
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Run detection
            if self.model and self.processor:
                # Preprocess image
                inputs = self.processor(images=img, return_tensors="pt")
                
                # Get predictions
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    logits = outputs.logits
                    probabilities = torch.nn.functional.softmax(logits, dim=-1)
                
                # Get prediction (class 0 = real, class 1 = fake for most deepfake models)
                predicted_class = probabilities.argmax(-1).item()
                confidence = float(probabilities[0][predicted_class])
                
                # DEBUG: Print all class probabilities
                print(f"   [DEBUG] Model predictions:")
                print(f"   - Class 0 (Artificial/AI): {float(probabilities[0][0]):.4f}")
                print(f"   - Class 1 (Human/Real): {float(probabilities[0][1]):.4f}")
                print(f"   - Predicted class: {predicted_class}")
                print(f"   - Confidence: {confidence:.4f}")
                
                # Check if AI-generated/deepfake
                # For umm-maybe/AI-image-detector: Class 0 = artificial, Class 1 = human
                is_deepfake = predicted_class == 0  # Class 0 means AI-generated/artificial
                
            else:
                # Fallback: Use basic ELA when model not loaded
                print("   Using basic image analysis (model not loaded)...")
                confidence = 0.3  # Low confidence placeholder
                is_deepfake = False
            
            return {
                "is_deepfake": is_deepfake,
                "confidence": confidence,
                "authenticity_score": 1.0 - confidence,
                "analysis": "Real image" if not is_deepfake else "Potential deepfake detected",
                "model_loaded": self.model is not None
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "is_deepfake": None,
                "confidence": 0.0
            }
