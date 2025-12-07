"""
Gesture Recognizer Module
~~~~~~~~~~~~~~~~~~~~~~~~~

Classifies hand landmarks into specific gestures.
"""

import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass
import time

from .detector import HandLandmarks
from .mappings import GestureType
from ..config import GESTURE_HOLD_TIME


@dataclass
class GestureState:
    """Tracks the current gesture state."""
    
    gesture: GestureType
    confidence: float
    start_time: float
    position: Tuple[float, float]  # Normalized position (0-1)
    is_held: bool = False  # True if gesture held for GESTURE_HOLD_TIME


class GestureRecognizer:
    """
    Recognizes gestures from hand landmarks.
    
    Uses geometric analysis of finger positions to classify gestures.
    
    Example:
        recognizer = GestureRecognizer()
        
        hands = detector.detect(frame)
        if hands:
            gesture_state = recognizer.recognize(hands[0])
            print(f"Gesture: {gesture_state.gesture.name}")
    """
    
    # Distance thresholds (ULTIMATE LAZY MODE!)
    PINCH_THRESHOLD = 0.22  # Bigger = easier pinch detection
    FINGER_CLOSE_THRESHOLD = 0.18  # More forgiving
    
    def __init__(self):
        """Initialize recognizer."""
        self._last_gesture: Optional[GestureType] = None
        self._gesture_start_time: float = 0.0
        self._gesture_position: Tuple[float, float] = (0.5, 0.5)
    
    def recognize(self, hand: HandLandmarks) -> GestureState:
        """
        Recognize gesture from hand landmarks.
        
        Args:
            hand: HandLandmarks from HandDetector.
        
        Returns:
            GestureState with recognized gesture and metadata.
        """
        # Get extended fingers
        extended = hand.get_extended_fingers()
        num_extended = len(extended)
        
        # Get key measurements
        thumb_index_dist = self._normalized_distance(
            hand.thumb_tip, hand.index_tip, hand
        )
        
        # Determine gesture based on finger configuration
        gesture = self._classify_gesture(extended, thumb_index_dist, hand)
        
        # Track timing
        current_time = time.time()
        if gesture != self._last_gesture:
            self._last_gesture = gesture
            self._gesture_start_time = current_time
        
        # Calculate hold duration
        hold_duration = current_time - self._gesture_start_time
        is_held = hold_duration >= GESTURE_HOLD_TIME
        
        # Get position from palm center
        palm = hand.palm_center
        bbox = hand.bbox
        frame_w = bbox[0] + bbox[2] / 2 + 200  # Approximate frame width
        frame_h = bbox[1] + bbox[3] / 2 + 200  # Approximate frame height
        
        # Normalize position to 0-1 range
        pos_x = np.clip(palm[0] / frame_w, 0, 1)
        pos_y = np.clip(palm[1] / frame_h, 0, 1)
        
        return GestureState(
            gesture=gesture,
            confidence=hand.confidence,
            start_time=self._gesture_start_time,
            position=(pos_x, pos_y),
            is_held=is_held,
        )
    
    def _classify_gesture(
        self,
        extended: list,
        thumb_index_dist: float,
        hand: HandLandmarks,
    ) -> GestureType:
        """Classify gesture (ULTIMATE LAZY MODE - super forgiving!)."""
        
        num_extended = len(extended)
        
        # Check for pinch first (thumb and index close together)
        # PINCH is highest priority for volume control
        if thumb_index_dist < self.PINCH_THRESHOLD:
            # Pinch detected - check if other fingers are out
            if "middle" in extended and "ring" in extended and "pinky" in extended:
                return GestureType.OK_SIGN
            # Any pinch gesture (for volume control)
            return GestureType.PINCH
        
        # Fist - no fingers extended
        if num_extended == 0:
            return GestureType.FIST
        
        # Thumbs up/down - only thumb extended (LAZY: smaller threshold!)
        if num_extended == 1 and "thumb" in extended:
            # Check thumb orientation - LAZY: only 15px difference needed!
            thumb_y = hand.thumb_tip[1]
            wrist_y = hand.wrist[1]
            
            if thumb_y < wrist_y - 15:  # Thumb pointing up
                return GestureType.THUMBS_UP
            elif thumb_y > wrist_y + 15:  # Thumb pointing down
                return GestureType.THUMBS_DOWN
        
        # Point - index extended (LAZY: thumb can be out too!)
        if "index" in extended and num_extended <= 2:
            if num_extended == 1 or (num_extended == 2 and "thumb" in extended):
                return GestureType.POINT
        
        # Peace sign - index and middle extended
        if num_extended == 2 and "index" in extended and "middle" in extended:
            return GestureType.PEACE
        
        # Rock sign - index and pinky extended
        if num_extended == 2 and "index" in extended and "pinky" in extended:
            return GestureType.ROCK
        
        # Three fingers - index, middle, ring extended
        if (num_extended == 3 and 
            "index" in extended and 
            "middle" in extended and 
            "ring" in extended):
            return GestureType.THREE_FINGERS
        
        # Open palm - LAZY: 3 or more fingers is enough!
        if num_extended >= 3:
            return GestureType.OPEN_PALM
        
        return GestureType.NONE
    
    def _normalized_distance(
        self,
        point1: np.ndarray,
        point2: np.ndarray,
        hand: HandLandmarks,
    ) -> float:
        """
        Calculate distance between two points, normalized by hand size.
        """
        # Use wrist to middle MCP as hand size reference
        hand_size = np.linalg.norm(hand.landmarks[9] - hand.wrist)
        
        if hand_size < 1:
            return 1.0
        
        distance = np.linalg.norm(point1[:2] - point2[:2])
        return distance / hand_size
    
    def reset(self):
        """Reset gesture tracking state."""
        self._last_gesture = None
        self._gesture_start_time = 0.0
