from google.adk.tools.base_tool import BaseTool
from openai import OpenAI
from PIL import Image
import base64
import io
import os

class QwenVisionTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="qwen_vision_analysis",
            description="Advanced vision analysis using Qwen VL model for text extraction, content understanding, and claim detection in images."
        )
        # Initialize Qwen client via OpenAI-compatible API
        api_key = os.getenv('QWEN_API_KEY', 'psai_lytHwV57cfUv6iBLRFfigLn0fqU03lwOtspDKqaF2_psVO_b')
        
        if api_key:
            try:
                self.client = OpenAI(
                    base_url='https://api.pipeshift.com/api/v0/',
                    api_key=api_key
                )
                print("✓ Qwen Vision (qwen3-vl-30b) initialized successfully")
                self.available = True
            except Exception as e:
                print(f"⚠️ Warning: Could not initialize Qwen Vision: {e}")
                self.client = None
                self.available = False
        else:
            print("⚠️ Warning: QWEN_API_KEY not set")
            self.client = None
            self.available = False
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 for API call."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (max 1024px on longest side)
                max_size = 1024
                if max(img.size) > max_size:
                    ratio = max_size / max(img.size)
                    new_size = tuple(int(dim * ratio) for dim in img.size)
                    img = img.resize(new_size, Image.LANCZOS)
                
                # Convert to base64
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=85)
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                return f"data:image/jpeg;base64,{img_base64}"
        except Exception as e:
            print(f"Error encoding image: {e}")
            return None
    
    def run(self, image_path: str = None, analysis_type: str = "comprehensive") -> dict:
        """
        Performs advanced vision analysis on an image using Qwen VL model.
        
        Args:
            image_path: Path to image file
            analysis_type: Type of analysis - "ocr", "claims", "context", or "comprehensive"
            
        Returns:
            Dictionary with extracted text, claims, context, and content understanding
        """
        if not self.available or not self.client:
            return {
                "error": "Qwen Vision model not available",
                "extracted_text": "",
                "claims": [],
                "context": ""
            }
        
        if not image_path or not os.path.exists(image_path):
            return {
                "error": "Invalid image path",
                "extracted_text": "",
                "claims": [],
                "context": ""
            }
        
        try:
            # Encode image
            image_data = self._encode_image_to_base64(image_path)
            if not image_data:
                return {
                    "error": "Failed to encode image",
                    "extracted_text": "",
                    "claims": [],
                    "context": ""
                }
            
            # Prepare prompt based on analysis type
            if analysis_type == "ocr":
                prompt = """Extract ALL text visible in this image. Include:
- Main headlines and titles
- Body text and captions
- Text overlays and watermarks
- Any numbers, dates, or statistics
- Social media handles and URLs

Return the text exactly as it appears, maintaining formatting where possible."""
            
            elif analysis_type == "claims":
                prompt = """Analyze this image and identify ALL factual claims that can be verified. For each claim:
1. Extract the exact claim statement
2. Note if it's from text, visual context, or implied
3. Rate the claim's verifiability (high/medium/low)

Focus on:
- Factual statements about events, people, places
- Statistics and numbers
- Quotes attributed to people
- News headlines
- Scientific or medical claims

Return in this format:
CLAIM 1: [exact claim]
CLAIM 2: [exact claim]
..."""
            
            elif analysis_type == "context":
                prompt = """Describe this image comprehensively:
1. What is the main subject/topic?
2. What type of content is this? (meme, news screenshot, infographic, photo, etc.)
3. What is the apparent purpose/message?
4. Are there any visual indicators of manipulation? (poor quality, inconsistencies, etc.)
5. What emotions or reactions might this evoke?

Be specific and objective."""
            
            else:  # comprehensive
                prompt = """Analyze this image comprehensively for fact-checking purposes:

1. TEXT EXTRACTION:
   - Extract ALL visible text exactly as it appears
   
2. FACTUAL CLAIMS:
   - Identify all factual claims that can be verified
   - Note claims from both text and visual elements
   
3. CONTEXT & CONTENT:
   - What type of content is this?
   - What is the main message or narrative?
   - Are there signs of manipulation or poor quality?
   
4. VERIFICATION PRIORITY:
   - Which claims should be fact-checked first?
   - What information is most likely to be misleading?

Provide detailed, structured output."""
            
            # Call Qwen Vision API
            response = self.client.chat.completions.create(
                model="neysa-qwen3-vl-30b-a3b",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.3  # Lower temperature for more factual output
            )
            
            # Extract response
            result_text = response.choices[0].message.content
            
            # Parse response based on analysis type
            if analysis_type == "ocr":
                return {
                    "extracted_text": result_text.strip(),
                    "has_text": len(result_text.strip()) > 0,
                    "word_count": len(result_text.split()),
                    "method": "qwen-vision"
                }
            
            elif analysis_type == "claims":
                # Extract claims from response
                claims = []
                lines = result_text.split('\n')
                for line in lines:
                    if line.strip().startswith('CLAIM'):
                        claim_text = line.split(':', 1)[1].strip() if ':' in line else line.strip()
                        if claim_text:
                            claims.append(claim_text)
                
                return {
                    "claims": claims,
                    "claim_count": len(claims),
                    "raw_analysis": result_text,
                    "method": "qwen-vision"
                }
            
            elif analysis_type == "context":
                return {
                    "context": result_text.strip(),
                    "content_type": self._extract_content_type(result_text),
                    "method": "qwen-vision"
                }
            
            else:  # comprehensive
                # Parse comprehensive output
                sections = self._parse_comprehensive_analysis(result_text)
                return {
                    "extracted_text": sections.get("text_extraction", ""),
                    "claims": sections.get("claims", []),
                    "context": sections.get("context", ""),
                    "priority_claims": sections.get("priority", ""),
                    "raw_analysis": result_text,
                    "has_text": len(sections.get("text_extraction", "")) > 0,
                    "claim_count": len(sections.get("claims", [])),
                    "method": "qwen-vision"
                }
        
        except Exception as e:
            print(f"Error in Qwen Vision analysis: {e}")
            return {
                "error": str(e),
                "extracted_text": "",
                "claims": [],
                "context": ""
            }
    
    def _extract_content_type(self, text: str) -> str:
        """Extract content type from context analysis."""
        text_lower = text.lower()
        if "meme" in text_lower:
            return "meme"
        elif "news" in text_lower or "headline" in text_lower:
            return "news"
        elif "infographic" in text_lower:
            return "infographic"
        elif "screenshot" in text_lower:
            return "screenshot"
        elif "photo" in text_lower:
            return "photo"
        else:
            return "unknown"
    
    def _parse_comprehensive_analysis(self, text: str) -> dict:
        """Parse comprehensive analysis into structured sections."""
        sections = {
            "text_extraction": "",
            "claims": [],
            "context": "",
            "priority": ""
        }
        
        current_section = None
        section_markers = {
            "1. TEXT EXTRACTION": "text_extraction",
            "2. FACTUAL CLAIMS": "claims",
            "3. CONTEXT": "context",
            "4. VERIFICATION PRIORITY": "priority"
        }
        
        lines = text.split('\n')
        current_content = []
        
        for line in lines:
            # Check if line is a section marker
            section_found = False
            for marker, section_key in section_markers.items():
                if marker in line:
                    # Save previous section
                    if current_section and current_content:
                        if current_section == "claims":
                            # Extract claims
                            for claim_line in current_content:
                                if claim_line.strip().startswith('-'):
                                    sections["claims"].append(claim_line.strip()[1:].strip())
                        else:
                            sections[current_section] = '\n'.join(current_content).strip()
                    
                    # Start new section
                    current_section = section_key
                    current_content = []
                    section_found = True
                    break
            
            if not section_found and current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            if current_section == "claims":
                for claim_line in current_content:
                    if claim_line.strip().startswith('-') or 'CLAIM' in claim_line:
                        claim_text = claim_line.strip().lstrip('-').strip()
                        if ':' in claim_text:
                            claim_text = claim_text.split(':', 1)[1].strip()
                        if claim_text:
                            sections["claims"].append(claim_text)
            else:
                sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
