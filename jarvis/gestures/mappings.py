"""
Gesture Mappings
~~~~~~~~~~~~~~~~

Defines gesture types and their corresponding actions.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Callable, Optional


class GestureType(Enum):
    """Enumeration of recognized gestures."""
    
    NONE = auto()           # No gesture detected
    OPEN_PALM = auto()      # ✋ All fingers extended - cursor mode
    FIST = auto()           # ✊ All fingers closed - drag mode
    POINT = auto()          # ☝️ Index extended - left click
    PEACE = auto()          # ✌️ Index + middle extended - right click
    THUMBS_UP = auto()      # 👍 Thumb up - scroll up
    THUMBS_DOWN = auto()    # 👎 Thumb down - scroll down
    PINCH = auto()          # 🤏 Thumb + index close - zoom/precision
    THREE_FINGERS = auto()  # 🖖 Index + middle + ring - middle click
    ROCK = auto()           # 🤘 Index + pinky extended - special action
    OK_SIGN = auto()        # 👌 Thumb + index circle - confirm
    HOOK = auto()           # 🪝 Index raised, others closed - text select


@dataclass
class GestureAction:
    """Defines the action associated with a gesture."""
    
    gesture: GestureType
    name: str
    description: str
    action_type: str  # "mouse", "keyboard", "system", "custom"
    command: Optional[str] = None
    continuous: bool = False  # If True, action continues while gesture held


# Default gesture to action mappings
GESTURE_ACTIONS = {
    GestureType.OPEN_PALM: GestureAction(
        gesture=GestureType.OPEN_PALM,
        name="Cursor Mode",
        description="Move cursor following palm position",
        action_type="mouse",
        command="move",
        continuous=True,
    ),
    GestureType.FIST: GestureAction(
        gesture=GestureType.FIST,
        name="Drag Mode",
        description="Click and drag while fist is held",
        action_type="mouse",
        command="drag",
        continuous=True,
    ),
    GestureType.POINT: GestureAction(
        gesture=GestureType.POINT,
        name="Left Click",
        description="Single left click when gesture detected",
        action_type="mouse",
        command="left_click",
        continuous=False,
    ),
    GestureType.PEACE: GestureAction(
        gesture=GestureType.PEACE,
        name="Right Click",
        description="Right click when peace sign shown",
        action_type="mouse",
        command="right_click",
        continuous=False,
    ),
    GestureType.THUMBS_UP: GestureAction(
        gesture=GestureType.THUMBS_UP,
        name="Scroll Up",
        description="Scroll up while thumb up is held",
        action_type="mouse",
        command="scroll_up",
        continuous=True,
    ),
    GestureType.THUMBS_DOWN: GestureAction(
        gesture=GestureType.THUMBS_DOWN,
        name="Scroll Down",
        description="Scroll down while thumb down is held",
        action_type="mouse",
        command="scroll_down",
        continuous=True,
    ),
    GestureType.PINCH: GestureAction(
        gesture=GestureType.PINCH,
        name="Precision Mode",
        description="Fine cursor control when pinching",
        action_type="mouse",
        command="precision",
        continuous=True,
    ),
    GestureType.THREE_FINGERS: GestureAction(
        gesture=GestureType.THREE_FINGERS,
        name="Middle Click",
        description="Middle click for opening links in new tab",
        action_type="mouse",
        command="middle_click",
        continuous=False,
    ),
    GestureType.ROCK: GestureAction(
        gesture=GestureType.ROCK,
        name="Voice Activate",
        description="Activate voice command mode",
        action_type="system",
        command="voice_activate",
        continuous=False,
    ),
    GestureType.OK_SIGN: GestureAction(
        gesture=GestureType.OK_SIGN,
        name="Confirm",
        description="Confirm current action or selection",
        action_type="keyboard",
        command="enter",
        continuous=False,
    ),
}


def get_gesture_action(gesture: GestureType) -> Optional[GestureAction]:
    """Get the action for a gesture type."""
    return GESTURE_ACTIONS.get(gesture)


def get_all_gestures() -> list:
    """Get list of all supported gestures with descriptions."""
    return [
        {
            "gesture": g.name,
            "action": a.name,
            "description": a.description,
            "continuous": a.continuous,
        }
        for g, a in GESTURE_ACTIONS.items()
    ]
