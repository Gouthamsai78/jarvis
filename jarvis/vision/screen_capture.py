"""
Screen Capture Module
~~~~~~~~~~~~~~~~~~~~~

Handles real-time screen capture for Gemini vision analysis.
"""

import time
import threading
from typing import Optional, Callable
from dataclasses import dataclass
from queue import Queue
import io
import base64

import pyautogui
from PIL import Image
import numpy as np

from ..config import (
    SCREEN_CAPTURE_FPS,
    SCREEN_CAPTURE_QUALITY,
    MAX_IMAGE_DIMENSION,
)


@dataclass
class ScreenFrame:
    """A captured screen frame."""
    
    image: Image.Image
    timestamp: float
    width: int
    height: int
    
    def to_base64(self, quality: int = SCREEN_CAPTURE_QUALITY) -> str:
        """Convert frame to base64 JPEG."""
        buffer = io.BytesIO()
        self.image.save(buffer, format="JPEG", quality=quality)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    def to_numpy(self) -> np.ndarray:
        """Convert frame to numpy array (RGB)."""
        return np.array(self.image)


class ScreenCapture:
    """
    Real-time screen capture for vision analysis.
    
    Captures screen frames at a configurable rate and provides them
    for Gemini vision processing.
    
    Example:
        capture = ScreenCapture()
        capture.start()
        
        while True:
            frame = capture.get_latest_frame()
            if frame:
                # Send to Gemini for analysis
                base64_img = frame.to_base64()
                response = gemini.analyze(base64_img)
        
        capture.stop()
    """
    
    def __init__(
        self,
        fps: float = SCREEN_CAPTURE_FPS,
        max_dimension: int = MAX_IMAGE_DIMENSION,
        region: Optional[tuple] = None,
    ):
        """
        Initialize screen capture.
        
        Args:
            fps: Frames per second to capture.
            max_dimension: Maximum image dimension (will resize if larger).
            region: Optional (x, y, width, height) to capture specific region.
        """
        self.fps = fps
        self.max_dimension = max_dimension
        self.region = region
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._latest_frame: Optional[ScreenFrame] = None
        self._frame_queue: Queue = Queue(maxsize=3)
        self._callbacks: list[Callable[[ScreenFrame], None]] = []
    
    def start(self):
        """Start screen capture in background thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop screen capture."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
    
    def _capture_loop(self):
        """Main capture loop running in background thread."""
        interval = 1.0 / self.fps
        
        while self._running:
            start_time = time.time()
            
            try:
                frame = self._capture_frame()
                self._latest_frame = frame
                
                # Add to queue (non-blocking)
                if not self._frame_queue.full():
                    self._frame_queue.put_nowait(frame)
                
                # Call callbacks
                for callback in self._callbacks:
                    try:
                        callback(frame)
                    except Exception:
                        pass
                        
            except Exception as e:
                print(f"Screen capture error: {e}")
            
            # Maintain frame rate
            elapsed = time.time() - start_time
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _capture_frame(self) -> ScreenFrame:
        """Capture a single frame."""
        # Take screenshot
        if self.region:
            screenshot = pyautogui.screenshot(region=self.region)
        else:
            screenshot = pyautogui.screenshot()
        
        # Resize if needed
        if max(screenshot.size) > self.max_dimension:
            ratio = self.max_dimension / max(screenshot.size)
            new_size = (
                int(screenshot.width * ratio),
                int(screenshot.height * ratio),
            )
            screenshot = screenshot.resize(new_size, Image.LANCZOS)
        
        return ScreenFrame(
            image=screenshot,
            timestamp=time.time(),
            width=screenshot.width,
            height=screenshot.height,
        )
    
    def get_latest_frame(self) -> Optional[ScreenFrame]:
        """Get the most recent captured frame."""
        return self._latest_frame
    
    def get_frame(self, timeout: float = 1.0) -> Optional[ScreenFrame]:
        """Get a frame from the queue (blocking)."""
        try:
            return self._frame_queue.get(timeout=timeout)
        except:
            return None
    
    def capture_now(self) -> ScreenFrame:
        """Capture a frame immediately (synchronous)."""
        return self._capture_frame()
    
    def on_frame(self, callback: Callable[[ScreenFrame], None]):
        """Register a callback to be called on each new frame."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Remove a previously registered callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    @property
    def is_running(self) -> bool:
        """Check if capture is running."""
        return self._running
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()
