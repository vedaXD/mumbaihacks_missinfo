from google.adk.tools.base_tool import BaseTool
import torch
import torch.nn.functional as F
from torchvision import transforms
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
from PIL import Image
import io
import base64
import os
import numpy as np
import cv2

class ImageDeepfakeTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="detect_image_deepfake",
            description="Detects if an image is AI-generated or manipulated using custom-trained EfficientNet model with Grad-CAM visualization."
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
            
            # Store target layer for Grad-CAM (last convolutional layer before classifier)
            self.target_layer = self.model.features[-1]
            self.gradients = None
            self.activations = None
            
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
    
    def _save_gradient(self, grad):
        """Hook to save gradients during backward pass"""
        self.gradients = grad
    
    def _save_activation(self, module, input, output):
        """Hook to save activations during forward pass"""
        self.activations = output
    
    def _generate_gradcam(self, input_tensor, target_class):
        """Generate Grad-CAM heatmap"""
        # Register hooks
        handle_forward = self.target_layer.register_forward_hook(self._save_activation)
        
        # Forward pass
        output = self.model(input_tensor)
        
        # Get the score for target class
        target_score = output[0, target_class]
        
        # Backward pass
        self.model.zero_grad()
        target_score.backward()
        
        # Get gradients from the hook
        handle_backward = self.activations.register_hook(self._save_gradient)
        target_score.backward(retain_graph=True)
        
        # Calculate weights
        gradients = self.gradients.detach()
        activations = self.activations.detach()
        
        # Global average pooling
        weights = torch.mean(gradients, dim=(2, 3), keepdim=True)
        
        # Weighted combination
        cam = torch.sum(weights * activations, dim=1, keepdim=True)
        
        # ReLU
        cam = F.relu(cam)
        
        # Normalize
        cam = cam - cam.min()
        if cam.max() > 0:
            cam = cam / cam.max()
        
        # Remove hooks
        handle_forward.remove()
        handle_backward.remove()
        
        # Resize to input size
        cam = F.interpolate(cam, size=(224, 224), mode='bilinear', align_corners=False)
        cam = cam.squeeze().cpu().numpy()
        
        return cam
    
    def _apply_gradcam_overlay(self, original_img, heatmap):
        """Apply Grad-CAM heatmap as overlay on original image"""
        # Resize original image to 224x224
        img_resized = original_img.resize((224, 224))
        img_array = np.array(img_resized)
        
        # Convert heatmap to colormap
        heatmap_uint8 = (heatmap * 255).astype(np.uint8)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
        
        # Overlay
        overlay = (0.6 * img_array + 0.4 * heatmap_colored).astype(np.uint8)
        
        # Convert to PIL Image
        overlay_img = Image.fromarray(overlay)
        
        # Convert to base64
        buffer = io.BytesIO()
        overlay_img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return img_base64
    
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
            gradcam_base64 = None
            
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
                
                # Generate Grad-CAM visualization if deepfake detected
                try:
                    if is_deepfake:
                        print(f"   Generating Grad-CAM visualization...")
                        input_tensor_grad = self.transform(img).unsqueeze(0)
                        input_tensor_grad.requires_grad = True
                        
                        # Generate heatmap for the predicted class (FAKE=1)
                        heatmap = self._generate_gradcam(input_tensor_grad, predicted_class)
                        
                        # Apply overlay
                        gradcam_base64 = self._apply_gradcam_overlay(img, heatmap)
                        print(f"   ✓ Grad-CAM visualization generated")
                except Exception as e:
                    print(f"   Warning: Could not generate Grad-CAM: {e}")
                    gradcam_base64 = None
                
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
            
            result = {
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
            
            # Add Grad-CAM if available
            if gradcam_base64:
                result["gradcam_visualization"] = gradcam_base64
            
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "is_deepfake": None,
                "confidence": 0.0
            }
