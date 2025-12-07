"""
Jarvis Agent
~~~~~~~~~~~~

Main AI agent using Google ADK for intelligent task automation.
Combines gesture input, vision understanding, and system control.
"""

from google.adk.agents import Agent

from .tools.mouse_tools import move_mouse, click_mouse, drag_mouse, scroll_mouse
from .tools.keyboard_tools import type_text, press_key, hotkey
from .tools.system_tools import (
    open_app,
    close_window,
    switch_window,
    search_start_menu,
    minimize_window,
    maximize_window,
    get_open_windows,
    focus_window,
)
from .tools.vision_tools import take_screenshot, get_screen_info, get_screen_text


# =============================================================================
# Jarvis Agent Definition
# =============================================================================

JARVIS_INSTRUCTION = """You are Jarvis, an intelligent AI assistant for laptop automation.

## Your Capabilities:
1. **Mouse Control**: Move cursor, click, drag, and scroll
2. **Keyboard Control**: Type text, press keys, execute shortcuts
3. **Application Control**: Open, close, and switch between apps
4. **Screen Understanding**: Take screenshots and analyze content
5. **Task Automation**: Execute multi-step tasks based on user requests

## Guidelines:
- Be concise and efficient in your responses
- Confirm before executing potentially destructive actions
- Break complex tasks into clear steps
- Report success or failure of each action
- If an action fails, suggest alternatives

## Safety:
- Never type passwords or sensitive information
- Don't close unsaved documents without warning
- Stay within screen bounds for mouse movements
- Report any errors encountered

## Response Style:
- Be helpful and proactive
- Explain what you're doing briefly
- Celebrate successful task completion
- Ask for clarification if needed"""


# Create the main Jarvis agent
root_agent = Agent(
    name="jarvis",
    model="gemini-2.0-flash",
    description="Personal AI assistant for laptop automation using gestures and voice",
    instruction=JARVIS_INSTRUCTION,
    tools=[
        # Mouse tools
        move_mouse,
        click_mouse,
        drag_mouse,
        scroll_mouse,
        # Keyboard tools
        type_text,
        press_key,
        hotkey,
        # System tools
        open_app,
        close_window,
        switch_window,
        search_start_menu,
        minimize_window,
        maximize_window,
        get_open_windows,
        focus_window,
        # Vision tools
        take_screenshot,
        get_screen_info,
        get_screen_text,
    ],
)


# =============================================================================
# Specialized Sub-Agents (for complex tasks)
# =============================================================================

# Browser automation agent
browser_agent = Agent(
    name="browser_assistant",
    model="gemini-2.0-flash",
    description="Specialized agent for web browser automation",
    instruction="""You are a browser automation assistant.
You help users navigate websites, fill forms, and interact with web content.

Key shortcuts you know:
- Ctrl+T: New tab
- Ctrl+W: Close tab
- Ctrl+L: Focus address bar
- Ctrl+F: Find on page
- F5: Refresh
- Alt+Left: Back
- Alt+Right: Forward

Always wait for pages to load before interacting.""",
    tools=[
        click_mouse,
        type_text,
        press_key,
        hotkey,
        take_screenshot,
        scroll_mouse,
    ],
)

# File manager agent
file_agent = Agent(
    name="file_assistant",
    model="gemini-2.0-flash",
    description="Specialized agent for file management tasks",
    instruction="""You are a file management assistant.
You help users navigate folders, organize files, and manage their file system.

Key shortcuts:
- Win+E: Open File Explorer
- Ctrl+C/V/X: Copy/Paste/Cut
- F2: Rename
- Delete: Move to trash
- Shift+Delete: Permanent delete

Always confirm before deleting files.""",
    tools=[
        open_app,
        click_mouse,
        type_text,
        press_key,
        hotkey,
        take_screenshot,
    ],
)


def get_agent() -> Agent:
    """Get the main Jarvis agent."""
    return root_agent


def get_all_agents() -> dict:
    """Get all available agents."""
    return {
        "jarvis": root_agent,
        "browser": browser_agent,
        "file": file_agent,
    }
