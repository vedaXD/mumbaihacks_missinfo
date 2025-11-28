from google.adk.tools.base_tool import BaseTool
from PIL import Image
import easyocr
import cv2
import numpy as np

class OCRTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="extract_text_from_image",
            description="Extracts text from images and video frames using OCR (Optical Character Recognition)."
        )
        # Initialize EasyOCR reader
        try:
            self.reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if CUDA available
            print("✓ EasyOCR initialized successfully")
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize EasyOCR: {e}")
            self.reader = None
    
    def run(self, image_path: str = None, image_array: np.ndarray = None) -> dict:
        """
        Performs OCR on an image to extract text.
        
        Args:
            image_path: Path to image file
            image_array: Numpy array of image (for video frames)
            
        Returns:
            Dictionary with extracted text and confidence
        """
        try:
            # Load image
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
            
            return {
                "extracted_text": text.strip(),
                "confidence": float(avg_confidence),
                "has_text": len(text.strip()) > 0,
                "word_count": len(text.split())
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "extracted_text": "",
                "confidence": 0.0,
                "has_text": False
            }
