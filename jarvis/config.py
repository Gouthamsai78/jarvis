"""
Jarvis Configuration
~~~~~~~~~~~~~~~~~~~~

Central configuration for all Jarvis modules.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# API Configuration
# =============================================================================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"

# =============================================================================
# Gesture Recognition Settings (ULTIMATE LAZY MODE!)
# =============================================================================
# Confidence threshold for hand detection (0.0 - 1.0)
# Super low = detects hands even with poor lighting/weird angles
GESTURE_CONFIDENCE_THRESHOLD = 0.4

# Minimum tracking confidence for MediaPipe
# Very low = tracks hands even when partially visible
TRACKING_CONFIDENCE = 0.3

# Cursor movement smoothing (0.0 = no smoothing, 1.0 = max smoothing)
# Low = cursor responds instantly to hand movement
CURSOR_SMOOTHING_FACTOR = 0.2

# Screen margin - cursor won't go beyond these margins (pixels)
# Small = more screen coverage with less hand movement
SCREEN_MARGIN = 30

# Gesture hold time for activation (seconds)
# Very short = gestures activate almost instantly
GESTURE_HOLD_TIME = 0.05

# =============================================================================
# Screen Capture Settings
# =============================================================================
# Frames per second for screen capture
SCREEN_CAPTURE_FPS = 1

# JPEG quality for screen captures (1-100)
SCREEN_CAPTURE_QUALITY = 80

# Maximum image dimension for Gemini (will resize if larger)
MAX_IMAGE_DIMENSION = 1024

# =============================================================================
# Voice Settings
# =============================================================================
# Wake word to activate Jarvis
VOICE_ACTIVATION_KEYWORD = "jarvis"

# Enable text-to-speech responses
VOICE_RESPONSE_ENABLED = True

# Speech rate (words per minute)
SPEECH_RATE = 175

# =============================================================================
# UI Settings
# =============================================================================
# Show gesture preview window
SHOW_GESTURE_PREVIEW = True

# Preview window size
PREVIEW_WIDTH = 480
PREVIEW_HEIGHT = 360

# =============================================================================
# Safety Settings (LAZY MODE)
# =============================================================================
# Maximum mouse movement per frame (prevents jumps)
# Higher = cursor can move faster with quick hand movements
MAX_MOUSE_SPEED = 200

# Safe zone - prevent actions near screen edges
SAFE_ZONE_MARGIN = 5  # Small = access more of the screen edges

# =============================================================================
# Paths
# =============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
CACHE_DIR = PROJECT_ROOT / ".cache"

# Create directories if they don't exist
LOGS_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
