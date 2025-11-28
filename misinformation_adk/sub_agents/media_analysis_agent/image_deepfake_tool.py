from google.adk.tools.base_tool import BaseTool
import torch
from torchvision import transforms
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
from PIL import Image
import io
import base64
import os

class ImageDeepfakeTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="detect_image_deepfake",
            description="Detects if an image is AI-generated or manipulated using custom-trained EfficientNet model."
        )
        # Load custom trained EfficientNet model
        try:
            model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'best_model-v3.pt')
            print(f"Loading custom EfficientNet deepfake detection model from: {model_path}...")
            
            # Initialize EfficientNet architecture
            weights = EfficientNet_B0_Weights.IMAGENET1K_V1
            self.model = efficientnet_b0(weights=weights)
            in_features = self.model.classifier[1].in_features
            self.model.classifier = torch.nn.Sequential(
                torch.nn.Dropout(0.4),
                torch.nn.Linear(in_features, 2)  # 2 classes: REAL (0) and FAKE (1)
            )
            
            # Load trained weights
            self.model.load_state_dict(torch.load(model_path, map_location="cpu"))
            self.model.eval()
            
            # Define image preprocessing
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])
            
            print("✓ Custom EfficientNet deepfake detection model loaded successfully")
            print("   Classes: 0=REAL, 1=FAKE")
        except Exception as e:
            print(f"⚠️ Warning: Could not load custom deepfake model: {e}")
            print("   Continuing with fallback detection...")
            self.model = None
            self.transform = None
    
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
            
            # Initialize variables
            real_prob = None
            fake_prob = None
            
            # Run detection with custom EfficientNet model
            if self.model and self.transform:
                # Preprocess image
                input_tensor = self.transform(img).unsqueeze(0)
                
                # Get predictions
                with torch.no_grad():
                    output = self.model(input_tensor)
                    probabilities = torch.softmax(output, dim=1)[0]
                    predicted_class = torch.argmax(probabilities).item()
                
                # Extract probabilities
                real_prob = float(probabilities[0])
                fake_prob = float(probabilities[1])
                
                # Determine result (class 0 = REAL, class 1 = FAKE)
                is_deepfake = predicted_class == 1
                confidence = fake_prob if is_deepfake else real_prob
                
                # Print results
                print(f"   [DEEPFAKE DETECTION]")
                print(f"   - Real probability: {real_prob:.3f}")
                print(f"   - Fake probability: {fake_prob:.3f}")
                print(f"   - Prediction: {'FAKE' if is_deepfake else 'REAL'}")
                print(f"   - Confidence: {confidence:.3f}")
                
                # Generate explanation
                if is_deepfake:
                    explanation = f"Image detected as AI-GENERATED/FAKE with {confidence:.1%} confidence. The model identified artificial patterns consistent with deepfake or synthetic image generation."
                else:
                    explanation = f"Image appears AUTHENTIC/REAL with {confidence:.1%} confidence. No significant manipulation detected."
                
            else:
                # Fallback: Model not loaded
                print("   Using fallback detection (model not loaded)...")
                confidence = 0.5
                is_deepfake = False
                explanation = "Deepfake model not loaded. Unable to perform detailed analysis."
            
            return {
                "is_manipulated": is_deepfake,
                "is_deepfake": is_deepfake,  # For backward compatibility
                "confidence": confidence,
                "authenticity_score": 1.0 - confidence if is_deepfake else confidence,
                "explanation": explanation,
                "technical_details": {
                    "model": "EfficientNet-B0 (Custom Trained)",
                    "real_probability": real_prob if self.model else None,
                    "fake_probability": fake_prob if self.model else None
                },
                "model_loaded": self.model is not None
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "is_deepfake": None,
                "confidence": 0.0
            }
