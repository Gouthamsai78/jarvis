"""
Jarvis Main Entry Point
~~~~~~~~~~~~~~~~~~~~~~~

Launches the Jarvis AI assistant with all modules.

Usage:
    python -m jarvis.main [options]

Options:
    --no-gesture    Disable gesture control
    --no-voice      Disable voice control
    --no-ui         Run in headless mode
    --vision-only   Only enable vision features
"""

import sys
import argparse
import time
import threading
from typing import Optional

import cv2
import numpy as np
import pyautogui

from .config import (
    SHOW_GESTURE_PREVIEW,
    PREVIEW_WIDTH,
    PREVIEW_HEIGHT,
    SCREEN_MARGIN,
    MAX_MOUSE_SPEED,
    CURSOR_SMOOTHING_FACTOR,
)
from .gestures import HandDetector, GestureRecognizer, GestureType, GESTURE_ACTIONS
from .vision import ScreenCapture, GeminiVision
from .voice import TextToSpeech, VoiceListener
from .agent import root_agent


class JarvisController:
    """
    Main controller that coordinates all Jarvis modules.
    """
    
    def __init__(
        self,
        enable_gesture: bool = True,
        enable_voice: bool = True,
        enable_vision: bool = True,
        show_preview: bool = SHOW_GESTURE_PREVIEW,
    ):
        """
        Initialize Jarvis controller.
        
        Args:
            enable_gesture: Enable hand gesture control.
            enable_voice: Enable voice commands.
            enable_vision: Enable screen vision.
            show_preview: Show camera preview window.
        """
        self.enable_gesture = enable_gesture
        self.enable_voice = enable_voice
        self.enable_vision = enable_vision
        self.show_preview = show_preview
        
        # Screen info
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Gesture control
        self._detector: Optional[HandDetector] = None
        self._recognizer: Optional[GestureRecognizer] = None
        self._camera: Optional[cv2.VideoCapture] = None
        
        # Vision
        self._screen_capture: Optional[ScreenCapture] = None
        self._gemini_vision: Optional[GeminiVision] = None
        
        # Voice
        self._tts: Optional[TextToSpeech] = None
        self._listener: Optional[VoiceListener] = None
        
        # State
        self._running = False
        self._last_cursor_pos = (0, 0)
        self._gesture_cooldown = 0.0
        self._dragging = False
        
        # Sci-Fi Volume Control State
        self._volume_mode = False
        self._volume_start_y = 0
        self._current_volume = 50
        
        # Text Selection State (OK Sign gesture)
        self._selection_mode = False
        self._selection_start = None
    
    def start(self):
        """Start Jarvis."""
        print("=" * 50)
        print("  🤖 JARVIS AI ASSISTANT")
        print("=" * 50)
        print()
        
        self._running = True
        
        # Initialize modules
        if self.enable_gesture:
            self._init_gesture()
        
        if self.enable_voice:
            self._init_voice()
        
        if self.enable_vision:
            self._init_vision()
        
        # Start main loop
        self._say("Jarvis is online and ready to assist.")
        
        if self.enable_gesture:
            self._run_gesture_loop()
        else:
            # Keep running without gesture control
            try:
                while self._running:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                pass
        
        self.stop()
    
    def stop(self):
        """Stop Jarvis."""
        self._running = False
        
        if self._camera:
            self._camera.release()
        
        if self._detector:
            self._detector.release()
        
        if self._screen_capture:
            self._screen_capture.stop()
        
        cv2.destroyAllWindows()
        
        self._say("Jarvis shutting down. Goodbye!")
        print("\n👋 Jarvis stopped.")
    
    def _init_gesture(self):
        """Initialize gesture control."""
        print("🖐️  Initializing gesture control...")
        
        try:
            self._camera = cv2.VideoCapture(0)
            self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self._detector = HandDetector()
            self._recognizer = GestureRecognizer()
            
            # Check if MediaPipe is actually available
            if not self._detector.available:
                print("❌ Hand tracking unavailable (MediaPipe requires Python 3.12 or earlier)")
                print("   📥 To fix: Install Python 3.12 and reinstall dependencies")
                print("   📺 Camera preview will still show, but no hand tracking")
                print()
            else:
                print("✅ Gesture control ready!")
                print(f"   - Show ✋ open palm to move cursor")
                print(f"   - Point ☝️ to click")
                print(f"   - Make ✌️ peace sign for right-click")
                print(f"   - Press 'q' to quit")
                print()
            
        except Exception as e:
            print(f"❌ Failed to initialize gesture control: {e}")
            self.enable_gesture = False
    
    def _init_voice(self):
        """Initialize voice control."""
        print("🎤 Initializing voice control...")
        
        try:
            self._tts = TextToSpeech()
            self._listener = VoiceListener()
            
            if self._listener.available:
                @self._listener.on_command
                def handle_voice(command):
                    self._handle_voice_command(command.text)
                
                self._listener.start()
                print("✅ Voice control ready! Say 'Jarvis' to activate.")
            else:
                print("⚠️  Voice input not available (install SpeechRecognition)")
                
        except Exception as e:
            print(f"❌ Failed to initialize voice: {e}")
            self.enable_voice = False
    
    def _init_vision(self):
        """Initialize vision module."""
        print("👁️  Initializing vision module...")
        
        try:
            self._screen_capture = ScreenCapture()
            self._gemini_vision = GeminiVision()
            print("✅ Vision module ready!")
            
        except Exception as e:
            print(f"⚠️  Vision module partially initialized: {e}")
            # Vision can work without API key for screenshots
    
    def _run_gesture_loop(self):
        """Main gesture control loop."""
        print("\n🎬 Starting gesture control. Press 'q' to quit.\n")
        
        while self._running:
            # Read frame
            ret, frame = self._camera.read()
            if not ret:
                continue
            
            # Flip horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Detect hands
            hands = self._detector.detect(frame)
            
            if hands:
                hand = hands[0]
                
                # Recognize gesture
                gesture_state = self._recognizer.recognize(hand)
                
                # Handle gesture
                self._handle_gesture(gesture_state, hand, frame)
                
                # Draw landmarks
                frame = self._detector.draw_landmarks(frame, hand)
                
                # Draw gesture info
                self._draw_gesture_info(frame, gesture_state)
            
            # 🚀 RENDER SCI-FI HUD OVERLAY
            frame = self._render_scifi_hud(frame, hands)
            
            # Show preview
            if self.show_preview:
                preview = cv2.resize(frame, (PREVIEW_WIDTH, PREVIEW_HEIGHT))
                cv2.imshow("Jarvis - Gesture Control", preview)
            
            # Check for quit
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
    
    def _handle_gesture(self, gesture_state, hand, frame):
        """Process detected gesture."""
        gesture = gesture_state.gesture
        is_held = gesture_state.is_held
        
        # Skip if in cooldown
        current_time = time.time()
        if current_time < self._gesture_cooldown:
            return
        
        # Get palm position for cursor control
        palm = hand.palm_center
        frame_h, frame_w = frame.shape[:2]
        
        # Handle different gestures
        if gesture == GestureType.OPEN_PALM and is_held:
            # Cursor movement
            self._move_cursor(palm, frame_w, frame_h)
            
        elif gesture == GestureType.POINT and is_held:
            # Left click
            pyautogui.click()
            self._gesture_cooldown = current_time + 0.5
            
        elif gesture == GestureType.PEACE and is_held:
            # Right click
            pyautogui.rightClick()
            self._gesture_cooldown = current_time + 0.5
            
        elif gesture == GestureType.FIST and is_held:
            # Drag mode
            if not self._dragging:
                pyautogui.mouseDown()
                self._dragging = True
            self._move_cursor(palm, frame_w, frame_h)
            
        elif gesture == GestureType.THUMBS_UP and is_held:
            # Scroll up
            pyautogui.scroll(3)
            self._gesture_cooldown = current_time + 0.2
            
        elif gesture == GestureType.THUMBS_DOWN and is_held:
            # Scroll down
            pyautogui.scroll(-3)
            self._gesture_cooldown = current_time + 0.2
            
        elif gesture == GestureType.THREE_FINGERS and is_held:
            # Middle click
            pyautogui.middleClick()
            self._gesture_cooldown = current_time + 0.5
        
        elif gesture == GestureType.PINCH:
            # 🚀 SCI-FI VOLUME CONTROL - Pinch and move up/down!
            if is_held:
                if not self._volume_mode:
                    # Just entered volume mode
                    self._volume_mode = True
                    self._volume_start_y = palm[1]
                    print("🔊 Volume control activated! Move hand up/down")
                else:
                    # Calculate volume based on hand movement
                    delta_y = self._volume_start_y - palm[1]  # Up = positive
                    volume_change = int(delta_y / 3)  # Sensitivity
                    
                    new_volume = max(0, min(100, self._current_volume + volume_change))
                    
                    if new_volume != self._current_volume:
                        # Apply volume change
                        if new_volume > self._current_volume:
                            for _ in range(min(5, new_volume - self._current_volume)):
                                pyautogui.press("volumeup")
                        else:
                            for _ in range(min(5, self._current_volume - new_volume)):
                                pyautogui.press("volumedown")
                        
                        self._current_volume = new_volume
                        self._volume_start_y = palm[1]  # Reset reference point
            else:
                # Released pinch - exit volume mode
                if self._volume_mode:
                    self._volume_mode = False
                    print(f"🔊 Volume set to {self._current_volume}%")
            
        elif gesture == GestureType.ROCK and is_held:
            # Voice activation
            self._say("Voice command mode activated")
            self._gesture_cooldown = current_time + 2.0
        
        elif gesture == GestureType.OK_SIGN:
            # ✨ TEXT SELECTION MODE - Make OK sign to start selecting!
            if is_held:
                if not self._selection_mode:
                    # Start selection
                    self._selection_mode = True
                    self._selection_start = pyautogui.position()
                    pyautogui.mouseDown()
                    print("📝 Selection mode! Move hand to select text...")
                else:
                    # Move while selecting (drag)
                    self._move_cursor(palm, frame_w, frame_h)
            else:
                # Released - complete selection
                if self._selection_mode:
                    pyautogui.mouseUp()
                    self._selection_mode = False
                    print("✅ Text selected!")
        
        # Release drag if fist is released
        if gesture != GestureType.FIST and self._dragging:
            pyautogui.mouseUp()
            self._dragging = False
    
    def _move_cursor(self, palm_pos, frame_w, frame_h):
        """Move cursor based on palm position - natural mapping."""
        # Frame is already flipped (mirror mode), so direct mapping works:
        # Move hand right -> cursor goes right
        # Move hand up -> cursor goes up
        
        # Map palm position (0 to frame_w/h) to screen with expanded range
        # Use only the central 60% of camera frame for full screen coverage
        margin_x = frame_w * 0.2  # 20% margin on each side
        margin_y = frame_h * 0.2
        
        # Normalize to 0-1 range within the active zone
        norm_x = (palm_pos[0] - margin_x) / (frame_w - 2 * margin_x)
        norm_y = (palm_pos[1] - margin_y) / (frame_h - 2 * margin_y)
        
        # Clamp to valid range
        norm_x = max(0, min(1, norm_x))
        norm_y = max(0, min(1, norm_y))
        
        # Map to screen coordinates
        screen_x = int(norm_x * self.screen_width)
        screen_y = int(norm_y * self.screen_height)
        
        # Apply screen margins
        screen_x = max(SCREEN_MARGIN, min(screen_x, self.screen_width - SCREEN_MARGIN))
        screen_y = max(SCREEN_MARGIN, min(screen_y, self.screen_height - SCREEN_MARGIN))
        
        # Lighter smoothing for more responsive feel (0.3 instead of 0.5)
        smoothing = 0.3
        last_x, last_y = self._last_cursor_pos
        
        # Initialize last position if first movement
        if last_x == 0 and last_y == 0:
            last_x, last_y = screen_x, screen_y
        
        smooth_x = int(last_x + (screen_x - last_x) * (1 - smoothing))
        smooth_y = int(last_y + (screen_y - last_y) * (1 - smoothing))
        
        # Move cursor
        pyautogui.moveTo(smooth_x, smooth_y)
        self._last_cursor_pos = (smooth_x, smooth_y)
    
    def _draw_gesture_info(self, frame, gesture_state):
        """Draw gesture information on frame."""
        gesture = gesture_state.gesture
        is_held = gesture_state.is_held
        
        # Get action info
        action = GESTURE_ACTIONS.get(gesture)
        
        if action:
            text = f"{action.name}"
            color = (0, 255, 0) if is_held else (0, 255, 255)
        else:
            text = "No gesture"
            color = (128, 128, 128)
        
        # Draw text
        cv2.putText(
            frame,
            text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            color,
            2,
        )
        
        # Draw hold indicator
        if is_held and action:
            cv2.putText(
                frame,
                "ACTIVE",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
        
        # 🚀 SCI-FI VOLUME HUD
        if self._volume_mode:
            h, w = frame.shape[:2]
            
            # Draw volume bar background (right side)
            bar_x = w - 50
            bar_h = 200
            bar_y = (h - bar_h) // 2
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + 30, bar_y + bar_h), (50, 50, 50), -1)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + 30, bar_y + bar_h), (0, 255, 255), 2)
            
            # Draw volume level (fill from bottom)
            fill_h = int((self._current_volume / 100) * bar_h)
            fill_y = bar_y + bar_h - fill_h
            
            # Gradient color: red (low) -> yellow (mid) -> green (high)
            if self._current_volume < 30:
                color = (0, 0, 255)  # Red
            elif self._current_volume < 70:
                color = (0, 255, 255)  # Yellow
            else:
                color = (0, 255, 0)  # Green
            
            cv2.rectangle(frame, (bar_x + 3, fill_y), (bar_x + 27, bar_y + bar_h - 3), color, -1)
            
            # Draw volume percentage
            cv2.putText(frame, f"{self._current_volume}%", (bar_x - 10, bar_y + bar_h + 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # Draw "VOLUME" label
            cv2.putText(frame, "VOL", (bar_x + 2, bar_y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            # Draw sci-fi corner brackets
            cv2.line(frame, (bar_x - 10, bar_y), (bar_x - 10, bar_y + 20), (0, 255, 255), 2)
            cv2.line(frame, (bar_x - 10, bar_y), (bar_x, bar_y), (0, 255, 255), 2)
            cv2.line(frame, (bar_x + 40, bar_y + bar_h), (bar_x + 40, bar_y + bar_h - 20), (0, 255, 255), 2)
            cv2.line(frame, (bar_x + 40, bar_y + bar_h), (bar_x + 30, bar_y + bar_h), (0, 255, 255), 2)
    
    def _render_scifi_hud(self, frame, hands):
        """Render Iron Man style sci-fi HUD overlay."""
        import math
        h, w = frame.shape[:2]
        current_time = time.time()
        
        # Color scheme (cyan/orange like Iron Man HUD)
        CYAN = (255, 255, 0)  # BGR
        ORANGE = (0, 165, 255)
        GREEN = (0, 255, 0)
        
        # ═══════════════════════════════════════════════════════
        # CORNER BRACKETS (Iron Man style)
        # ═══════════════════════════════════════════════════════
        bracket_len = 40
        bracket_offset = 15
        
        # Top-left
        cv2.line(frame, (bracket_offset, bracket_offset), (bracket_offset + bracket_len, bracket_offset), CYAN, 2)
        cv2.line(frame, (bracket_offset, bracket_offset), (bracket_offset, bracket_offset + bracket_len), CYAN, 2)
        
        # Top-right
        cv2.line(frame, (w - bracket_offset, bracket_offset), (w - bracket_offset - bracket_len, bracket_offset), CYAN, 2)
        cv2.line(frame, (w - bracket_offset, bracket_offset), (w - bracket_offset, bracket_offset + bracket_len), CYAN, 2)
        
        # Bottom-left
        cv2.line(frame, (bracket_offset, h - bracket_offset), (bracket_offset + bracket_len, h - bracket_offset), CYAN, 2)
        cv2.line(frame, (bracket_offset, h - bracket_offset), (bracket_offset, h - bracket_offset - bracket_len), CYAN, 2)
        
        # Bottom-right
        cv2.line(frame, (w - bracket_offset, h - bracket_offset), (w - bracket_offset - bracket_len, h - bracket_offset), CYAN, 2)
        cv2.line(frame, (w - bracket_offset, h - bracket_offset), (w - bracket_offset, h - bracket_offset - bracket_len), CYAN, 2)
        
        # ═══════════════════════════════════════════════════════
        # STATUS BAR (Top)
        # ═══════════════════════════════════════════════════════
        cv2.rectangle(frame, (80, 10), (w - 80, 35), (50, 50, 50), -1)
        cv2.rectangle(frame, (80, 10), (w - 80, 35), CYAN, 1)
        cv2.putText(frame, "J.A.R.V.I.S. INTERFACE v2.0", (w // 2 - 120, 28), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, CYAN, 1)
        
        # ═══════════════════════════════════════════════════════
        # SCANLINES (subtle holographic effect)
        # ═══════════════════════════════════════════════════════
        for y in range(0, h, 4):
            if y % 8 == 0:
                overlay = frame.copy()
                cv2.line(overlay, (0, y), (w, y), (50, 50, 50), 1)
                cv2.addWeighted(overlay, 0.1, frame, 0.9, 0, frame)
        
        # ═══════════════════════════════════════════════════════
        # HAND TRACKING RETICLE
        # ═══════════════════════════════════════════════════════
        if hands:
            for hand in hands:
                palm = hand.palm_center
                px, py = int(palm[0]), int(palm[1])
                
                # Animated circle radius
                pulse = int(20 + 5 * math.sin(current_time * 5))
                
                # Outer targeting circles
                cv2.circle(frame, (px, py), pulse + 20, CYAN, 1)
                cv2.circle(frame, (px, py), pulse + 30, CYAN, 1)
                
                # Cross-hairs
                cv2.line(frame, (px - 40, py), (px - 15, py), CYAN, 2)
                cv2.line(frame, (px + 15, py), (px + 40, py), CYAN, 2)
                cv2.line(frame, (px, py - 40), (px, py - 15), CYAN, 2)
                cv2.line(frame, (px, py + 15), (px, py + 40), CYAN, 2)
                
                # Small corner markers
                size = 8
                cv2.line(frame, (px - 50, py - 50), (px - 50 + size, py - 50), ORANGE, 2)
                cv2.line(frame, (px - 50, py - 50), (px - 50, py - 50 + size), ORANGE, 2)
                cv2.line(frame, (px + 50, py - 50), (px + 50 - size, py - 50), ORANGE, 2)
                cv2.line(frame, (px + 50, py - 50), (px + 50, py - 50 + size), ORANGE, 2)
                cv2.line(frame, (px - 50, py + 50), (px - 50 + size, py + 50), ORANGE, 2)
                cv2.line(frame, (px - 50, py + 50), (px - 50, py + 50 - size), ORANGE, 2)
                cv2.line(frame, (px + 50, py + 50), (px + 50 - size, py + 50), ORANGE, 2)
                cv2.line(frame, (px + 50, py + 50), (px + 50, py + 50 - size), ORANGE, 2)
                
                # Coordinates display
                cv2.putText(frame, f"X:{px} Y:{py}", (px + 55, py - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, CYAN, 1)
        
        # ═══════════════════════════════════════════════════════
        # BOTTOM STATUS PANEL
        # ═══════════════════════════════════════════════════════
        panel_y = h - 60
        cv2.rectangle(frame, (10, panel_y), (200, h - 10), (30, 30, 30), -1)
        cv2.rectangle(frame, (10, panel_y), (200, h - 10), CYAN, 1)
        
        # System status indicators
        cv2.circle(frame, (25, panel_y + 15), 5, GREEN, -1)
        cv2.putText(frame, "GESTURE", (35, panel_y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.35, CYAN, 1)
        
        cv2.circle(frame, (25, panel_y + 30), 5, GREEN if self._listener else ORANGE, -1)
        cv2.putText(frame, "VOICE", (35, panel_y + 33), cv2.FONT_HERSHEY_SIMPLEX, 0.35, CYAN, 1)
        
        cv2.circle(frame, (110, panel_y + 15), 5, GREEN if self._gemini_vision else ORANGE, -1)
        cv2.putText(frame, "VISION", (120, panel_y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.35, CYAN, 1)
        
        # FPS counter (simulated)
        cv2.putText(frame, f"FPS: 30", (110, panel_y + 33), cv2.FONT_HERSHEY_SIMPLEX, 0.35, CYAN, 1)
        
        # ═══════════════════════════════════════════════════════
        # SELECTION MODE INDICATOR
        # ═══════════════════════════════════════════════════════
        if self._selection_mode:
            # Pulsing selection indicator
            pulse = int(255 * (0.5 + 0.5 * math.sin(current_time * 6)))
            selection_color = (pulse, 100, 255)  # Pulsing magenta
            
            cv2.rectangle(frame, (w//4, 10), (3*w//4, 40), (50, 50, 50), -1)
            cv2.rectangle(frame, (w//4, 10), (3*w//4, 40), selection_color, 2)
            cv2.putText(frame, "📝 SELECTING TEXT...", (w//2 - 80, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, selection_color, 2)
        
        # ═══════════════════════════════════════════════════════
        # RIGHT SIDE INFO PANEL
        # ═══════════════════════════════════════════════════════
        if not self._volume_mode and not self._selection_mode:
            info_x = w - 150
            cv2.rectangle(frame, (info_x, 50), (w - 10, 165), (30, 30, 30), -1)
            cv2.rectangle(frame, (info_x, 50), (w - 10, 165), CYAN, 1)
            cv2.putText(frame, "GESTURES", (info_x + 10, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.4, ORANGE, 1)
            cv2.putText(frame, "Palm: Move", (info_x + 10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.35, CYAN, 1)
            cv2.putText(frame, "Point: Click", (info_x + 10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.35, CYAN, 1)
            cv2.putText(frame, "Peace: R-Click", (info_x + 10, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.35, CYAN, 1)
            cv2.putText(frame, "Pinch: Volume", (info_x + 10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.35, CYAN, 1)
            cv2.putText(frame, "OK: Select", (info_x + 10, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.35, GREEN, 1)
            cv2.putText(frame, "Fist: Drag", (info_x + 10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.35, CYAN, 1)
            cv2.putText(frame, "Peace: R-Click", (info_x + 10, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.35, CYAN, 1)
            cv2.putText(frame, "Pinch: Volume", (info_x + 10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.35, CYAN, 1)
            cv2.putText(frame, "Fist: Drag", (info_x + 10, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.35, CYAN, 1)
        
        return frame
    
    def _handle_voice_command(self, command: str):
        """Process voice command and execute actions."""
        command_lower = command.lower().strip()
        print(f"🎤 Voice command: {command}")
        
        # Import tools
        from .tools.system_tools import open_app, close_window, search_start_menu
        from .tools.mouse_tools import click_mouse, scroll_mouse
        from .tools.keyboard_tools import type_text, press_key, hotkey
        from .tools.vision_tools import take_screenshot
        
        try:
            # Common websites mapping
            websites = {
                "youtube": "https://www.youtube.com",
                "google": "https://www.google.com",
                "gmail": "https://mail.google.com",
                "twitter": "https://twitter.com",
                "x": "https://twitter.com",
                "facebook": "https://www.facebook.com",
                "instagram": "https://www.instagram.com",
                "reddit": "https://www.reddit.com",
                "github": "https://github.com",
                "linkedin": "https://www.linkedin.com",
                "amazon": "https://www.amazon.com",
                "netflix": "https://www.netflix.com",
                "spotify": "https://open.spotify.com",
                "whatsapp": "https://web.whatsapp.com",
                "chatgpt": "https://chat.openai.com",
            }
            
            # Check for website commands
            if any(word in command_lower for word in ["open", "go to", "launch"]):
                import webbrowser
                
                # Check if it's a known website
                for site_name, url in websites.items():
                    if site_name in command_lower:
                        webbrowser.open(url)
                        self._say(f"Opening {site_name}")
                        print(f"   Opened: {url}")
                        return
                
                # Check for direct URL
                if "http" in command_lower or ".com" in command_lower or ".org" in command_lower:
                    # Extract URL-like text
                    words = command_lower.split()
                    for word in words:
                        if "." in word:
                            url = word if word.startswith("http") else f"https://{word}"
                            webbrowser.open(url)
                            self._say(f"Opening {word}")
                            return
            
            # Open app commands (for desktop apps)
            if any(word in command_lower for word in ["open", "launch", "start"]):
                # Extract app name
                for trigger in ["open ", "launch ", "start "]:
                    if trigger in command_lower:
                        app_name = command_lower.split(trigger, 1)[1].strip()
                        # Skip if it's a website we already handled
                        if any(site in app_name for site in websites.keys()):
                            continue
                        result = open_app(app_name)
                        self._say(f"Opening {app_name}")
                        print(f"   Result: {result}")
                        return
            
            # Close window
            if any(word in command_lower for word in ["close", "exit", "quit"]):
                result = close_window()
                self._say("Closing window")
                print(f"   Result: {result}")
                return
            
            # Screenshot
            if "screenshot" in command_lower or "capture" in command_lower:
                result = take_screenshot()
                self._say("Screenshot taken")
                print(f"   Result: {result.get('status', 'done')}")
                return
            
            # Scroll commands
            if "scroll" in command_lower:
                if "up" in command_lower:
                    result = scroll_mouse(direction="up", amount=5)
                    self._say("Scrolling up")
                elif "down" in command_lower:
                    result = scroll_mouse(direction="down", amount=5)
                    self._say("Scrolling down")
                print(f"   Result: {result}")
                return
            
            # Click commands
            if "click" in command_lower:
                if "right" in command_lower:
                    result = click_mouse(button="right")
                    self._say("Right click")
                elif "double" in command_lower:
                    result = click_mouse(clicks=2)
                    self._say("Double click")
                else:
                    result = click_mouse()
                    self._say("Click")
                print(f"   Result: {result}")
                return
            
            # Type text
            if command_lower.startswith("type "):
                text = command[5:].strip()
                result = type_text(text)
                self._say(f"Typing: {text}")
                print(f"   Result: {result}")
                return
            
            # Search
            if "search" in command_lower:
                query = command_lower.replace("search", "").replace("for", "").strip()
                if query:
                    result = search_start_menu(query)
                    self._say(f"Searching for {query}")
                    print(f"   Result: {result}")
                return
            
            # Keyboard shortcuts
            if "copy" in command_lower:
                result = hotkey("ctrl", "c")
                self._say("Copied")
                return
            if "paste" in command_lower:
                result = hotkey("ctrl", "v")
                self._say("Pasted")
                return
            if "undo" in command_lower:
                result = hotkey("ctrl", "z")
                self._say("Undo")
                return
            if "save" in command_lower:
                result = hotkey("ctrl", "s")
                self._say("Saved")
                return
            
            # Volume control
            if "volume" in command_lower:
                import re
                import subprocess
                
                # Check for specific volume level (e.g., "volume to 50")
                match = re.search(r'(\d+)', command_lower)
                if match and ("to" in command_lower or "set" in command_lower):
                    volume_level = int(match.group(1))
                    volume_level = max(0, min(100, volume_level))  # Clamp 0-100
                    
                    # Use PowerShell to set volume (Windows)
                    ps_script = f'''
                    $vol = [audio.volume]::new()
                    $vol.SetMasterVolumeLevelScalar({volume_level/100}, [System.Guid]::Empty)
                    '''
                    # Alternative: use nircmd if available, or multiple key presses
                    # For now, simulate with key presses
                    # Mute first, then set approximate level
                    try:
                        subprocess.run([
                            'powershell', '-Command',
                            f'(New-Object -ComObject WScript.Shell).SendKeys([char]173); Start-Sleep -Milliseconds 100; $wshell = New-Object -ComObject wscript.shell; for($i=0; $i -lt {volume_level // 2}; $i++) {{ $wshell.SendKeys([char]175) }}'
                        ], capture_output=True, timeout=5)
                        self._say(f"Volume set to {volume_level}")
                    except:
                        # Fallback
                        for _ in range(volume_level // 4):
                            press_key("volumeup")
                        self._say(f"Volume set to approximately {volume_level}")
                elif "up" in command_lower or "louder" in command_lower or "increase" in command_lower:
                    result = press_key("volumeup")
                    self._say("Volume up")
                elif "down" in command_lower or "quieter" in command_lower or "decrease" in command_lower:
                    result = press_key("volumedown") 
                    self._say("Volume down")
                elif "mute" in command_lower:
                    result = press_key("volumemute")
                    self._say("Muted")
                elif "max" in command_lower or "full" in command_lower:
                    for _ in range(50):  # Press up many times
                        press_key("volumeup")
                    self._say("Volume at maximum")
                return
            
            # Media controls
            if any(word in command_lower for word in ["play", "pause", "stop music", "resume"]):
                result = press_key("playpause")
                self._say("Play pause")
                return
            if "next" in command_lower and any(word in command_lower for word in ["song", "track", "music"]):
                result = press_key("nexttrack")
                self._say("Next track")
                return
            if "previous" in command_lower and any(word in command_lower for word in ["song", "track", "music"]):
                result = press_key("prevtrack")
                self._say("Previous track")
                return
            
            # Window controls
            if "minimize" in command_lower:
                if "all" in command_lower:
                    result = hotkey("win", "d")
                    self._say("Minimizing all windows")
                else:
                    result = hotkey("win", "down")
                    self._say("Minimizing window")
                return
            if "maximize" in command_lower:
                result = hotkey("win", "up")
                self._say("Maximizing window")
                return
            if any(word in command_lower for word in ["switch window", "switch app", "alt tab", "next window"]):
                result = hotkey("alt", "tab")
                self._say("Switching window")
                return
            if "show desktop" in command_lower or "hide all" in command_lower:
                result = hotkey("win", "d")
                self._say("Showing desktop")
                return
            
            # System controls
            import os
            if "lock" in command_lower and any(word in command_lower for word in ["screen", "computer", "pc"]):
                os.system("rundll32.exe user32.dll,LockWorkStation")
                self._say("Locking computer")
                return
            if "sleep" in command_lower and any(word in command_lower for word in ["computer", "pc", "mode"]):
                self._say("Putting computer to sleep")
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                return
            if "shutdown" in command_lower:
                self._say("Are you sure? Say shutdown confirm to proceed")
                return
            if "shutdown confirm" in command_lower:
                self._say("Shutting down in 10 seconds")
                os.system("shutdown /s /t 10")
                return
            if "restart" in command_lower:
                self._say("Restarting in 10 seconds")
                os.system("shutdown /r /t 10")
                return
            if "cancel shutdown" in command_lower:
                os.system("shutdown /a")
                self._say("Shutdown cancelled")
                return
            
            # Open system apps
            if "task manager" in command_lower:
                result = hotkey("ctrl", "shift", "esc")
                self._say("Opening task manager")
                return
            if "settings" in command_lower:
                result = hotkey("win", "i")
                self._say("Opening settings")
                return
            if "file explorer" in command_lower or "my computer" in command_lower:
                result = hotkey("win", "e")
                self._say("Opening file explorer")
                return
            if "run" in command_lower and "dialog" in command_lower:
                result = hotkey("win", "r")
                self._say("Opening run dialog")
                return
            if "notification" in command_lower or "action center" in command_lower:
                result = hotkey("win", "a")
                self._say("Opening action center")
                return
            
            # Brightness (Windows 10/11)
            if "brightness" in command_lower:
                import subprocess
                if "up" in command_lower or "increase" in command_lower:
                    subprocess.run(["powershell", "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,80)"], capture_output=True)
                    self._say("Brightness increased")
                elif "down" in command_lower or "decrease" in command_lower:
                    subprocess.run(["powershell", "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,30)"], capture_output=True)
                    self._say("Brightness decreased")
                return
            
            # Screen analysis commands
            if any(word in command_lower for word in ["screen", "see", "look", "what is", "what's on", "describe"]):
                self._say("Let me see what's on your screen")
                try:
                    if self._gemini_vision:
                        import asyncio
                        # Capture and analyze screen
                        if self._screen_capture:
                            self._screen_capture.start()
                            import time
                            time.sleep(0.5)  # Wait for frame
                            frame = self._screen_capture.get_latest_frame()
                            self._screen_capture.stop()
                            
                            if frame:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                result = loop.run_until_complete(
                                    self._gemini_vision.analyze_screen(frame)
                                )
                                loop.close()
                                self._say(result)
                                print(f"   Screen analysis: {result}")
                                return
                    self._say("I can see your screen but need an API key to analyze it")
                except Exception as e:
                    print(f"   Screen analysis error: {e}")
                    self._say("Sorry, I couldn't analyze the screen")
                return
            # ═══════════════════════════════════════════════════════
            # AI SCREEN CONTROLLER - Let AI navigate for you!
            # ═══════════════════════════════════════════════════════
            if any(word in command_lower for word in ["navigate", "find and click", "go to", "click on", "locate", "show me where"]):
                self._say("Let me take control and navigate for you")
                import asyncio
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._ai_screen_control(command))
                    loop.close()
                except Exception as e:
                    print(f"   AI Screen Control Error: {e}")
                return
            
            # General AI questions - use Gemini to answer
            try:
                from google import genai
                from .config import GOOGLE_API_KEY
                
                if GOOGLE_API_KEY:
                    client = genai.Client(api_key=GOOGLE_API_KEY)
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=f"You are Jarvis, a helpful AI assistant. Answer briefly in 1-2 sentences. User asked: {command}"
                    )
                    answer = response.text.strip()
                    self._say(answer)
                    print(f"   AI Response: {answer}")
                else:
                    self._say(f"I heard: {command}. Please set your Google API key for AI responses.")
            except Exception as e:
                print(f"   AI Error: {e}")
                self._say(f"I heard: {command}")
            
        except Exception as e:
            print(f"❌ Error executing command: {e}")
            self._say("Sorry, there was an error")
    
    async def _ai_screen_control(self, command: str):
        """AI-powered screen navigation - sees screen and performs actions."""
        from google import genai
        from .config import GOOGLE_API_KEY
        import pyautogui
        import json
        import re
        
        if not GOOGLE_API_KEY:
            self._say("I need a Google API key for AI screen control")
            return
        
        try:
            # Capture current screen
            screenshot = pyautogui.screenshot()
            
            # Convert to bytes for Gemini
            import io
            img_buffer = io.BytesIO()
            screenshot.save(img_buffer, format='JPEG', quality=80)
            img_bytes = img_buffer.getvalue()
            
            # Create Gemini client
            client = genai.Client(api_key=GOOGLE_API_KEY)
            
            # AI prompt for screen analysis
            prompt = f"""You are an AI screen controller. Analyze this screenshot and help the user with: "{command}"

Return a JSON action to perform. Available actions:
- {{"action": "click", "x": 500, "y": 300, "description": "what you're clicking"}}
- {{"action": "double_click", "x": 500, "y": 300, "description": "what you're clicking"}}
- {{"action": "right_click", "x": 500, "y": 300, "description": "what you're clicking"}}
- {{"action": "type", "text": "text to type", "description": "where you're typing"}}
- {{"action": "scroll", "direction": "up" or "down", "amount": 5}}
- {{"action": "hotkey", "keys": ["ctrl", "c"], "description": "shortcut purpose"}}
- {{"action": "speak", "message": "response to user"}}

Screen resolution: {screenshot.width}x{screenshot.height}

IMPORTANT: 
- Look at the ACTUAL screen content to find UI elements
- Provide EXACT pixel coordinates for clicks
- If you can't find what the user wants, use "speak" action to explain

Return ONLY the JSON, no other text."""

            # Send to Gemini
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    {"mime_type": "image/jpeg", "data": img_bytes},
                    prompt
                ]
            )
            
            result_text = response.text.strip()
            print(f"   AI Decision: {result_text}")
            
            # Parse JSON response
            # Find JSON in response
            json_match = re.search(r'\{[^{}]*\}', result_text)
            if json_match:
                action_data = json.loads(json_match.group())
                
                action = action_data.get("action", "speak")
                
                if action == "click":
                    x, y = action_data.get("x", 0), action_data.get("y", 0)
                    desc = action_data.get("description", "target")
                    self._say(f"Clicking on {desc}")
                    pyautogui.click(x, y)
                    
                elif action == "double_click":
                    x, y = action_data.get("x", 0), action_data.get("y", 0)
                    desc = action_data.get("description", "target")
                    self._say(f"Double clicking on {desc}")
                    pyautogui.doubleClick(x, y)
                    
                elif action == "right_click":
                    x, y = action_data.get("x", 0), action_data.get("y", 0)
                    desc = action_data.get("description", "target")
                    self._say(f"Right clicking on {desc}")
                    pyautogui.rightClick(x, y)
                    
                elif action == "type":
                    text = action_data.get("text", "")
                    desc = action_data.get("description", "")
                    self._say(f"Typing {text}")
                    pyautogui.typewrite(text, interval=0.05)
                    
                elif action == "scroll":
                    direction = action_data.get("direction", "down")
                    amount = action_data.get("amount", 5)
                    self._say(f"Scrolling {direction}")
                    scroll_amount = amount if direction == "up" else -amount
                    pyautogui.scroll(scroll_amount)
                    
                elif action == "hotkey":
                    keys = action_data.get("keys", [])
                    desc = action_data.get("description", "")
                    self._say(f"Pressing {' + '.join(keys)}")
                    pyautogui.hotkey(*keys)
                    
                elif action == "speak":
                    message = action_data.get("message", "I'm not sure how to help with that")
                    self._say(message)
                    
            else:
                self._say("I couldn't understand the screen. Please try again.")
                
        except Exception as e:
            print(f"   AI Screen Control Error: {e}")
            self._say("Sorry, there was an error analyzing the screen")
    
    def _say(self, text: str):
        """Speak text using Google TTS (non-blocking)."""
        print(f"🤖 {text}")
        
        # Run Google TTS in a separate thread to avoid blocking
        import threading
        def speak_thread():
            try:
                from gtts import gTTS
                import pygame
                import io
                import tempfile
                import os
                
                # Generate speech
                tts = gTTS(text=text, lang='en', slow=False)
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                    temp_file = fp.name
                    tts.save(temp_file)
                
                # Play using pygame
                pygame.mixer.init()
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                pygame.mixer.quit()
                
                # Clean up
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
            except Exception as e:
                print(f"   TTS Error: {e}")
                # Fallback to pyttsx3
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 175)
                    engine.say(text)
                    engine.runAndWait()
                    engine.stop()
                except:
                    pass
        
        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Jarvis AI Assistant")
    parser.add_argument("--no-gesture", action="store_true", help="Disable gesture control")
    parser.add_argument("--no-voice", action="store_true", help="Disable voice control")
    parser.add_argument("--no-vision", action="store_true", help="Disable vision features")
    parser.add_argument("--no-preview", action="store_true", help="Hide camera preview")
    
    args = parser.parse_args()
    
    controller = JarvisController(
        enable_gesture=not args.no_gesture,
        enable_voice=not args.no_voice,
        enable_vision=not args.no_vision,
        show_preview=not args.no_preview,
    )
    
    try:
        controller.start()
    except KeyboardInterrupt:
        controller.stop()


if __name__ == "__main__":
    main()
