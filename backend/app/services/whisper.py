"""Speech-to-text via the OpenAI Whisper API."""

from __future__ import annotations

from pathlib import Path

from app.config import get_settings
from app.core.schemas import TranscriptionResponse
from app.services.openai_client import get_openai_client


async def transcribe_file(path: Path) -> TranscriptionResponse:
    """Transcribe an audio file using the configured Whisper model."""
    settings = get_settings()
    client = get_openai_client()

    with path.open("rb") as audio:
        result = await client.audio.transcriptions.create(
            model=settings.openai_whisper_model,
            file=audio,
            response_format="verbose_json",
        )

    # The verbose_json response shape gives us extra metadata when available.
    text = getattr(result, "text", "") or ""
    duration = getattr(result, "duration", None)
    language = getattr(result, "language", None)
    return TranscriptionResponse(text=text, duration=duration, language=language)
