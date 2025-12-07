"""
Vision Tools
~~~~~~~~~~~~

ADK-compatible tools for screen capture and vision analysis.
"""

import pyautogui
import io
import base64
from pathlib import Path
from datetime import datetime
from PIL import Image
from typing import Optional

from ..config import CACHE_DIR, SCREEN_CAPTURE_QUALITY, MAX_IMAGE_DIMENSION


def take_screenshot(
    region: Optional[tuple] = None,
    save_path: Optional[str] = None,
) -> dict:
    """
    Take a screenshot of the entire screen or a specific region.
    
    Args:
        region: Optional tuple (x, y, width, height) for specific region.
                If not provided, captures the entire screen.
        save_path: Optional path to save the screenshot. 
                   If not provided, saves to cache with timestamp.
    
    Returns:
        dict: Status, file path, and base64-encoded image data.
    
    Example:
        take_screenshot()  # Full screen screenshot
        take_screenshot(region=(0, 0, 800, 600))  # Capture specific region
    """
    try:
        # Take screenshot
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
        
        # Resize if too large
        if max(screenshot.size) > MAX_IMAGE_DIMENSION:
            ratio = MAX_IMAGE_DIMENSION / max(screenshot.size)
            new_size = (int(screenshot.width * ratio), int(screenshot.height * ratio))
            screenshot = screenshot.resize(new_size, Image.LANCZOS)
        
        # Determine save path
        if save_path:
            file_path = Path(save_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = CACHE_DIR / f"screenshot_{timestamp}.jpg"
        
        # Save screenshot
        screenshot.save(file_path, "JPEG", quality=SCREEN_CAPTURE_QUALITY)
        
        # Also create base64 for API usage
        buffer = io.BytesIO()
        screenshot.save(buffer, format="JPEG", quality=SCREEN_CAPTURE_QUALITY)
        base64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        return {
            "status": "success",
            "message": f"Screenshot saved to {file_path}",
            "file_path": str(file_path),
            "size": {"width": screenshot.width, "height": screenshot.height},
            "base64_data": base64_data,
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to take screenshot: {str(e)}"
        }


def get_screen_info() -> dict:
    """
    Get information about the screen.
    
    Returns:
        dict: Screen dimensions and other info.
    """
    try:
        size = pyautogui.size()
        position = pyautogui.position()
        
        return {
            "status": "success",
            "screen_width": size.width,
            "screen_height": size.height,
            "mouse_position": {"x": position.x, "y": position.y},
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get screen info: {str(e)}"
        }


def get_screen_text(region: Optional[tuple] = None) -> dict:
    """
    Capture screen and prepare for OCR/Vision analysis.
    
    This function captures the screen and prepares it for 
    analysis by Gemini's vision capabilities.
    
    Args:
        region: Optional tuple (x, y, width, height) for specific region.
    
    Returns:
        dict: Status and base64-encoded image ready for Gemini.
    """
    try:
        # Take screenshot
        result = take_screenshot(region=region)
        
        if result["status"] != "success":
            return result
        
        return {
            "status": "success",
            "message": "Screen captured and ready for vision analysis",
            "image_base64": result["base64_data"],
            "size": result["size"],
            "hint": "Send this image to Gemini for text extraction or analysis",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to capture screen: {str(e)}"
        }


def locate_on_screen(
    image_path: str,
    confidence: float = 0.9,
) -> dict:
    """
    Find an image on the screen.
    
    Args:
        image_path: Path to the image to find.
        confidence: Match confidence threshold (0.0 to 1.0).
    
    Returns:
        dict: Status and location if found.
    """
    try:
        location = pyautogui.locateOnScreen(
            image_path,
            confidence=confidence,
        )
        
        if location:
            center = pyautogui.center(location)
            return {
                "status": "success",
                "found": True,
                "location": {
                    "x": location.left,
                    "y": location.top,
                    "width": location.width,
                    "height": location.height,
                },
                "center": {"x": center.x, "y": center.y},
            }
        else:
            return {
                "status": "success",
                "found": False,
                "message": "Image not found on screen",
            }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to locate image: {str(e)}"
        }
