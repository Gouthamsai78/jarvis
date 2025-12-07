"""
LiveKit Voice Agent for Jarvis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Real-time voice agent powered by LiveKit and Google Gemini.
Provides natural conversation with computer automation capabilities.
"""

import os
import logging
import asyncio

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobRequest,
    WorkerOptions,
    cli,
)
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins.google import LLM, TTS, STT

# Import automation tools
import pyautogui
import webbrowser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jarvis-livekit")

# Disable pyautogui fail-safe for smoother operation
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


# ═══════════════════════════════════════════════════════════════════
# COMPUTER AUTOMATION TOOLS
# ═══════════════════════════════════════════════════════════════════

@function_tool()
async def click(x: int, y: int, button: str = "left") -> str:
    """Click at a specific screen position.
    
    Args:
        x: X coordinate on screen
        y: Y coordinate on screen
        button: Mouse button - left, right, or middle
    """
    try:
        pyautogui.click(x, y, button=button)
        return f"Clicked at ({x}, {y}) with {button} button"
    except Exception as e:
        return f"Click failed: {str(e)}"


@function_tool()
async def type_text(text: str) -> str:
    """Type text using the keyboard.
    
    Args:
        text: The text to type
    """
    try:
        pyautogui.typewrite(text, interval=0.02)
        return f"Typed: {text}"
    except:
        try:
            pyautogui.write(text)
            return f"Typed: {text}"
        except Exception as e:
            return f"Type failed: {str(e)}"


@function_tool()
async def press_key(key: str) -> str:
    """Press a keyboard key.
    
    Args:
        key: Key to press (e.g., 'enter', 'escape', 'tab', 'space')
    """
    try:
        pyautogui.press(key)
        return f"Pressed: {key}"
    except Exception as e:
        return f"Key press failed: {str(e)}"


@function_tool()
async def hotkey(keys: str) -> str:
    """Press a keyboard shortcut like Ctrl+C, Alt+Tab.
    
    Args:
        keys: Keys separated by '+', e.g., 'ctrl+c', 'alt+tab'
    """
    try:
        key_list = [k.strip() for k in keys.split('+')]
        pyautogui.hotkey(*key_list)
        return f"Pressed hotkey: {keys}"
    except Exception as e:
        return f"Hotkey failed: {str(e)}"


@function_tool()
async def scroll(direction: str, amount: int = 5) -> str:
    """Scroll the mouse wheel up or down.
    
    Args:
        direction: Direction - 'up' or 'down'
        amount: Number of scroll clicks (default 5)
    """
    try:
        scroll_amount = amount if direction == "up" else -amount
        pyautogui.scroll(scroll_amount)
        return f"Scrolled {direction} by {amount}"
    except Exception as e:
        return f"Scroll failed: {str(e)}"


@function_tool()
async def open_app(app_name: str) -> str:
    """Open an application by name.
    
    Args:
        app_name: Name of the application (e.g., 'notepad', 'chrome', 'calculator')
    """
    import subprocess
    import time
    
    app_mappings = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "edge": "msedge.exe",
        "explorer": "explorer.exe",
        "settings": "ms-settings:",
        "code": "code",
        "vscode": "code",
        "spotify": "spotify.exe",
    }
    
    try:
        executable = app_mappings.get(app_name.lower(), app_name)
        if executable.startswith("ms-"):
            os.startfile(executable)
            return f"Opened {app_name}"
        else:
            result = subprocess.Popen(executable, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.3)
            if result.poll() is not None and result.returncode != 0:
                raise FileNotFoundError("App not found")
            return f"Opened {app_name}"
    except (FileNotFoundError, OSError):
        # Fallback: Use Windows search to find and open the app
        try:
            pyautogui.press("win")
            time.sleep(0.5)
            pyautogui.typewrite(app_name, interval=0.02)
            time.sleep(0.8)
            pyautogui.press("enter")
            return f"Searched and opened {app_name}"
        except Exception as e:
            return f"Failed to open {app_name}: {str(e)}"
    except Exception as e:
        return f"Failed to open {app_name}: {str(e)}"


