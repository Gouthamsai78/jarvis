"""
Text to Speech Module
~~~~~~~~~~~~~~~~~~~~~

Provides voice output for Jarvis responses.
"""

import threading
from typing import Optional
from queue import Queue

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

from ..config import VOICE_RESPONSE_ENABLED, SPEECH_RATE


class TextToSpeech:
    """
    Text-to-speech output for Jarvis.
    
    Uses pyttsx3 for offline text-to-speech synthesis.
    
    Example:
        tts = TextToSpeech()
        tts.speak("Hello, I am Jarvis")
        
        # Non-blocking speech
        tts.speak_async("Processing your request")
    """
    
    def __init__(
        self,
        rate: int = SPEECH_RATE,
        enabled: bool = VOICE_RESPONSE_ENABLED,
    ):
        """
        Initialize TTS engine.
        
        Args:
            rate: Speech rate in words per minute.
            enabled: Whether TTS is enabled.
        """
        self.enabled = enabled
        self.rate = rate
        
        self._engine: Optional[pyttsx3.Engine] = None
        self._queue: Queue = Queue()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        
        if PYTTSX3_AVAILABLE and enabled:
            self._init_engine()
    
    def _init_engine(self):
        """Initialize the TTS engine."""
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.rate)
            
            # Get available voices
            voices = self._engine.getProperty("voices")
            
            # Try to use a more natural voice if available
            for voice in voices:
                if "david" in voice.name.lower() or "zira" in voice.name.lower():
                    self._engine.setProperty("voice", voice.id)
                    break
                    
        except Exception as e:
            print(f"Failed to initialize TTS: {e}")
            self._engine = None
    
    def speak(self, text: str):
        """
        Speak text synchronously (blocking).
        
        Args:
            text: Text to speak.
        """
        if not self.enabled or not self._engine:
            print(f"[Jarvis]: {text}")
            return
        
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as e:
            print(f"TTS error: {e}")
            print(f"[Jarvis]: {text}")
    
    def speak_async(self, text: str):
        """
        Speak text asynchronously (non-blocking).
        
        Args:
            text: Text to speak.
        """
        if not self.enabled:
            print(f"[Jarvis]: {text}")
            return
        
        self._queue.put(text)
        
        if not self._running:
            self._start_worker()
    
    def _start_worker(self):
        """Start background speech worker."""
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
    
    def _worker_loop(self):
        """Background worker for async speech."""
        while True:
            try:
                text = self._queue.get(timeout=1.0)
                self.speak(text)
            except:
                if self._queue.empty():
                    self._running = False
                    break
    
    def stop(self):
        """Stop any ongoing speech."""
        if self._engine:
            try:
                self._engine.stop()
            except:
                pass
    
    def set_rate(self, rate: int):
        """Set speech rate."""
        self.rate = rate
        if self._engine:
            self._engine.setProperty("rate", rate)
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        if self._engine:
            self._engine.setProperty("volume", max(0.0, min(1.0, volume)))
    
    @property
    def available(self) -> bool:
        """Check if TTS is available."""
        return PYTTSX3_AVAILABLE and self._engine is not None


# Global TTS instance
_tts_instance: Optional[TextToSpeech] = None


def say(text: str, blocking: bool = False):
    """
    Convenience function to speak text.
    
    Args:
        text: Text to speak.
        blocking: If True, wait for speech to complete.
    """
    global _tts_instance
    
    if _tts_instance is None:
        _tts_instance = TextToSpeech()
    
    if blocking:
        _tts_instance.speak(text)
    else:
        _tts_instance.speak_async(text)
