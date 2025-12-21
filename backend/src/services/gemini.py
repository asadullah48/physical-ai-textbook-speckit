"""Gemini API wrapper for chat completions."""

import logging
from typing import AsyncGenerator, Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from src.api.config import get_settings
from src.services.embeddings import configure_gemini_api

logger = logging.getLogger(__name__)


class GeminiChatService:
    """Wrapper for Gemini chat completions."""

    def __init__(self) -> None:
        """Initialize the Gemini chat service."""
        configure_gemini_api()
        settings = get_settings()
        self.model_name = settings.gemini_model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=GenerationConfig(
                temperature=0.3,  # Lower temperature for factual responses
                top_p=0.95,
                top_k=40,
                max_output_tokens=2048,
            ),
        )

    async def generate_response(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
    ) -> tuple[str, dict]:
        """Generate a complete response from Gemini.

        Args:
            messages: List of message dictionaries with role and parts.
            temperature: Optional temperature override.

        Returns:
            Tuple of (response text, usage metadata).
        """
        try:
            # Build chat from messages
            chat = self.model.start_chat(history=messages[:-1])

            # Get the last user message
            last_message = messages[-1]

            # Generate response
            response = chat.send_message(
                last_message["parts"][0],
                generation_config=GenerationConfig(
                    temperature=temperature if temperature is not None else 0.3,
                ),
            )

            # Extract usage metadata
            usage = {
                "input_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                "output_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
            }

            return response.text, usage

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    async def stream_response(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a response from Gemini.

        Args:
            messages: List of message dictionaries with role and parts.
            temperature: Optional temperature override.

        Yields:
            Response text chunks.
        """
        try:
            # Build chat from messages
            chat = self.model.start_chat(history=messages[:-1])

            # Get the last user message
            last_message = messages[-1]

            # Generate streaming response
            response = chat.send_message(
                last_message["parts"][0],
                generation_config=GenerationConfig(
                    temperature=temperature if temperature is not None else 0.3,
                ),
                stream=True,
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise

    async def count_tokens(self, text: str) -> int:
        """Count tokens in a text string.

        Args:
            text: The text to count tokens for.

        Returns:
            Token count.
        """
        try:
            result = self.model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            # Rough estimate: ~4 characters per token
            return len(text) // 4


# Global service instance
_gemini_service: Optional[GeminiChatService] = None


def get_gemini_service() -> GeminiChatService:
    """Get or create the Gemini service instance.

    Returns:
        GeminiChatService instance.
    """
    global _gemini_service

    if _gemini_service is None:
        _gemini_service = GeminiChatService()

    return _gemini_service
