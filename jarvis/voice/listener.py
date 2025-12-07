"""
Voice Listener Module
~~~~~~~~~~~~~~~~~~~~~

Provides voice input and wake word detection for Jarvis.
"""

import threading
from typing import Optional, Callable
from dataclasses import dataclass

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

from ..config import VOICE_ACTIVATION_KEYWORD


@dataclass
class VoiceCommand:
    """A recognized voice command."""
    
    text: str
    confidence: float
    triggered_by_wake_word: bool


class VoiceListener:
    """
    Voice input listener with wake word detection.
    
    Listens for the wake word "Jarvis" then captures commands.
    
    Example:
        listener = VoiceListener()
        
        @listener.on_command
        def handle_command(command: VoiceCommand):
            print(f"Received: {command.text}")
        
        listener.start()
    """
    
    def __init__(
        self,
        wake_word: str = VOICE_ACTIVATION_KEYWORD,
        timeout: float = 5.0,
        phrase_time_limit: float = 10.0,
    ):
        """
        Initialize voice listener.
        
        Args:
            wake_word: Word to listen for to activate (default: "jarvis").
            timeout: Seconds to wait for speech.
            phrase_time_limit: Maximum seconds for a phrase.
        """
        self.wake_word = wake_word.lower()
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit
        
        self._recognizer: Optional[sr.Recognizer] = None
        self._microphone: Optional[sr.Microphone] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: list[Callable[[VoiceCommand], None]] = []
        self._continuous_mode = False
        
        if SPEECH_RECOGNITION_AVAILABLE:
            self._init_recognizer()
    
    def _init_recognizer(self):
        """Initialize speech recognizer."""
        try:
            self._recognizer = sr.Recognizer()
            self._microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
        except Exception as e:
            print(f"Failed to initialize voice listener: {e}")
            self._recognizer = None
    
    def start(self, continuous: bool = True):
        """
        Start listening for voice commands.
        
        Args:
            continuous: If True, continuously listen. If False, listen once.
        """
        if not SPEECH_RECOGNITION_AVAILABLE:
            print("Speech recognition not available. Install: pip install SpeechRecognition")
            return
        
        if not self._recognizer or not self._microphone:
            print("Voice listener not initialized")
            return
        
        self._continuous_mode = continuous
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print(f"Voice listener started. Say '{self.wake_word}' to activate.")
    
    def stop(self):
        """Stop listening."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
    
    def _listen_loop(self):
        """Main listening loop."""
        while self._running:
            try:
                command = self._listen_once()
                
                if command:
                    for callback in self._callbacks:
                        try:
                            callback(command)
                        except Exception as e:
                            print(f"Callback error: {e}")
                
                if not self._continuous_mode:
                    break
                    
            except Exception as e:
                print(f"Listen error: {e}")
    
    def _listen_once(self) -> Optional[VoiceCommand]:
        """Listen for a single command."""
        if not self._recognizer or not self._microphone:
            return None
        
        try:
            with self._microphone as source:
                print("Listening...")
                audio = self._recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_time_limit,
                )
            
            # Recognize speech
            text = self._recognizer.recognize_google(audio)
            text_lower = text.lower()
            
            # Check for wake word
            triggered = self.wake_word in text_lower
            
            if triggered:
                # Remove wake word from command
                command_text = text_lower.replace(self.wake_word, "").strip()
                
                # If just wake word, wait for follow-up command
                if not command_text:
                    print("Yes?")
                    with self._microphone as source:
                        audio = self._recognizer.listen(
                            source,
                            timeout=self.timeout,
                            phrase_time_limit=self.phrase_time_limit,
                        )
                    command_text = self._recognizer.recognize_google(audio)
                
                return VoiceCommand(
                    text=command_text,
                    confidence=1.0,
                    triggered_by_wake_word=True,
                )
            
            return None
            
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"Speech recognition service error: {e}")
            return None
    
    def listen_for_command(self) -> Optional[str]:
        """
        Listen for a single command (blocking).
        
        Returns:
            The recognized command text, or None if nothing recognized.
        """
        command = self._listen_once()
        return command.text if command else None
    
    def on_command(self, callback: Callable[[VoiceCommand], None]):
        """
        Register a callback for voice commands.
        
        Can be used as a decorator:
        
            @listener.on_command
            def handle(command):
                print(command.text)
        """
        self._callbacks.append(callback)
        return callback
    
    @property
    def available(self) -> bool:
        """Check if voice listening is available."""
        return (
            SPEECH_RECOGNITION_AVAILABLE
            and self._recognizer is not None
            and self._microphone is not None
        )
    
    @property
    def is_running(self) -> bool:
        """Check if listener is running."""
        return self._running
