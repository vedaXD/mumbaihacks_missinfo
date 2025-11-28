from google.adk.tools.base_tool import BaseTool
import cv2
import numpy as np
from PIL import Image
import torch
from torchvision import transforms
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
import os

class VideoDeepfakeTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="detect_video_deepfake",
            description="Detects deepfake videos using frame-by-frame analysis with custom EfficientNet model."
        )
        # Load custom trained EfficientNet model (same as image detector)
        try:
            model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'best_model-v3.pt')
            print(f"Loading custom EfficientNet for video analysis from: {model_path}...")
            
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
            
            print("✓ Custom EfficientNet video deepfake detection model loaded successfully")
        except Exception as e:
            print(f"⚠️ Warning: Could not load video deepfake model: {e}")
            self.model = None
            self.transform = None
    
    def run(self, video_path: str, sample_frames: int = 30) -> dict:
        """
        Analyzes a video for deepfake indicators.
        
        Args:
            video_path: Path to video file
            sample_frames: Number of frames to analyze
            
        Returns:
            Dictionary with deepfake analysis results
        """
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Sample frames uniformly
            frame_indices = np.linspace(0, total_frames - 1, sample_frames, dtype=int)
            
            deepfake_scores = []
            
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # Convert BGR to RGB and to PIL Image
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_frame = Image.fromarray(frame_rgb)
                
                # Run detection on frame with custom EfficientNet
                if self.model and self.transform:
                    input_tensor = self.transform(pil_frame).unsqueeze(0)
                    
                    with torch.no_grad():
                        output = self.model(input_tensor)
                        probabilities = torch.softmax(output, dim=1)[0]
                        predicted_class = torch.argmax(probabilities).item()
                    
                    fake_prob = float(probabilities[1])
                    
                    # Class 1 = FAKE, so add fake probability
                    deepfake_scores.append(fake_prob)
                else:
                    # Placeholder
                    deepfake_scores.append(0.0)
            
            cap.release()
            
            # Aggregate scores
            avg_score = np.mean(deepfake_scores) if deepfake_scores else 0.0
            max_score = np.max(deepfake_scores) if deepfake_scores else 0.0
            is_deepfake = avg_score > 0.5
            
            # Generate explanation
            if is_deepfake:
                explanation = f"Video detected as DEEPFAKE with {avg_score:.1%} average confidence across {len(deepfake_scores)} frames. Peak detection: {max_score:.1%}."
            else:
                explanation = f"Video appears AUTHENTIC with {1.0-avg_score:.1%} confidence. Analyzed {len(deepfake_scores)} frames uniformly sampled from {total_frames} total frames."
            
            return {
                "is_deepfake": is_deepfake,
                "confidence": float(avg_score),
                "average_confidence": float(avg_score),
                "max_confidence": float(max_score),
                "frames_analyzed": len(deepfake_scores),
                "total_frames": total_frames,
                "fps": fps,
                "explanation": explanation,
                "technical_details": {
                    "model": "EfficientNet-B0 (Custom Trained)",
                    "frames_sampled": sample_frames,
                    "detection_threshold": 0.5
                },
                "model_loaded": self.model is not None
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "is_deepfake": None,
                "confidence": 0.0
            }
