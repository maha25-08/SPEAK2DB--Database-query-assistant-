"""
Voice Recognition Service for Query Console
Handles speech-to-text conversion with multiple backend options.
"""

import logging
import json
from typing import Optional, Dict, Any
import threading
import queue

try:
    import speech_recognition as sr
    _SPEECH_AVAILABLE = True
except ImportError:
    _SPEECH_AVAILABLE = False
    logging.warning("SpeechRecognition not available - voice input disabled")

logger = logging.getLogger(__name__)

class VoiceRecognitionService:
    """Advanced voice recognition service with multiple backends."""
    
    def __init__(self):
        self.recognizer = sr.Recognizer() if _SPEECH_AVAILABLE else None
        self.microphone = sr.Microphone() if _SPEECH_AVAILABLE else None
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.current_thread = None
        
        # Configure recognizer for noisy environments
        if self.recognizer:
            self.recognizer.energy_threshold = 300  # Lower threshold for noisy environments
            self.recognizer.dynamic_energy_threshold = True  # Enable dynamic adjustment
            self.recognizer.pause_threshold = 0.8  # Shorter pause for noisy environments
            self.recognizer.operation_timeout = 5
            self.recognizer.phrase_threshold = 0.1  # Lower threshold for noisy environments
            self.recognizer.non_speaking_duration = 0.3  # Shorter non-speaking duration
            self.recognizer.dynamic_energy_adjustment_damping = 0.15  # Faster adjustment
            self.recognizer.dynamic_energy_ratio = 1.5  # More sensitive adjustment
    
    def start_listening(self, callback=None):
        """Start listening for voice input."""
        if not _SPEECH_AVAILABLE:
            return {
                "success": False,
                "error": "Speech recognition not available",
                "message": "Please install SpeechRecognition library: pip install SpeechRecognition"
            }
        
        if self.is_listening:
            return {
                "success": False,
                "error": "Already listening",
                "message": "Voice recognition is already active"
            }
        
        try:
            self.is_listening = True
            self.current_thread = threading.Thread(
                target=self._listen_loop,
                args=(callback,),
                daemon=True
            )
            self.current_thread.start()
            
            logger.info("Voice recognition started")
            return {
                "success": True,
                "message": "Voice recognition started",
                "status": "listening"
            }
            
        except Exception as e:
            logger.error(f"Failed to start voice recognition: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to start voice recognition"
            }
    
    def stop_listening(self):
        """Stop listening for voice input."""
        if not self.is_listening:
            return {"success": True, "message": "Not listening"}
        
        self.is_listening = False
        if self.current_thread and self.current_thread.is_alive():
            self.current_thread.join(timeout=1)
        
        logger.info("Voice recognition stopped")
        return {
            "success": True,
            "message": "Voice recognition stopped",
            "status": "stopped"
        }
    
    def _listen_loop(self, callback):
        """Main listening loop with enhanced noise handling."""
        if not self.recognizer or not self.microphone:
            return
        
        try:
            with self.microphone as source:
                logger.info("Adjusting for ambient noise in noisy environment...")
                # Extended noise adjustment for better background noise handling
                self.recognizer.adjust_for_ambient_noise(source, duration=3)
                
                # Additional noise calibration
                logger.info("Calibrating for speech patterns...")
                
                while self.is_listening:
                    try:
                        logger.info("Listening for speech (noise-aware mode)...")
                        # Enhanced listen parameters for noisy environments
                        audio = self.recognizer.listen(
                            source, 
                            timeout=3,  # Shorter timeout
                            phrase_time_limit=8,  # Longer phrase time
                            snowboy_detector=None  # Disable snowboy for better accuracy
                        )
                        
                        if audio:
                            # Multiple attempts with different engines
                            self._process_audio_with_retry(audio, callback, max_retries=3)
                            
                    except sr.WaitTimeoutError:
                        logger.debug("Listening timeout - continuing...")
                        continue
                    except sr.UnknownValueError:
                        logger.debug("Could not understand audio (may be background noise)")
                        if callback:
                            callback({
                                "type": "noise_detected",
                                "message": "Background noise detected - please speak clearly",
                                "suggestion": "Try moving to a quieter area or speak louder"
                            })
                        continue
                    except sr.RequestError as e:
                        logger.error(f"Speech recognition service error: {e}")
                        if callback:
                            callback({
                                "type": "error",
                                "message": f"Speech recognition service error: {e}",
                                "suggestion": "Please check your internet connection"
                            })
                        break
                    except Exception as e:
                        logger.error(f"Unexpected error in listening loop: {e}")
                        break
                        
        except Exception as e:
            logger.error(f"Error initializing microphone: {e}")
            if callback:
                callback({
                    "type": "error",
                    "message": f"Microphone initialization error: {e}",
                    "suggestion": "Please check your microphone permissions"
                })
    
    def _process_audio_with_retry(self, audio, callback, max_retries=3):
        """Process audio with multiple retry attempts and noise filtering."""
        if not self.recognizer:
            return
        
        # Try multiple recognition engines with noise handling
        engines = [
            ("Google Cloud", self._try_google_with_noise_filter),
            ("Whisper", self._try_whisper_with_noise_filter),
            ("Sphinx", self._try_sphinx_with_noise_filter),
            ("Vosk", self._try_vosk_with_noise_filter)
        ]
        
        for attempt in range(max_retries):
            for engine_name, recognize_func in engines:
                try:
                    text = recognize_func(audio, attempt=attempt)
                    
                    if text and self._is_valid_speech(text):
                        confidence = self._calculate_confidence(text, engine_name)
                        logger.info(f"Recognized text using {engine_name} (attempt {attempt + 1}): {text}")
                        
                        if callback:
                            callback({
                                "type": "transcription",
                                "text": text.strip(),
                                "engine": engine_name,
                                "confidence": confidence,
                                "attempts": attempt + 1,
                                "noise_level": self._assess_noise_level(audio)
                            })
                        return
                        
                except Exception as e:
                    logger.debug(f"{engine_name} recognition failed (attempt {attempt + 1}): {e}")
                    continue
        
        # If all engines failed
        if callback:
            callback({
                "type": "error",
                "message": "Could not recognize speech with any engine",
                "suggestion": "Please try speaking more clearly or reduce background noise",
                "attempts": max_retries
            })
    
    def _is_valid_speech(self, text: str) -> bool:
        """Validate if recognized text is actual speech, not noise."""
        if not text or len(text.strip()) < 2:
            return False
        
        # Filter out common noise patterns
        noise_patterns = [
            r'^[hm]+$',  # Hmmm, hmmmm
            r'^[uh]+$',  # Uh, uhh
            r'^[ah]+$',  # Ah, ahh
            r'^[mm]+$',  # Mmm, mmmm
            r'^[\s\-\s]+$',  # Just dashes/spaces
            r'^[\.]+$',  # Just dots
        ]
        
        text_lower = text.lower().strip()
        for pattern in noise_patterns:
            if re.match(pattern, text_lower):
                return False
        
        return True
    
    def _calculate_confidence(self, text: str, engine: str) -> str:
        """Calculate confidence based on text quality and engine."""
        confidence_scores = {
            "Google Cloud": "high",
            "Whisper": "high", 
            "Sphinx": "medium",
            "Vosk": "medium"
        }
        
        base_confidence = confidence_scores.get(engine, "medium")
        
        # Adjust confidence based on text characteristics
        if len(text.strip()) < 5:
            return "low"  # Short text might be partial recognition
        elif len(text.strip()) > 20:
            return "medium"  # Very long text might include noise
        elif any(char in text for char in ['?', '!', '.', ',']):
            return base_confidence  # Punctuation suggests complete sentence
        else:
            return base_confidence
    
    def _assess_noise_level(self, audio) -> str:
        """Assess the noise level in audio."""
        try:
            # Simple noise assessment based on audio properties
            audio_data = audio.get_raw_data()
            if audio_data:
                # Calculate basic audio statistics
                sample_rate = audio.sample_rate
                samples = len(audio_data)
                
                # Simple RMS calculation for noise level
                import math
                rms = math.sqrt(sum(sample**2 for sample in audio_data) / samples)
                
                if rms < 100:
                    return "low"
                elif rms < 500:
                    return "medium"
                else:
                    return "high"
        except:
            return "unknown"
    
    def _try_google_with_noise_filter(self, audio, attempt=0):
        """Try Google recognition with noise filtering."""
        try:
            # Adjust recognition parameters based on attempt
            if attempt == 0:
                # First attempt - standard settings
                return self.recognizer.recognize_google(audio)
            elif attempt == 1:
                # Second attempt - more permissive
                return self.recognizer.recognize_google(audio, show_all=True)
            else:
                # Third attempt - even more permissive
                return self.recognizer.recognize_google(audio, show_all=True, with_confidence=True)
        except:
            raise sr.RequestError("Google recognition failed")
    
    def _try_whisper_with_noise_filter(self, audio, attempt=0):
        """Try Whisper with noise filtering."""
        try:
            # Convert audio to WAV format
            wav_data = audio.get_wav_data()
            
            # Use OpenAI Whisper (requires API key)
            import openai
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=("audio.wav", wav_data, "audio/wav"),
                language="en",
                temperature=0.1 + (attempt * 0.1),  # Increase temperature with attempts
                response_format="json"
            )
            return response["text"]
            
        except ImportError:
            logger.debug("OpenAI not available for Whisper")
            raise sr.RequestError("Whisper not available")
        except Exception as e:
            logger.debug(f"Whisper recognition failed (attempt {attempt}): {e}")
            raise sr.RequestError(f"Whisper failed: {e}")
    
    def _try_sphinx_with_noise_filter(self, audio, attempt=0):
        """Try Sphinx with noise filtering."""
        try:
            if attempt == 0:
                return self.recognizer.recognize_sphinx(audio)
            else:
                # Try with different language models
                return self.recognizer.recognize_sphinx(audio, language="en-US")
        except:
            raise sr.RequestError("Sphinx recognition failed")
    
    def _try_vosk_with_noise_filter(self, audio, attempt=0):
        """Try Vosk with noise filtering."""
        try:
            import speech_recognition as sr
            # Try Vosk if available
            return self.recognizer.recognize_vosk(audio)
        except:
            raise sr.RequestError("Vosk recognition failed")
    
    def _process_audio(self, audio, callback):
        """Process audio and convert to text."""
        if not self.recognizer:
            return
        
        try:
            # Try multiple recognition engines
            text = None
            engines = [
                ("Google", self.recognizer.recognize_google),
                ("Whisper", self._try_whisper),
                ("Sphinx", self.recognizer.recognize_sphinx)
            ]
            
            for engine_name, recognize_func in engines:
                try:
                    if engine_name == "Whisper":
                        text = recognize_func(audio)
                    else:
                        text = recognize_func(audio)
                    
                    if text and text.strip():
                        logger.info(f"Recognized text using {engine_name}: {text}")
                        
                        if callback:
                            callback({
                                "type": "transcription",
                                "text": text.strip(),
                                "engine": engine_name,
                                "confidence": "high" if engine_name == "Google" else "medium"
                            })
                        return
                        
                except Exception as e:
                    logger.debug(f"{engine_name} recognition failed: {e}")
                    continue
            
            # If all engines failed
            if not text:
                if callback:
                    callback({
                        "type": "error",
                        "message": "Could not recognize speech with any engine",
                        "suggestion": "Please try speaking more clearly or check microphone"
                    })
                    
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            if callback:
                callback({
                    "type": "error",
                    "message": f"Error processing audio: {e}",
                    "suggestion": "Please try again"
                })
    
    def _try_whisper(self, audio):
        """Try Whisper API for speech recognition."""
        try:
            # Convert audio to WAV format
            wav_data = audio.get_wav_data()
            
            # Use OpenAI Whisper (requires API key)
            import openai
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=("audio.wav", wav_data, "audio/wav")
            )
            return response["text"]
            
        except ImportError:
            logger.debug("OpenAI not available for Whisper")
            raise sr.RequestError("OpenAI Whisper not available")
        except Exception as e:
            logger.debug(f"Whisper recognition failed: {e}")
            raise sr.RequestError(f"Whisper failed: {e}")
    
    def get_status(self):
        """Get current voice recognition status."""
        return {
            "available": _SPEECH_AVAILABLE,
            "listening": self.is_listening,
            "microphone_available": self.microphone is not None,
            "engines": ["Google", "Whisper", "Sphinx"] if _SPEECH_AVAILABLE else []
        }
    
    def test_microphone(self):
        """Test microphone functionality."""
        if not _SPEECH_AVAILABLE:
            return {
                "success": False,
                "error": "Speech recognition not available"
            }
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Microphone test successful")
                return {
                    "success": True,
                    "message": "Microphone test successful",
                    "energy_threshold": self.recognizer.energy_threshold
                }
        except Exception as e:
            logger.error(f"Microphone test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Microphone test failed"
            }
    
    def adjust_sensitivity(self, energy_threshold=None, dynamic_threshold=None):
        """Adjust microphone sensitivity."""
        if not self.recognizer:
            return {"success": False, "error": "Recognizer not available"}
        
        try:
            if energy_threshold is not None:
                self.recognizer.energy_threshold = energy_threshold
            if dynamic_threshold is not None:
                self.recognizer.dynamic_energy_threshold = dynamic_threshold
            
            logger.info(f"Adjusted sensitivity - Energy: {self.recognizer.energy_threshold}, Dynamic: {self.recognizer.dynamic_energy_threshold}")
            return {
                "success": True,
                "message": "Sensitivity adjusted",
                "energy_threshold": self.recognizer.energy_threshold,
                "dynamic_threshold": self.recognizer.dynamic_energy_threshold
            }
        except Exception as e:
            logger.error(f"Failed to adjust sensitivity: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global voice recognition service
voice_service = VoiceRecognitionService()


def get_voice_service():
    """Get the global voice recognition service."""
    return voice_service


def is_voice_available():
    """Check if voice recognition is available."""
    return _SPEECH_AVAILABLE


def init_voice_service():
    """Initialize voice recognition service."""
    global voice_service
    if _SPEECH_AVAILABLE:
        logger.info("Voice recognition service initialized")
    else:
        logger.warning("Voice recognition service not available - SpeechRecognition library missing")
