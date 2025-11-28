from google.adk.tools.base_tool import BaseTool
import mimetypes
import os
import base64

class ContentAnalyzerTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="analyze_content_type",
            description="Analyzes incoming content and determines if it's text, image, video, audio, or mixed media."
        )

    def run(self, content: str, file_path: str = None) -> dict:
        """
        Analyzes content type and prepares routing information.
        
        Args:
            content: Text content or base64 encoded media
            file_path: Optional file path for media files
            
        Returns:
            Dictionary with content analysis and routing instructions
        """
        analysis = {
            "content_type": None,
            "has_text": False,
            "has_media": False,
            "media_type": None,
            "route_to": [],
            "original_content": content,
            "file_path": file_path
        }
        
        # Check if file path is provided
        if file_path and os.path.exists(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                if mime_type.startswith('image/'):
                    analysis["content_type"] = "image"
                    analysis["has_media"] = True
                    analysis["media_type"] = "image"
                    analysis["route_to"].append("image_deepfake_agent")
                elif mime_type.startswith('video/'):
                    analysis["content_type"] = "video"
                    analysis["has_media"] = True
                    analysis["media_type"] = "video"
                    analysis["route_to"].append("video_deepfake_agent")
                elif mime_type.startswith('audio/'):
                    analysis["content_type"] = "audio"
                    analysis["has_media"] = True
                    analysis["media_type"] = "audio"
                    analysis["route_to"].append("audio_deepfake_agent")
        
        # Check if there's text content
        if content and len(content.strip()) > 0:
            # Check if it's not just base64 encoded data
            if not self._is_base64(content):
                analysis["has_text"] = True
                if not analysis["content_type"]:
                    analysis["content_type"] = "text"
                else:
                    analysis["content_type"] = "mixed_media"
        
        # Determine routing
        if analysis["has_media"]:
            # Media needs deepfake detection first
            # Then OCR/transcription
            # Then fact checking
            if analysis["media_type"] in ["image", "video"]:
                analysis["route_to"].append("ocr_agent")
            elif analysis["media_type"] == "audio":
                analysis["route_to"].append("transcription_agent")
        
        if analysis["has_text"]:
            # Direct text to preprocessing
            analysis["route_to"].append("preprocessing_agent")
        
        return analysis
    
    def _is_base64(self, s: str) -> bool:
        """Check if string is base64 encoded."""
        try:
            if len(s) < 100:  # Too short to be base64 media
                return False
            base64.b64decode(s[:100])
            return True
        except:
            return False
