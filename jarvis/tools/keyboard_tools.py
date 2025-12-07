"""
Keyboard Control Tools
~~~~~~~~~~~~~~~~~~~~~~

ADK-compatible tools for keyboard control using PyAutoGUI.
"""

import pyautogui
from typing import List

# Configure PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


# Common keyboard shortcuts reference
COMMON_SHORTCUTS = {
    "copy": ["ctrl", "c"],
    "paste": ["ctrl", "v"],
    "cut": ["ctrl", "x"],
    "undo": ["ctrl", "z"],
    "redo": ["ctrl", "y"],
    "save": ["ctrl", "s"],
    "select_all": ["ctrl", "a"],
    "find": ["ctrl", "f"],
    "new_tab": ["ctrl", "t"],
    "close_tab": ["ctrl", "w"],
    "switch_window": ["alt", "tab"],
    "task_manager": ["ctrl", "shift", "esc"],
    "screenshot": ["win", "shift", "s"],
    "lock_screen": ["win", "l"],
    "minimize_all": ["win", "d"],
    "file_explorer": ["win", "e"],
    "settings": ["win", "i"],
    "run_dialog": ["win", "r"],
}


def type_text(text: str, interval: float = 0.02) -> dict:
    """
    Type text using keyboard simulation.
    
    Args:
        text: The text to type.
        interval: Time between each keystroke in seconds.
    
    Returns:
        dict: Status and result message.
    
    Example:
        type_text("Hello, World!")
        type_text("password123", interval=0.05)  # Slower typing
    """
    try:
        pyautogui.typewrite(text, interval=interval)
        
        return {
            "status": "success",
            "message": f"Typed {len(text)} characters",
            "text_length": len(text),
        }
    except Exception as e:
        # Try using write() for unicode support
        try:
            pyautogui.write(text)
            return {
                "status": "success",
                "message": f"Typed {len(text)} characters (unicode mode)",
                "text_length": len(text),
            }
        except Exception as e2:
            return {
                "status": "error",
                "error_message": f"Failed to type text: {str(e2)}"
            }


def press_key(key: str) -> dict:
    """
    Press a single key or use a named shortcut.
    
    Args:
        key: The key to press. Can be:
             - A single character: "a", "1", etc.
             - A special key: "enter", "tab", "escape", "backspace", etc.
             - A named shortcut: "copy", "paste", "undo", "save", etc.
    
    Returns:
        dict: Status and result message.
    
    Example:
        press_key("enter")      # Press Enter key
        press_key("escape")     # Press Escape key
        press_key("copy")       # Executes Ctrl+C
        press_key("save")       # Executes Ctrl+S
    
    Available shortcuts: copy, paste, cut, undo, redo, save, select_all, find,
                        new_tab, close_tab, switch_window, task_manager,
                        screenshot, lock_screen, minimize_all, file_explorer,
                        settings, run_dialog
    """
    try:
        # Check if it's a named shortcut
        if key.lower() in COMMON_SHORTCUTS:
            keys = COMMON_SHORTCUTS[key.lower()]
            pyautogui.hotkey(*keys)
            return {
                "status": "success",
                "message": f"Executed shortcut '{key}' ({'+'.join(keys)})",
            }
        
        # Press single key
        pyautogui.press(key)
        
        return {
            "status": "success",
            "message": f"Pressed key: {key}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to press key: {str(e)}"
        }


def hotkey(*keys: str) -> dict:
    """
    Press multiple keys simultaneously (keyboard shortcut).
    
    Args:
        *keys: Keys to press together.
    
    Returns:
        dict: Status and result message.
    
    Example:
        hotkey("ctrl", "c")           # Copy
        hotkey("ctrl", "shift", "n")  # New incognito window
        hotkey("alt", "f4")           # Close window
        hotkey("win", "d")            # Show desktop
    
    Common keys:
        - Modifiers: "ctrl", "alt", "shift", "win"
        - Function: "f1" through "f12"
        - Navigation: "home", "end", "pageup", "pagedown"
        - Arrows: "up", "down", "left", "right"
        - Others: "enter", "tab", "escape", "backspace", "delete", "space"
    """
    try:
        if not keys:
            return {
                "status": "error",
                "error_message": "No keys provided for hotkey"
            }
        
        pyautogui.hotkey(*keys)
        
        return {
            "status": "success",
            "message": f"Pressed hotkey: {'+'.join(keys)}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to execute hotkey: {str(e)}"
        }


def get_available_shortcuts() -> dict:
    """
    Get a list of all available named shortcuts.
    
    Returns:
        dict: Dictionary of shortcut names and their key combinations.
    """
    return {
        "status": "success",
        "shortcuts": COMMON_SHORTCUTS,
    }
