"""
System Control Tools
~~~~~~~~~~~~~~~~~~~~

ADK-compatible tools for system and application control.
"""

import subprocess
import os
import pyautogui
import time
from typing import Optional

try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except ImportError:
    PYGETWINDOW_AVAILABLE = False


def open_app(app_name: str) -> dict:
    """
    Open an application by name.
    
    Args:
        app_name: Name of the application to open. Can be:
                 - An executable name: "notepad", "chrome", "code"
                 - A full path: "C:/Program Files/..."
                 - A common app name that will be searched
    
    Returns:
        dict: Status and result message.
    
    Example:
        open_app("notepad")          # Open Notepad
        open_app("chrome")           # Open Google Chrome
        open_app("code")             # Open VS Code
        open_app("firefox")          # Open Firefox
        open_app("explorer")         # Open File Explorer
    """
    # Common app mappings for Windows
    app_mappings = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "paint": "mspaint.exe",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "settings": "ms-settings:",
        "chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "edge": "msedge.exe",
        "code": "code",
        "vscode": "code",
        "word": "WINWORD.EXE",
        "excel": "EXCEL.EXE",
        "powerpoint": "POWERPNT.EXE",
        "outlook": "OUTLOOK.EXE",
        "spotify": "spotify.exe",
        "discord": "discord.exe",
        "slack": "slack.exe",
        "teams": "teams.exe",
    }
    
    try:
        # Check if it's a mapped app name
        executable = app_mappings.get(app_name.lower(), app_name)
        
        # Special handling for Windows settings
        if executable.startswith("ms-"):
            os.startfile(executable)
        else:
            # Try to start the application
            result = subprocess.Popen(
                executable,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Give it a moment to see if it fails
            time.sleep(0.3)
            if result.poll() is not None and result.returncode != 0:
                raise FileNotFoundError(f"App {app_name} not found")
        
        return {
            "status": "success",
            "message": f"Opened application: {app_name}",
        }
    except (FileNotFoundError, OSError):
        # Fallback: Use Windows search to find and open the app
        try:
            pyautogui.press("win")
            time.sleep(0.5)
            pyautogui.typewrite(app_name, interval=0.02)
            time.sleep(0.8)
            pyautogui.press("enter")
            
            return {
                "status": "success",
                "message": f"Opened application via search: {app_name}",
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Could not find or open '{app_name}'. Error: {str(e)}"
            }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to open application: {str(e)}"
        }


def close_window() -> dict:
    """
    Close the currently active window.
    
    Returns:
        dict: Status and result message.
    
    Example:
        close_window()  # Closes the active window using Alt+F4
    """
    try:
        pyautogui.hotkey("alt", "f4")
        
        return {
            "status": "success",
            "message": "Sent close command (Alt+F4) to active window",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to close window: {str(e)}"
        }


def switch_window(direction: str = "next") -> dict:
    """
    Switch between open windows.
    
    Args:
        direction: "next" to switch to next window, "previous" for previous.
    
    Returns:
        dict: Status and result message.
    
    Example:
        switch_window()           # Switch to next window (Alt+Tab)
        switch_window("previous") # Switch to previous window (Alt+Shift+Tab)
    """
    try:
        if direction.lower() == "previous":
            pyautogui.hotkey("alt", "shift", "tab")
            msg = "Switched to previous window"
        else:
            pyautogui.hotkey("alt", "tab")
            msg = "Switched to next window"
        
        return {
            "status": "success",
            "message": msg,
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to switch window: {str(e)}"
        }


def search_start_menu(query: str) -> dict:
    """
    Search in Windows Start Menu.
    
    Args:
        query: The search query (app name, setting, file, etc.)
    
    Returns:
        dict: Status and result message.
    
    Example:
        search_start_menu("notepad")   # Search for Notepad
        search_start_menu("bluetooth") # Search for Bluetooth settings
    """
    try:
        # Open Start Menu
        pyautogui.press("win")
        time.sleep(0.5)
        
        # Type search query
        pyautogui.typewrite(query, interval=0.02)
        
        # Wait for search results to appear
        time.sleep(0.8)
        
        # Press Enter to open the first result
        pyautogui.press("enter")
        
        return {
            "status": "success",
            "message": f"Searched and opened: {query}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to search: {str(e)}"
        }


def minimize_window() -> dict:
    """
    Minimize the currently active window.
    
    Returns:
        dict: Status and result message.
    """
    try:
        pyautogui.hotkey("win", "down")
        
        return {
            "status": "success",
            "message": "Minimized active window",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to minimize: {str(e)}"
        }


def maximize_window() -> dict:
    """
    Maximize the currently active window.
    
    Returns:
        dict: Status and result message.
    """
    try:
        pyautogui.hotkey("win", "up")
        
        return {
            "status": "success",
            "message": "Maximized active window",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to maximize: {str(e)}"
        }


def get_open_windows() -> dict:
    """
    Get a list of all open windows.
    
    Returns:
        dict: Status and list of window titles.
    """
    if not PYGETWINDOW_AVAILABLE:
        return {
            "status": "error",
            "error_message": "pygetwindow is not installed. Install with: pip install pygetwindow"
        }
    
    try:
        windows = gw.getAllTitles()
        # Filter out empty titles
        windows = [w for w in windows if w.strip()]
        
        return {
            "status": "success",
            "windows": windows,
            "count": len(windows),
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get windows: {str(e)}"
        }


def focus_window(title: str) -> dict:
    """
    Focus a window by its title.
    
    Args:
        title: The window title (or partial match).
    
    Returns:
        dict: Status and result message.
    """
    if not PYGETWINDOW_AVAILABLE:
        return {
            "status": "error",
            "error_message": "pygetwindow is not installed"
        }
    
    try:
        windows = gw.getWindowsWithTitle(title)
        
        if not windows:
            return {
                "status": "error",
                "error_message": f"No window found with title containing: {title}"
            }
        
        window = windows[0]
        window.activate()
        
        return {
            "status": "success",
            "message": f"Focused window: {window.title}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to focus window: {str(e)}"
        }
