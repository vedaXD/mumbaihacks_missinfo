from google.adk.agents.llm_agent import Agent
from .image_deepfake_tool import ImageDeepfakeTool
from .video_deepfake_tool import VideoDeepfakeTool
from .audio_deepfake_tool import AudioDeepfakeTool
from .ocr_tool import OCRTool
from .transcription_tool import TranscriptionTool
from .qwen_vision_tool import QwenVisionTool

root_agent = Agent(
    model='gemini-2.5-flash',
    name='media_analysis_agent',
    description='Detects deepfakes in images, videos, and audio. Performs advanced vision analysis, OCR and transcription.',
    instruction='Analyze media content for authenticity using deepfake detection models. Use Qwen Vision for advanced image understanding, text extraction, and claim detection. Extract text from images/videos via OCR and transcribe audio. Prioritize Qwen Vision for complex images with text overlays, memes, or infographics.',
    tools=[
        ImageDeepfakeTool(),
        VideoDeepfakeTool(),
        AudioDeepfakeTool(),
        QwenVisionTool(),  # Advanced vision analysis for images
        OCRTool(),  # Now uses Qwen Vision + EasyOCR fallback
        TranscriptionTool()
    ],
)
