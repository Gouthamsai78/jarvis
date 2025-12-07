"""
Control Panel UI
~~~~~~~~~~~~~~~~

Modern control panel for Jarvis using CustomTkinter.
"""

import threading
from typing import Optional, Callable

try:
    import customtkinter as ctk
    CUSTOMTKINTER_AVAILABLE = True
except ImportError:
    CUSTOMTKINTER_AVAILABLE = False


class ControlPanel:
    """
    Modern control panel UI for Jarvis.
    
    Provides:
    - Toggle switches for gesture/voice/vision
    - Status indicators
    - Gesture preview
    - Command history
    - Settings panel
    
    Example:
        panel = ControlPanel()
        
        @panel.on_toggle("gesture")
        def on_gesture_toggle(enabled):
            print(f"Gesture: {enabled}")
        
        panel.run()
    """
    
    def __init__(self, title: str = "Jarvis Control Panel"):
        """Initialize control panel."""
        if not CUSTOMTKINTER_AVAILABLE:
            print("CustomTkinter not available. Install: pip install customtkinter")
            return
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create window
        self.root = ctk.CTk()
        self.root.title(title)
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        
        # State
        self._gesture_enabled = ctk.BooleanVar(value=True)
        self._voice_enabled = ctk.BooleanVar(value=True)
        self._vision_enabled = ctk.BooleanVar(value=True)
        
        # Callbacks
        self._toggle_callbacks = {}
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build the UI components."""
        if not CUSTOMTKINTER_AVAILABLE:
            return
        
        # Header
        header = ctk.CTkFrame(self.root, height=80)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header,
            text="🤖 JARVIS",
            font=("Helvetica", 28, "bold"),
        )
        title_label.pack(pady=10)
        
        subtitle = ctk.CTkLabel(
            header,
            text="AI Assistant Control Panel",
            font=("Helvetica", 12),
            text_color="gray",
        )
        subtitle.pack()
        
        # Status indicator
        self._status_frame = ctk.CTkFrame(self.root)
        self._status_frame.pack(fill="x", padx=10, pady=5)
        
        self._status_label = ctk.CTkLabel(
            self._status_frame,
            text="● Online",
            font=("Helvetica", 14),
            text_color="#00ff00",
        )
        self._status_label.pack(pady=10)
        
        # Toggles section
        toggles_frame = ctk.CTkFrame(self.root)
        toggles_frame.pack(fill="x", padx=10, pady=10)
        
        toggles_title = ctk.CTkLabel(
            toggles_frame,
            text="Controls",
            font=("Helvetica", 16, "bold"),
        )
        toggles_title.pack(anchor="w", padx=10, pady=5)
        
        # Gesture toggle
        self._create_toggle(
            toggles_frame,
            "🖐️ Gesture Control",
            "Control cursor with hand gestures",
            self._gesture_enabled,
            "gesture",
        )
        
        # Voice toggle
        self._create_toggle(
            toggles_frame,
            "🎤 Voice Control",
            "Say 'Jarvis' to activate",
            self._voice_enabled,
            "voice",
        )
        
        # Vision toggle
        self._create_toggle(
            toggles_frame,
            "👁️ Vision Analysis",
            "AI can see your screen",
            self._vision_enabled,
            "vision",
        )
        
        # Gesture info
        gestures_frame = ctk.CTkFrame(self.root)
        gestures_frame.pack(fill="x", padx=10, pady=10)
        
        gestures_title = ctk.CTkLabel(
            gestures_frame,
            text="Gestures",
            font=("Helvetica", 16, "bold"),
        )
        gestures_title.pack(anchor="w", padx=10, pady=5)
        
        gestures = [
            ("✋ Open Palm", "Move cursor"),
            ("☝️ Point", "Left click"),
            ("✌️ Peace", "Right click"),
            ("✊ Fist", "Drag"),
            ("👍 Thumbs Up", "Scroll up"),
            ("👎 Thumbs Down", "Scroll down"),
        ]
        
        for emoji, action in gestures:
            row = ctk.CTkFrame(gestures_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)
            
            ctk.CTkLabel(row, text=emoji, width=80, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=action, text_color="gray").pack(side="left")
        
        # Action buttons
        buttons_frame = ctk.CTkFrame(self.root)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        self._start_button = ctk.CTkButton(
            buttons_frame,
            text="▶ Start Jarvis",
            font=("Helvetica", 14),
            height=40,
            command=self._on_start,
        )
        self._start_button.pack(fill="x", padx=10, pady=5)
        
        self._stop_button = ctk.CTkButton(
            buttons_frame,
            text="⏹ Stop",
            font=("Helvetica", 14),
            height=40,
            fg_color="#cc3333",
            hover_color="#aa2222",
            command=self._on_stop,
            state="disabled",
        )
        self._stop_button.pack(fill="x", padx=10, pady=5)
        
        # Footer
        footer = ctk.CTkLabel(
            self.root,
            text="Press 'Q' in preview window to quit",
            text_color="gray",
            font=("Helvetica", 10),
        )
        footer.pack(side="bottom", pady=10)
    
    def _create_toggle(
        self,
        parent,
        title: str,
        description: str,
        variable: ctk.BooleanVar,
        key: str,
    ):
        """Create a toggle switch with label."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)
        
        text_frame = ctk.CTkFrame(frame, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            text_frame,
            text=title,
            font=("Helvetica", 13),
            anchor="w",
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            text_frame,
            text=description,
            font=("Helvetica", 10),
            text_color="gray",
            anchor="w",
        ).pack(anchor="w")
        
        switch = ctk.CTkSwitch(
            frame,
            text="",
            variable=variable,
            command=lambda: self._on_toggle(key, variable.get()),
        )
        switch.pack(side="right")
    
    def _on_toggle(self, key: str, enabled: bool):
        """Handle toggle switch change."""
        if key in self._toggle_callbacks:
            self._toggle_callbacks[key](enabled)
    
    def _on_start(self):
        """Handle start button click."""
        self._start_button.configure(state="disabled")
        self._stop_button.configure(state="normal")
        self._status_label.configure(text="● Running", text_color="#00ff00")
        
        if "start" in self._toggle_callbacks:
            self._toggle_callbacks["start"]()
    
    def _on_stop(self):
        """Handle stop button click."""
        self._start_button.configure(state="normal")
        self._stop_button.configure(state="disabled")
        self._status_label.configure(text="● Stopped", text_color="#ff6600")
        
        if "stop" in self._toggle_callbacks:
            self._toggle_callbacks["stop"]()
    
    def on_toggle(self, key: str):
        """
        Decorator to register toggle callback.
        
        Args:
            key: One of "gesture", "voice", "vision", "start", "stop"
        """
        def decorator(func: Callable):
            self._toggle_callbacks[key] = func
            return func
        return decorator
    
    def set_status(self, text: str, color: str = "#00ff00"):
        """Update status display."""
        if CUSTOMTKINTER_AVAILABLE and hasattr(self, '_status_label'):
            self._status_label.configure(text=f"● {text}", text_color=color)
    
    def run(self):
        """Run the control panel (blocking)."""
        if CUSTOMTKINTER_AVAILABLE:
            self.root.mainloop()
    
    def run_async(self):
        """Run the control panel in a background thread."""
        if CUSTOMTKINTER_AVAILABLE:
            thread = threading.Thread(target=self.run, daemon=True)
            thread.start()
            return thread
        return None


def main():
    """Test the control panel."""
    panel = ControlPanel()
    
    @panel.on_toggle("gesture")
    def on_gesture(enabled):
        print(f"Gesture: {enabled}")
    
    @panel.on_toggle("voice")
    def on_voice(enabled):
        print(f"Voice: {enabled}")
    
    @panel.on_toggle("start")
    def on_start():
        print("Starting Jarvis...")
    
    @panel.on_toggle("stop")
    def on_stop():
        print("Stopping Jarvis...")
    
    panel.run()


if __name__ == "__main__":
    main()
