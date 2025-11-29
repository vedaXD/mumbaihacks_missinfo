"""
Video Composer Agent - Creates synced video reels with images and audio
"""

import logging
import tempfile
import os
from pathlib import Path

# Try to import TTS, make it optional
try:
    from google.cloud import texttospeech
    TTS_AVAILABLE = True
except ImportError:
    texttospeech = None
    TTS_AVAILABLE = False

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip, TextClip, CompositeVideoClip
import numpy as np
from PIL import Image
import io

logger = logging.getLogger(__name__)

class VideoComposerAgent:
    """Agent that composes video reels with synced images and TTS audio"""
    
    def __init__(self, project_id: str):
        """
        Initialize the Video Composer Agent
        
        Args:
            project_id: Google Cloud project ID
        """
        self.project_id = project_id
        
        # Initialize Text-to-Speech client
        if TTS_AVAILABLE:
            try:
                self.tts_client = texttospeech.TextToSpeechClient()
                logger.info("🎙️ Video Composer initialized with Google TTS")
            except Exception as e:
                logger.warning(f"⚠️ TTS client initialization failed: {e}")
                self.tts_client = None
        else:
            logger.warning("⚠️ Google Cloud TTS not available - using silent audio")
            self.tts_client = None
    
    def generate_audio(self, text: str, scene_number: int) -> bytes:
        """
        Generate audio from text using Google TTS
        
        Args:
            text: The text to convert to speech
            scene_number: Scene number for logging
            
        Returns:
            Audio bytes (MP3 format)
        """
        if not self.tts_client:
            logger.error(f"❌ TTS client not available for scene {scene_number}")
            return self._generate_silent_audio(3)
        
        logger.info(f"🎙️ Generating audio for scene {scene_number}: {text[:50]}...")
        
        try:
            # Set up the text input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configure voice (English, neutral, professional news voice)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Neural2-J",  # Professional male voice
                ssml_gender=texttospeech.SsmlVoiceGender.MALE
            )
            
            # Configure audio format
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=0.0
            )
            
            # Generate speech
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            logger.info(f"✅ Audio generated for scene {scene_number} ({len(response.audio_content)} bytes)")
            return response.audio_content
            
        except Exception as e:
            logger.error(f"❌ Error generating audio for scene {scene_number}: {e}")
            return self._generate_silent_audio(3)
    
    def compose_video(self, scenes: list, output_path: str = None) -> str:
        """
        Compose final video with synced images and audio
        
        Args:
            scenes: List of scene dictionaries with 'image_bytes', 'narration', 'duration'
            output_path: Optional output path for video file
            
        Returns:
            Path to the generated video file
        """
        logger.info(f"🎬 Composing video with {len(scenes)} scenes...")
        
        if output_path is None:
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"reel_{os.urandom(8).hex()}.mp4")
        
        try:
            video_clips = []
            audio_clips = []
            current_time = 0
            
            for scene in scenes:
                scene_number = scene.get('scene_number', 1)
                image_bytes = scene.get('image_bytes')
                narration = scene.get('narration', '')
                duration = scene.get('duration', 4)
                
                logger.info(f"🎞️ Processing scene {scene_number}...")
                
                # Save image to temporary file
                img = Image.open(io.BytesIO(image_bytes))
                img_array = np.array(img)
                
                # Generate audio for this scene
                audio_bytes = self.generate_audio(narration, scene_number)
                
                # Save audio to temporary file
                temp_audio_path = os.path.join(tempfile.gettempdir(), f"audio_{scene_number}.mp3")
                with open(temp_audio_path, 'wb') as f:
                    f.write(audio_bytes)
                
                # Load audio to get its actual duration
                audio_clip = AudioFileClip(temp_audio_path)
                actual_duration = max(audio_clip.duration, duration)
                
                # Create image clip with the duration of audio
                image_clip = ImageClip(img_array, duration=actual_duration)
                
                # Set audio start time
                audio_clip = audio_clip.set_start(current_time)
                
                video_clips.append(image_clip)
                audio_clips.append(audio_clip)
                
                current_time += actual_duration
                
                # Clean up temp audio file
                try:
                    os.remove(temp_audio_path)
                except:
                    pass
            
            # Concatenate all video clips
            logger.info("🔗 Concatenating video clips...")
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # Add "Vishwas Netra" watermark
            logger.info("🏷️ Adding Vishwas Netra watermark...")
            try:
                watermark = TextClip(
                    "Vishwas Netra",
                    fontsize=32,
                    color='white',
                    font='Arial-Bold',
                    stroke_color='black',
                    stroke_width=2
                ).set_position(('right', 'top')).set_duration(final_video.duration).margin(right=20, top=20, opacity=0)
                
                final_video = CompositeVideoClip([final_video, watermark])
            except Exception as e:
                logger.warning(f"⚠️ Could not add watermark (font may be missing): {e}")
                # Continue without watermark if TextClip fails
            
            # Combine all audio clips
            logger.info("🔊 Composing audio track...")
            final_audio = CompositeAudioClip(audio_clips)
            
            # Set audio to video
            final_video = final_video.set_audio(final_audio)
            
            # Write final video
            logger.info(f"💾 Writing video to {output_path}...")
            final_video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=os.path.join(tempfile.gettempdir(), 'temp-audio.m4a'),
                remove_temp=True,
                logger=None  # Suppress moviepy's verbose logging
            )
            
            # Clean up
            final_video.close()
            for clip in video_clips:
                clip.close()
            for clip in audio_clips:
                clip.close()
            
            logger.info(f"✅ Video composed successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error composing video: {type(e).__name__}: {e}")
            raise
    
    def _generate_silent_audio(self, duration: float) -> bytes:
        """Generate silent audio of specified duration"""
        import io
        from pydub import AudioSegment
        
        silent = AudioSegment.silent(duration=int(duration * 1000))
        buffer = io.BytesIO()
        silent.export(buffer, format="mp3")
        return buffer.getvalue()
