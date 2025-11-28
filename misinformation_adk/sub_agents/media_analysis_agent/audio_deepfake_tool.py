from google.adk.tools.base_tool import BaseTool
import librosa
import numpy as np
import pickle
import os
import speech_recognition as speech_rec
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("⚠️ pydub not available, using librosa for audio conversion")

class AudioDeepfakeTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="detect_audio_deepfake",
            description="Detects AI-generated or manipulated audio using custom ML model and transcribes content for fact-checking."
        )
        # Load custom .pkl audio deepfake classifier
        pkl_path = os.path.join(os.path.dirname(__file__), '..', '..', 'audio_deepfake_classifier.pkl')
        try:
            with open(pkl_path, 'rb') as f:
                model_dict = pickle.load(f)
            
            # Extract components from dictionary
            self.classifier = model_dict.get('classifier')
            self.scaler = model_dict.get('scaler')
            self.feature_count = model_dict.get('feature_count', 26)
            self.labels = model_dict.get('labels', {0: 'real', 1: 'fake'})
            
            print(f"✓ Custom audio deepfake model loaded from: {os.path.basename(pkl_path)}")
            print(f"   Classifier: {type(self.classifier).__name__}")
            print(f"   Expected features: {self.feature_count}")
            print(f"   Labels: {self.labels}")
        except Exception as e:
            print(f"⚠️ Warning: Could not load custom .pkl model: {e}")
            self.classifier = None
            self.scaler = None
            self.feature_count = 26
            self.labels = {0: 'real', 1: 'fake'}
        
        # Initialize speech recognizer for transcription
        self.recognizer = speech_rec.Recognizer()
    
    def run(self, audio_path: str = None, sample_rate: int = 16000) -> dict:
        """
        Analyzes audio for deepfake indicators AND transcribes for fact-checking.
        
        Args:
            audio_path: Path to audio file
            sample_rate: Target sample rate for analysis
            
        Returns:
            Dictionary with deepfake analysis + transcribed text
        """
        try:
            # Validate input
            if not audio_path:
                return {
                    "error": "No audio file path provided",
                    "is_deepfake": None,
                    "confidence": 0.0,
                    "transcribed_text": "",
                    "model_loaded": self.classifier is not None
                }
            
            print(f"  → Analyzing audio: {os.path.basename(audio_path)}")
            
            # Step 1: TRANSCRIBE AUDIO for fact-checking
            transcribed_text = self._transcribe_audio(audio_path)
            print(f"  → Transcribed: {len(transcribed_text)} characters")
            
            # Step 2: DEEPFAKE DETECTION using custom .pkl model
            is_deepfake, confidence = self._detect_deepfake(audio_path, sample_rate)
            
            # Step 3: Get audio duration
            audio_data, sr = librosa.load(audio_path, sr=sample_rate)
            duration = len(audio_data) / sr
            
            return {
                "is_deepfake": is_deepfake,
                "confidence": confidence,
                "authenticity_score": 1.0 - confidence if is_deepfake else confidence,
                "transcribed_text": transcribed_text,  # For fact-checking
                "duration_seconds": duration,
                "sample_rate": sr,
                "analysis": "Real audio" if not is_deepfake else "Potential AI-generated/deepfake audio",
                "model_loaded": self.classifier is not None
            }
            
        except Exception as e:
            print(f"  ⚠️ Audio analysis error: {e}")
            return {
                "error": str(e),
                "is_deepfake": None,
                "confidence": 0.0,
                "transcribed_text": ""
            }
    
    def _transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio to text using Google Speech Recognition."""
        wav_path = None
        try:
            file_ext = os.path.splitext(audio_path)[1].lower()
            print(f"  → Preparing {file_ext} for transcription...")
            
            # Method 1: Try librosa (most reliable, no ffmpeg needed)
            try:
                audio_data, sr = librosa.load(audio_path, sr=16000, mono=True)
                wav_path = audio_path.rsplit('.', 1)[0] + '_temp_transcript.wav'
                import soundfile as sf
                sf.write(wav_path, audio_data, 16000)
                print(f"  ✓ Converted using librosa")
            except Exception as e1:
                print(f"  ⚠️ Librosa conversion failed: {e1}")
                
                # Method 2: Try pydub if available
                if PYDUB_AVAILABLE:
                    try:
                        if file_ext in ['.mp3']:
                            audio = AudioSegment.from_mp3(audio_path)
                        elif file_ext in ['.m4a', '.aac']:
                            audio = AudioSegment.from_file(audio_path, format='m4a')
                        elif file_ext in ['.ogg']:
                            audio = AudioSegment.from_ogg(audio_path)
                        elif file_ext in ['.flac']:
                            audio = AudioSegment.from_file(audio_path, format='flac')
                        elif file_ext in ['.wav']:
                            audio = AudioSegment.from_wav(audio_path)
                        else:
                            audio = AudioSegment.from_file(audio_path)
                        
                        wav_path = audio_path.rsplit('.', 1)[0] + '_temp_transcript.wav'
                        audio = audio.set_frame_rate(16000).set_channels(1)
                        audio.export(wav_path, format='wav')
                        print(f"  ✓ Converted using pydub")
                    except Exception as e2:
                        print(f"  ❌ Both conversions failed. Librosa: {e1}, Pydub: {e2}")
                        return ""
                else:
                    print(f"  ❌ Conversion failed and pydub not available")
                    return ""
            
            # Transcribe
            with speech_rec.AudioFile(wav_path) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = self.recognizer.record(source)
            
            text = self.recognizer.recognize_google(audio_data)
            print(f"  ✓ Transcribed: '{text[:50]}...' ({len(text)} chars)")
            return text
            
        except speech_rec.UnknownValueError:
            print("  ℹ️ No speech detected in audio")
            return ""
        except speech_rec.RequestError as e:
            print(f"  ⚠️ Speech API error: {e}")
            return ""
        except Exception as e:
            print(f"  ⚠️ Transcription error: {e}")
            import traceback
            traceback.print_exc()
            return ""
        finally:
            if wav_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except:
                    pass
    
    def _detect_deepfake(self, audio_path: str, sample_rate: int) -> tuple:
        """
        Detect if audio is deepfake using custom .pkl model.
        
        Returns:
            (is_deepfake: bool, confidence: float)
        """
        try:
            if not self.classifier:
                print("  ℹ️ No classifier loaded, skipping deepfake detection")
                return False, 0.0
            
            print(f"  → Loading audio with librosa...")
            # Load audio with librosa (handles most formats)
            try:
                audio, sr = librosa.load(audio_path, sr=sample_rate)
                print(f"  ✓ Audio loaded: {len(audio)} samples at {sr}Hz")
            except Exception as e:
                print(f"  ⚠️ Librosa load failed: {e}")
                # Try converting with pydub first
                file_ext = os.path.splitext(audio_path)[1].lower()
                temp_wav = audio_path.rsplit('.', 1)[0] + '_temp_analysis.wav'
                
                try:
                    audio_seg = AudioSegment.from_file(audio_path)
                    audio_seg.export(temp_wav, format='wav')
                    audio, sr = librosa.load(temp_wav, sr=sample_rate)
                    os.remove(temp_wav)
                    print(f"  ✓ Audio converted and loaded: {len(audio)} samples")
                except Exception as e2:
                    print(f"  ⚠️ Audio conversion failed: {e2}")
                    return False, 0.0
            
            # Extract features
            print(f"  → Extracting audio features...")
            features = self._extract_audio_features(audio, sr)
            print(f"  ✓ Extracted {len(features)} features")
            
            # Ensure feature count matches
            if len(features) != self.feature_count:
                print(f"  ⚠️ Feature mismatch: expected {self.feature_count}, got {len(features)}")
                # Pad or truncate
                if len(features) < self.feature_count:
                    features = np.pad(features, (0, self.feature_count - len(features)))
                else:
                    features = features[:self.feature_count]
            
            # Scale features if scaler is available
            if self.scaler:
                features = self.scaler.transform([features])[0]
                print(f"  ✓ Features scaled")
            
            # Get prediction
            print(f"  → Running deepfake classifier...")
            if hasattr(self.classifier, 'predict_proba'):
                # Get probability scores
                proba = self.classifier.predict_proba([features])[0]
                predicted_class = int(np.argmax(proba))
                confidence = float(proba[predicted_class])
            else:
                # Fallback to simple prediction
                prediction = self.classifier.predict([features])[0]
                predicted_class = int(prediction)
                confidence = 0.85  # Default confidence
            
            # Determine if deepfake based on labels
            # Check what label is assigned to class 1
            is_deepfake = (predicted_class == 1 and self.labels.get(1, 'fake').lower() in ['fake', 'deepfake', 'ai'])
            
            label = self.labels.get(predicted_class, 'unknown')
            print(f"  ✓ Deepfake detection: {label.upper()} (class {predicted_class}, confidence: {confidence:.2%})")
            
            return is_deepfake, confidence
            
        except Exception as e:
            print(f"  ⚠️ Deepfake detection error: {e}")
            import traceback
            traceback.print_exc()
            return False, 0.0
    
    def _extract_audio_features(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Extract audio features for ML model.
        Model expects 54 features.
        """
        try:
            # 1. MFCCs (20 coefficients)
            mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=20)
            mfccs_mean = np.mean(mfccs, axis=1)
            
            # 2. Spectral features (6 features)
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))
            spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio, sr=sr))
            spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=audio, sr=sr))
            spectral_contrast = np.mean(librosa.feature.spectral_contrast(y=audio, sr=sr))
            spectral_flatness = np.mean(librosa.feature.spectral_flatness(y=audio))
            
            # 3. Zero crossing rate
            zcr = np.mean(librosa.feature.zero_crossing_rate(audio))
            
            # 4. Chroma features (12 features)
            chroma = np.mean(librosa.feature.chroma_stft(y=audio, sr=sr), axis=1)
            
            # 5. Mel spectrogram features (4 features)
            mel_spec = librosa.feature.melspectrogram(y=audio, sr=sr)
            mel_mean = np.mean(mel_spec)
            mel_std = np.std(mel_spec)
            mel_min = np.min(mel_spec)
            mel_max = np.max(mel_spec)
            
            # 6. Tonnetz (6 features)
            tonnetz = librosa.feature.tonnetz(y=audio, sr=sr)
            tonnetz_mean = np.mean(tonnetz, axis=1)
            
            # 7. RMS energy
            rms = np.mean(librosa.feature.rms(y=audio))
            
            # Combine all features (20 + 6 + 1 + 12 + 4 + 6 + 1 = 50, pad to 54)
            features = np.concatenate([
                mfccs_mean,                                              # 20
                [spectral_centroid, spectral_rolloff, spectral_bandwidth, 
                 spectral_contrast, spectral_flatness, zcr],             # 6
                chroma,                                                  # 12
                [mel_mean, mel_std, mel_min, mel_max],                   # 4
                tonnetz_mean,                                            # 6
                [rms],                                                   # 1
                [0, 0, 0, 0, 0]                                          # Pad to 54
            ])
            
            return features
            
        except Exception as e:
            print(f"  ⚠️ Feature extraction error: {e}")
            import traceback
            traceback.print_exc()
            # Return zeros if extraction fails
            return np.zeros(54)  # Match model's expected input
