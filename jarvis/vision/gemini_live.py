"""
Gemini Vision Module
~~~~~~~~~~~~~~~~~~~~

Integrates with Gemini 2.0 for real-time screen understanding
and visual AI assistance.
"""

import asyncio
import base64
from typing import Optional, AsyncGenerator
from dataclasses import dataclass

from google import genai
from google.genai import types

from ..config import GOOGLE_API_KEY, GEMINI_MODEL
from .screen_capture import ScreenFrame


@dataclass
class VisionResponse:
    """Response from Gemini vision analysis."""
    
    text: str
    model: str
    finish_reason: str
    
    @property
    def success(self) -> bool:
        return bool(self.text)


class GeminiVision:
    """
    Gemini 2.0 Vision integration for screen understanding.
    
    Provides real-time screen analysis, descriptions, and
    intelligent assistance based on visual context.
    
    Example:
        vision = GeminiVision()
        
        # Analyze a screenshot
        frame = screen_capture.capture_now()
        response = await vision.analyze_screen(frame)
        print(response.text)
        
        # Ask a question about the screen
        response = await vision.ask_about_screen(
            frame,
            "What application is open?"
        )
    """
    
    # System prompt for screen analysis
    SCREEN_ANALYSIS_PROMPT = """You are Jarvis, an AI assistant that can see the user's screen.
Your role is to:
1. Describe what's currently visible on screen when asked
2. Help the user navigate and interact with applications
3. Provide helpful suggestions based on the visual context
4. Answer questions about on-screen content

Be concise but informative. Focus on actionable information."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = GEMINI_MODEL,
    ):
        """
        Initialize Gemini Vision.
        
        Args:
            api_key: Google AI API key. Uses GOOGLE_API_KEY from env if not provided.
            model: Gemini model to use.
        """
        self.api_key = api_key or GOOGLE_API_KEY
        self.model = model
        
        if not self.api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY in .env or pass api_key parameter."
            )
        
        # Initialize client
        self.client = genai.Client(api_key=self.api_key)
    
    async def analyze_screen(
        self,
        frame: ScreenFrame,
        prompt: Optional[str] = None,
    ) -> VisionResponse:
        """
        Analyze a screen capture with Gemini.
        
        Args:
            frame: ScreenFrame to analyze.
            prompt: Optional custom prompt. Defaults to general screen description.
        
        Returns:
            VisionResponse with analysis text.
        """
        if prompt is None:
            prompt = "Describe what's visible on this screen. Be concise and focus on the main content and active application."
        
        try:
            # Create image part
            image_data = frame.to_base64()
            
            # Make request
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part(
                                inline_data=types.Blob(
                                    mime_type="image/jpeg",
                                    data=base64.b64decode(image_data),
                                )
                            ),
                            types.Part(text=prompt),
                        ],
                    )
                ],
            )
            
            return VisionResponse(
                text=response.text,
                model=self.model,
                finish_reason=str(response.candidates[0].finish_reason) if response.candidates else "unknown",
            )
            
        except Exception as e:
            return VisionResponse(
                text=f"Error analyzing screen: {str(e)}",
                model=self.model,
                finish_reason="error",
            )
    
    async def ask_about_screen(
        self,
        frame: ScreenFrame,
        question: str,
    ) -> VisionResponse:
        """
        Ask a specific question about the screen content.
        
        Args:
            frame: ScreenFrame to analyze.
            question: Question to ask about the screen.
        
        Returns:
            VisionResponse with the answer.
        """
        prompt = f"""Look at this screenshot and answer the following question:

Question: {question}

Provide a clear, concise answer based on what you can see on the screen."""
        
        return await self.analyze_screen(frame, prompt)
    
    async def find_element(
        self,
        frame: ScreenFrame,
        element_description: str,
    ) -> VisionResponse:
        """
        Find a UI element on screen based on description.
        
        Args:
            frame: ScreenFrame to search.
            element_description: Description of the element to find.
        
        Returns:
            VisionResponse with location/instructions.
        """
        prompt = f"""Look at this screenshot and find the following element:

Element: {element_description}

If you find it, describe its location on screen (e.g., "top-left corner", "center of screen", "in the toolbar").
If you can't find it, say so and suggest where it might be."""
        
        return await self.analyze_screen(frame, prompt)
    
    async def get_next_action(
        self,
        frame: ScreenFrame,
        task: str,
    ) -> VisionResponse:
        """
        Get suggested next action to complete a task.
        
        Args:
            frame: Current screen state.
            task: The task the user wants to complete.
        
        Returns:
            VisionResponse with suggested action.
        """
        prompt = f"""You are helping the user complete this task: {task}

Look at the current screen state and suggest the next action to take.
Be specific - mention which button to click, what to type, etc.
If the task appears complete, say so."""
        
        return await self.analyze_screen(frame, prompt)
    
    def analyze_screen_sync(
        self,
        frame: ScreenFrame,
        prompt: Optional[str] = None,
    ) -> VisionResponse:
        """Synchronous version of analyze_screen."""
        return asyncio.run(self.analyze_screen(frame, prompt))
    
    def ask_about_screen_sync(
        self,
        frame: ScreenFrame,
        question: str,
    ) -> VisionResponse:
        """Synchronous version of ask_about_screen."""
        return asyncio.run(self.ask_about_screen(frame, question))
