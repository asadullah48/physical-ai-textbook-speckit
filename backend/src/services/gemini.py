"""Gemini chat completions on the current ``google-genai`` SDK.

Prompts are built as ``[{"role": "user"|"model", "parts": [str, ...]}]``
(see prompts.py); ``_to_contents`` converts them to SDK content objects. The
last message is the new turn; everything before it is chat history.
"""

import logging
from typing import AsyncGenerator, Optional

from google.genai import types

from src.api.config import get_settings
from src.services.embeddings import get_genai_client

logger = logging.getLogger(__name__)


def _to_contents(messages: list[dict]) -> list[types.Content]:
    return [
        types.Content(role=m["role"], parts=[types.Part(text=str(p)) for p in m["parts"]])
        for m in messages
    ]


def _usage(response) -> dict:
    meta = getattr(response, "usage_metadata", None)
    return {
        "input_tokens": getattr(meta, "prompt_token_count", 0) or 0,
        "output_tokens": getattr(meta, "candidates_token_count", 0) or 0,
    }


class GeminiChatService:
    """Wrapper for Gemini chat completions."""

    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.gemini_model
        self.client = get_genai_client()

    def _config(self, temperature: Optional[float]) -> types.GenerateContentConfig:
        # Low temperature: answers should restate the textbook, not improvise.
        return types.GenerateContentConfig(
            temperature=0.3 if temperature is None else temperature,
            top_p=0.95,
            max_output_tokens=2048,
        )

    def _chat(self, messages: list[dict], temperature: Optional[float]):
        contents = _to_contents(messages)
        chat = self.client.aio.chats.create(
            model=self.model_name, config=self._config(temperature), history=contents[:-1]
        )
        return chat, contents[-1].parts

    async def generate_response(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
    ) -> tuple[str, dict]:
        """Generate a complete response; returns (text, token usage)."""
        try:
            chat, parts = self._chat(messages, temperature)
            response = await chat.send_message(parts)
            return response.text or "", _usage(response)
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    async def stream_response(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream response text chunks."""
        try:
            chat, parts = self._chat(messages, temperature)
            async for chunk in await chat.send_message_stream(parts):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise

    async def count_tokens(self, text: str) -> int:
        """Count tokens in a text string (rough estimate if the API fails)."""
        try:
            result = await self.client.aio.models.count_tokens(model=self.model_name, contents=text)
            return result.total_tokens or 0
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
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
