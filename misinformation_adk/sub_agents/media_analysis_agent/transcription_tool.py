from google.adk.tools.base_tool import BaseTool
import speech_recognition as sr
from pydub import AudioSegment
import os

class TranscriptionTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="transcribe_audio",
            description="Transcribes audio to text using speech recognition."
        )
        self.recognizer = sr.Recognizer()
    
    def run(self, audio_path: str, language: str = "en-US") -> dict:
        """
        Transcribes audio file to text.
        
        Args:
            audio_path: Path to audio file
            language: Language code for recognition
            
        Returns:
            Dictionary with transcribed text and metadata
        """
        try:
            # Convert to WAV if needed
            file_ext = os.path.splitext(audio_path)[1].lower()
            
            if file_ext != '.wav':
                # Convert to WAV
                audio = AudioSegment.from_file(audio_path)
                wav_path = audio_path.rsplit('.', 1)[0] + '_temp.wav'
                audio.export(wav_path, format='wav')
                audio_path = wav_path
                temp_file = True
            else:
                temp_file = False
            
            # Load audio
            with sr.AudioFile(audio_path) as source:
                audio_data = self.recognizer.record(source)
                duration = source.DURATION
            
            # Transcribe using Google Speech Recognition (free)
            try:
                text = self.recognizer.recognize_google(audio_data, language=language)
                success = True
                confidence = 0.85  # Google API doesn't return confidence
            except sr.UnknownValueError:
                text = ""
                success = False
                confidence = 0.0
            except sr.RequestError as e:
                return {
                    "error": f"API request failed: {str(e)}",
                    "transcribed_text": "",
                    "success": False
                }
            
            # Clean up temp file
            if temp_file and os.path.exists(wav_path):
                os.remove(wav_path)
            
            return {
                "transcribed_text": text,
                "success": success,
                "confidence": confidence,
                "duration_seconds": duration,
                "language": language,
                "word_count": len(text.split()) if text else 0
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "transcribed_text": "",
                "success": False,
                "confidence": 0.0
            }
