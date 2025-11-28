from google.adk.tools.base_tool import BaseTool
from PIL import Image
import easyocr
import cv2
import numpy as np
import os

# Try to import Qwen Vision for better OCR
try:
    from .qwen_vision_tool import QwenVisionTool
    QWEN_AVAILABLE = True
except:
    QWEN_AVAILABLE = False

class OCRTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="extract_text_from_image",
            description="Extracts text from images and video frames using advanced vision AI (Qwen VL) with EasyOCR fallback."
        )
        # Initialize Qwen Vision (primary method - better accuracy)
        self.qwen_vision = None
        if QWEN_AVAILABLE and os.getenv('QWEN_API_KEY'):
            try:
                self.qwen_vision = QwenVisionTool()
                if self.qwen_vision.available:
                    print("✓ OCR: Using Qwen Vision (primary) + EasyOCR (fallback)")
                else:
                    self.qwen_vision = None
            except Exception as e:
                print(f"⚠️ Qwen Vision unavailable: {e}")
                self.qwen_vision = None
        
        # Initialize EasyOCR reader (fallback method)
        try:
            self.reader = easyocr.Reader(['en'], gpu=False)
            if not self.qwen_vision:
                print("✓ EasyOCR initialized (primary method)")
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize EasyOCR: {e}")
            self.reader = None
    
    def run(self, image_path: str = None, image_array: np.ndarray = None) -> dict:
        """
        Performs OCR on an image to extract text using Qwen Vision (primary) or EasyOCR (fallback).
        
        Args:
            image_path: Path to image file
            image_array: Numpy array of image (for video frames)
            
        Returns:
            Dictionary with extracted text and confidence
        """
        try:
            # For image arrays, save temporarily for Qwen Vision
            temp_path = None
            if image_array is not None and image_path is None:
                temp_path = "/tmp/temp_ocr_frame.jpg"
                img = Image.fromarray(image_array)
                img.save(temp_path)
                image_path = temp_path
            
            # Try Qwen Vision first (better accuracy, especially for complex layouts)
            if self.qwen_vision and image_path:
                try:
                    result = self.qwen_vision.run(image_path=image_path, analysis_type="ocr")
                    if "error" not in result and result.get("has_text"):
                        # Clean up temp file
                        if temp_path and os.path.exists(temp_path):
                            os.remove(temp_path)
                        return result
                except Exception as e:
                    print(f"Qwen Vision OCR failed, falling back to EasyOCR: {e}")
            
            # Fallback to EasyOCR
            if image_path:
                img = Image.open(image_path)
            elif image_array is not None:
                img = Image.fromarray(image_array)
            else:
                return {"error": "No image provided"}
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert to numpy array for EasyOCR
            img_array = np.array(img)
            
            # Extract text using EasyOCR
            if self.reader:
                results = self.reader.readtext(img_array)
                
                # Combine all detected text
                text_parts = []
                confidences = []
                
                for (bbox, text, confidence) in results:
                    text_parts.append(text)
                    confidences.append(confidence)
                
                text = ' '.join(text_parts)
                avg_confidence = np.mean(confidences) * 100 if confidences else 0
            else:
                text = ""
                avg_confidence = 0
            
            # Clean up temp file
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            
            return {
                "extracted_text": text.strip(),
                "confidence": float(avg_confidence),
                "has_text": len(text.strip()) > 0,
                "word_count": len(text.split()),
                "method": "easyocr"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "extracted_text": "",
                "confidence": 0.0,
                "has_text": False
            }
