"""Lazy singleton wrapper around the OpenAI async client."""

from __future__ import annotations

from functools import lru_cache

from openai import AsyncOpenAI

from app.config import get_settings


class OpenAINotConfigured(RuntimeError):
    """Raised when the OpenAI API key is missing."""


@lru_cache(maxsize=1)
def get_openai_client() -> AsyncOpenAI:
    """Return a cached AsyncOpenAI client.

    Raises:
        OpenAINotConfigured: if no API key is configured.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        raise OpenAINotConfigured(
            "OPENAI_API_KEY is not set. Add it to your environment or .env file."
        )
    return AsyncOpenAI(api_key=settings.openai_api_key)


def openai_is_configured() -> bool:
    return bool(get_settings().openai_api_key)
