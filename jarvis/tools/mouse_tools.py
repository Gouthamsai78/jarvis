"""
Mouse Control Tools
~~~~~~~~~~~~~~~~~~~

ADK-compatible tools for mouse control using PyAutoGUI.
"""

import pyautogui
from typing import Literal

# Configure PyAutoGUI for safety
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.05      # Small pause between actions


def move_mouse(x: int, y: int) -> dict:
    """
    Move the mouse cursor to an absolute screen position.
    
    Args:
        x: The x-coordinate (horizontal position) on the screen.
        y: The y-coordinate (vertical position) on the screen.
    
    Returns:
        dict: Status and result message.
    
    Example:
        move_mouse(500, 300)  # Move cursor to position (500, 300)
    """
    try:
        # Get screen size for validation
        screen_w, screen_h = pyautogui.size()
        
        # Clamp to screen bounds
        x = max(0, min(x, screen_w - 1))
        y = max(0, min(y, screen_h - 1))
        
        pyautogui.moveTo(x, y, duration=0.1)
        
        return {
            "status": "success",
            "message": f"Moved mouse to ({x}, {y})",
            "position": {"x": x, "y": y}
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to move mouse: {str(e)}"
        }


def click_mouse(
    button: Literal["left", "right", "middle"] = "left",
    clicks: int = 1,
    x: int = None,
    y: int = None,
) -> dict:
    """
    Click the mouse button at the current or specified position.
    
    Args:
        button: Which mouse button to click ("left", "right", or "middle").
        clicks: Number of clicks (1 for single, 2 for double-click).
        x: Optional x-coordinate to click at. If not provided, clicks at current position.
        y: Optional y-coordinate to click at. If not provided, clicks at current position.
    
    Returns:
        dict: Status and result message.
    
    Example:
        click_mouse()  # Single left click at current position
        click_mouse(button="right")  # Right click
        click_mouse(clicks=2)  # Double click
        click_mouse(x=100, y=200)  # Click at specific position
    """
    try:
        if x is not None and y is not None:
            pyautogui.click(x=x, y=y, button=button, clicks=clicks)
            pos_msg = f"at ({x}, {y})"
        else:
            pyautogui.click(button=button, clicks=clicks)
            current_x, current_y = pyautogui.position()
            pos_msg = f"at current position ({current_x}, {current_y})"
        
        click_type = "double-click" if clicks == 2 else "click"
        
        return {
            "status": "success",
            "message": f"{button.capitalize()} {click_type} {pos_msg}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to click: {str(e)}"
        }


def drag_mouse(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration: float = 0.5,
    button: Literal["left", "right", "middle"] = "left",
) -> dict:
    """
    Drag from one position to another.
    
    Args:
        start_x: Starting x-coordinate.
        start_y: Starting y-coordinate.
        end_x: Ending x-coordinate.
        end_y: Ending y-coordinate.
        duration: How long the drag should take in seconds.
        button: Which button to hold during drag.
    
    Returns:
        dict: Status and result message.
    
    Example:
        drag_mouse(100, 100, 500, 500)  # Drag from (100,100) to (500,500)
    """
    try:
        # Move to start position
        pyautogui.moveTo(start_x, start_y, duration=0.1)
        
        # Perform drag
        pyautogui.drag(
            end_x - start_x,
            end_y - start_y,
            duration=duration,
            button=button,
        )
        
        return {
            "status": "success",
            "message": f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to drag: {str(e)}"
        }


def scroll_mouse(
    direction: Literal["up", "down", "left", "right"] = "down",
    amount: int = 3,
    x: int = None,
    y: int = None,
) -> dict:
    """
    Scroll the mouse wheel.
    
    Args:
        direction: Direction to scroll ("up", "down", "left", "right").
        amount: How much to scroll (number of "clicks").
        x: Optional x-coordinate to scroll at.
        y: Optional y-coordinate to scroll at.
    
    Returns:
        dict: Status and result message.
    
    Example:
        scroll_mouse("down", 5)  # Scroll down 5 clicks
        scroll_mouse("up", 3)    # Scroll up 3 clicks
    """
    try:
        # Move to position if specified
        if x is not None and y is not None:
            pyautogui.moveTo(x, y, duration=0.1)
        
        if direction == "up":
            pyautogui.scroll(amount)
        elif direction == "down":
            pyautogui.scroll(-amount)
        elif direction == "left":
            pyautogui.hscroll(-amount)
        elif direction == "right":
            pyautogui.hscroll(amount)
        
        return {
            "status": "success",
            "message": f"Scrolled {direction} by {amount} clicks",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to scroll: {str(e)}"
        }
