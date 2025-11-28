from google.adk.agents.llm_agent import Agent
from .image_deepfake_tool import ImageDeepfakeTool
from .video_deepfake_tool import VideoDeepfakeTool
from .audio_deepfake_tool import AudioDeepfakeTool
from .ocr_tool import OCRTool
from .transcription_tool import TranscriptionTool

root_agent = Agent(
    model='gemini-2.5-flash',
    name='media_analysis_agent',
    description='Detects deepfakes in images, videos, and audio. Performs OCR and transcription.',
    instruction='Analyze media content for authenticity using deepfake detection models. Extract text from images/videos via OCR and transcribe audio.',
    tools=[
        ImageDeepfakeTool(),
        VideoDeepfakeTool(),
        AudioDeepfakeTool(),
        OCRTool(),
        TranscriptionTool()
    ],
)
