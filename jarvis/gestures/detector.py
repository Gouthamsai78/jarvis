"""
Hand Detector Module
~~~~~~~~~~~~~~~~~~~~

Uses MediaPipe Hands to detect and track hand landmarks in real-time.
Provides 21 3D landmarks per hand for gesture recognition.
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List

# MediaPipe may not be available on Python 3.13+
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("⚠️ MediaPipe not available. Hand gesture detection disabled.")
    print("   Install with Python 3.12 or earlier for full gesture support.")

from ..config import GESTURE_CONFIDENCE_THRESHOLD, TRACKING_CONFIDENCE


@dataclass
class HandLandmarks:
    """Container for hand landmark data."""
    
    # All 21 landmarks as numpy array (21, 3) - x, y, z
    landmarks: np.ndarray
    
    # Handedness (left or right)
    handedness: str
    
    # Confidence score
    confidence: float
    
    # Bounding box (x, y, w, h)
    bbox: Tuple[int, int, int, int]
    
    @property
    def wrist(self) -> np.ndarray:
        """Landmark 0: Wrist position."""
        return self.landmarks[0]
    
    @property
    def thumb_tip(self) -> np.ndarray:
        """Landmark 4: Thumb tip."""
        return self.landmarks[4]
    
    @property
    def index_tip(self) -> np.ndarray:
        """Landmark 8: Index finger tip."""
        return self.landmarks[8]
    
    @property
    def middle_tip(self) -> np.ndarray:
        """Landmark 12: Middle finger tip."""
        return self.landmarks[12]
    
    @property
    def ring_tip(self) -> np.ndarray:
        """Landmark 16: Ring finger tip."""
        return self.landmarks[16]
    
    @property
    def pinky_tip(self) -> np.ndarray:
        """Landmark 20: Pinky tip."""
        return self.landmarks[20]
    
    @property
    def palm_center(self) -> np.ndarray:
        """Approximate palm center (average of landmarks 0, 5, 9, 13, 17)."""
        palm_landmarks = [0, 5, 9, 13, 17]
        return np.mean(self.landmarks[palm_landmarks], axis=0)
    
    def finger_is_extended(self, finger_landmarks: List[int]) -> bool:
        """
        Check if a finger is extended based on its landmarks.
        
        Args:
            finger_landmarks: List of 4 landmark indices for a finger
                             [mcp, pip, dip, tip]
        
        Returns:
            True if finger is extended, False otherwise.
        """
        mcp = self.landmarks[finger_landmarks[0]]
        pip = self.landmarks[finger_landmarks[1]]
        tip = self.landmarks[finger_landmarks[3]]
        
        # Finger is extended if tip is further from wrist than pip
        tip_dist = np.linalg.norm(tip[:2] - self.wrist[:2])
        pip_dist = np.linalg.norm(pip[:2] - self.wrist[:2])
        
        return tip_dist > pip_dist
    
    def get_extended_fingers(self) -> List[str]:
        """
        Get list of extended fingers.
        
        Returns:
            List of finger names that are extended.
        """
        fingers = {
            "thumb": [1, 2, 3, 4],
            "index": [5, 6, 7, 8],
            "middle": [9, 10, 11, 12],
            "ring": [13, 14, 15, 16],
            "pinky": [17, 18, 19, 20],
        }
        
        extended = []
        
        # Thumb has different logic (check x-axis movement)
        thumb_tip = self.landmarks[4]
        thumb_mcp = self.landmarks[2]
        if self.handedness == "Right":
            if thumb_tip[0] < thumb_mcp[0]:
                extended.append("thumb")
        else:
            if thumb_tip[0] > thumb_mcp[0]:
                extended.append("thumb")
        
        # Other fingers
        for finger, landmarks in list(fingers.items())[1:]:
            if self.finger_is_extended(landmarks):
                extended.append(finger)
        
        return extended


class HandDetector:
    """
    Real-time hand detection using MediaPipe Hands.
    
    Detects up to 2 hands and provides 21 3D landmarks per hand.
    
    Example:
        detector = HandDetector()
        
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            hands = detector.detect(frame)
            
            for hand in hands:
                print(f"Detected {hand.handedness} hand")
                print(f"Index tip at: {hand.index_tip}")
    """
    
    # MediaPipe landmark indices
    LANDMARK_NAMES = [
        "WRIST",
        "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP",
        "INDEX_MCP", "INDEX_PIP", "INDEX_DIP", "INDEX_TIP",
        "MIDDLE_MCP", "MIDDLE_PIP", "MIDDLE_DIP", "MIDDLE_TIP",
        "RING_MCP", "RING_PIP", "RING_DIP", "RING_TIP",
        "PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP",
    ]
    
    def __init__(
        self,
        max_hands: int = 1,
        min_detection_confidence: float = GESTURE_CONFIDENCE_THRESHOLD,
        min_tracking_confidence: float = TRACKING_CONFIDENCE,
    ):
        """
        Initialize HandDetector.
        
        Args:
            max_hands: Maximum number of hands to detect.
            min_detection_confidence: Minimum confidence for detection.
            min_tracking_confidence: Minimum confidence for tracking.
        """
        self._available = MEDIAPIPE_AVAILABLE
        
        if not MEDIAPIPE_AVAILABLE:
            self.mp_hands = None
            self.mp_drawing = None
            self.mp_drawing_styles = None
            self.hands = None
            return
        
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        
        self._frame_shape: Optional[Tuple[int, int]] = None
    
    @property
    def available(self) -> bool:
        """Check if hand detection is available."""
        return self._available
    
    def detect(self, frame: np.ndarray) -> List[HandLandmarks]:
        """
        Detect hands in a frame.
        
        Args:
            frame: BGR image from OpenCV.
        
        Returns:
            List of HandLandmarks for each detected hand.
        """
        if not self._available:
            return []
        
        self._frame_shape = frame.shape[:2]
        h, w = self._frame_shape
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.hands.process(rgb_frame)
        
        hands = []
        
        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(
                results.multi_hand_landmarks,
                results.multi_handedness
            ):
                # Extract landmarks as numpy array
                landmarks = np.array([
                    [lm.x * w, lm.y * h, lm.z * w]
                    for lm in hand_landmarks.landmark
                ])
                
                # Calculate bounding box
                x_coords = landmarks[:, 0]
                y_coords = landmarks[:, 1]
                x_min, x_max = int(min(x_coords)), int(max(x_coords))
                y_min, y_max = int(min(y_coords)), int(max(y_coords))
                bbox = (x_min, y_min, x_max - x_min, y_max - y_min)
                
                # Get handedness
                hand_type = handedness.classification[0].label
                confidence = handedness.classification[0].score
                
                hands.append(HandLandmarks(
                    landmarks=landmarks,
                    handedness=hand_type,
                    confidence=confidence,
                    bbox=bbox,
                ))
        
        return hands
    
    def draw_landmarks(
        self,
        frame: np.ndarray,
        hand: HandLandmarks,
        draw_bbox: bool = True,
    ) -> np.ndarray:
        """
        Draw hand landmarks on frame.
        
        Args:
            frame: BGR image.
            hand: HandLandmarks to draw.
            draw_bbox: Whether to draw bounding box.
        
        Returns:
            Frame with landmarks drawn.
        """
        # Draw landmarks using OpenCV (compatible with all MediaPipe versions)
        landmark_color = (0, 255, 0)  # Green
        connection_color = (255, 0, 0)  # Blue
        
        # Draw connections
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),  # Index
            (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
            (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
            (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
            (5, 9), (9, 13), (13, 17),  # Palm
        ]
        
        for start_idx, end_idx in connections:
            start = tuple(hand.landmarks[start_idx][:2].astype(int))
            end = tuple(hand.landmarks[end_idx][:2].astype(int))
            cv2.line(frame, start, end, connection_color, 2)
        
        # Draw landmark points
        for i, lm in enumerate(hand.landmarks):
            center = tuple(lm[:2].astype(int))
            # Fingertips are larger
            radius = 6 if i in [4, 8, 12, 16, 20] else 4
            cv2.circle(frame, center, radius, landmark_color, -1)
            cv2.circle(frame, center, radius, (0, 0, 0), 1)  # Black border
        
        # Draw bounding box
        if draw_bbox:
            x, y, bw, bh = hand.bbox
            cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"{hand.handedness} ({hand.confidence:.2f})",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )
        
        return frame
    
    def release(self):
        """Release MediaPipe resources."""
        if self.hands:
            self.hands.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.release()