@function_tool()
async def open_website(url: str) -> str:
    """Open a website in the browser.
    
    Args:
        url: URL or website name (e.g., 'youtube', 'google', 'github.com')
    """
    websites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "twitter": "https://twitter.com",
        "github": "https://github.com",
        "reddit": "https://reddit.com",
        "chatgpt": "https://chat.openai.com",
    }
    try:
        target_url = websites.get(url.lower(), url)
        if not target_url.startswith("http"):
            target_url = f"https://{target_url}"
        webbrowser.open(target_url)
        return f"Opened {url}"
    except Exception as e:
        return f"Failed to open website: {str(e)}"


@function_tool()
async def set_volume(action: str) -> str:
    """Control system volume.
    
    Args:
        action: Action - 'up', 'down', or 'mute'
    """
    try:
        if action == "up":
            pyautogui.press("volumeup")
        elif action == "down":
            pyautogui.press("volumedown")
        elif action == "mute":
            pyautogui.press("volumemute")
        return f"Volume {action}"
    except Exception as e:
        return f"Volume control failed: {str(e)}"


@function_tool()
async def media_control(action: str) -> str:
    """Control media playback.
    
    Args:
        action: Action - 'play', 'pause', 'next', or 'previous'
    """
    try:
        if action in ["play", "pause"]:
            pyautogui.press("playpause")
        elif action == "next":
            pyautogui.press("nexttrack")
        elif action == "previous":
            pyautogui.press("prevtrack")
        return f"Media: {action}"
    except Exception as e:
        return f"Media control failed: {str(e)}"


# List of all tools
TOOLS = [
    click,
    type_text,
    press_key,
    hotkey,
    scroll,
    open_app,
    open_website,
    set_volume,
    media_control,
]


# ═══════════════════════════════════════════════════════════════════
# LIVEKIT AGENT - AUTO ACCEPT ALL JOBS
# ═══════════════════════════════════════════════════════════════════

async def request_handler(request: JobRequest):
    """Accept all incoming job requests."""
    logger.info(f"📥 Received job request: {request.room.name}")
    await request.accept()


async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit agent."""
    
    logger.info("🤖 Jarvis joining room...")
    
    # Connect to the room with audio
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    logger.info(f"📍 Connected to room: {ctx.room.name}")
    
    # Wait for a participant to join
    participant = await ctx.wait_for_participant()
    logger.info(f"👤 Participant joined: {participant.identity}")
    
    # Create Google LLM
    google_llm = LLM(
        model="gemini-2.0-flash-exp",
        temperature=0.8,
    )
    
    # Create the voice agent with tools
    agent = Agent(
        instructions="""You are Jarvis, an advanced AI assistant that can control the user's computer.

PERSONALITY:
- Be helpful, witty, and efficient like Tony Stark's JARVIS
- Keep responses concise but informative
- Start with a greeting when first connecting

CAPABILITIES (Use these tools):
- open_app: Open applications like Chrome, Notepad, Calculator
- open_website: Open websites like YouTube, Google, Gmail
- type_text: Type text on the keyboard
- press_key: Press keys like Enter, Escape, Tab
- hotkey: Press shortcuts like ctrl+c, alt+tab
- click: Click at screen coordinates
- scroll: Scroll up or down
- set_volume: Control volume (up, down, mute)
- media_control: Play, pause, next, previous

When you first connect, greet the user and ask how you can help.
""",
        llm=google_llm,
        stt=STT(),
        tts=TTS(voice="en-US-Journey-D"),
        tools=TOOLS,
    )
    
    # Start the agent session
    logger.info("🎤 Starting voice session...")
    session = AgentSession()
    session.start(agent=agent, room=ctx.room, participant=participant)
    
    logger.info("✅ Jarvis is now listening! Say something...")
    
    # Keep running
    await session.wait()


def main():
    """Run the LiveKit agent."""
    print("=" * 50)
    print("  🤖 JARVIS LIVEKIT VOICE AGENT")
    print("=" * 50)
    print()
    
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            request_fnc=request_handler,  # Auto-accept all jobs
            agent_name="jarvis",
        )
    )


if __name__ == "__main__":
    main()
