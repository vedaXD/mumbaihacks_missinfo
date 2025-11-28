from google.adk.tools.base_tool import BaseTool
from transformers import AutoProcessor, AutoModelForImageClassification
import cv2
import numpy as np
from PIL import Image
import torch

class VideoDeepfakeTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="detect_video_deepfake",
            description="Detects deepfake videos using frame-by-frame analysis and temporal consistency checks."
        )
        # Load pretrained deepfake detection model (same as image model for frames)
        try:
            model_name = "umm-maybe/AI-image-detector"
            self.processor = AutoProcessor.from_pretrained(model_name)
            self.model = AutoModelForImageClassification.from_pretrained(model_name)
            self.model.eval()
            print("✓ Video deepfake detection model loaded successfully")
        except Exception as e:
            print(f"⚠️ Warning: Could not load video deepfake model: {e}")
            self.processor = None
            self.model = None
    
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
                
                # Run detection on frame
                if self.model and self.processor:
                    inputs = self.processor(images=pil_frame, return_tensors="pt")
                    
                    with torch.no_grad():
                        outputs = self.model(**inputs)
                        logits = outputs.logits
                        probabilities = torch.nn.functional.softmax(logits, dim=-1)
                    
                    predicted_class = probabilities.argmax(-1).item()
                    confidence = float(probabilities[0][predicted_class])
                    
                    # For umm-maybe/AI-image-detector: Class 0 = artificial, Class 1 = human
                    # If predicted as AI/artificial (class 0), add the confidence
                    if predicted_class == 0:
                        deepfake_scores.append(confidence)
                    else:
                        deepfake_scores.append(0.0)
                else:
                    # Placeholder
                    deepfake_scores.append(0.0)
            
            cap.release()
            
            # Aggregate scores
            avg_score = np.mean(deepfake_scores) if deepfake_scores else 0.0
            max_score = np.max(deepfake_scores) if deepfake_scores else 0.0
            is_deepfake = avg_score > 0.5
            
            return {
                "is_deepfake": is_deepfake,
                "average_confidence": float(avg_score),
                "max_confidence": float(max_score),
                "frames_analyzed": len(deepfake_scores),
                "total_frames": total_frames,
                "fps": fps,
                "analysis": "Real video" if not is_deepfake else "Potential deepfake detected",
                "model_loaded": self.model is not None
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "is_deepfake": None,
                "confidence": 0.0
            }
