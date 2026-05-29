"""Speech-to-text endpoint backed by Whisper."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.schemas import TranscriptionResponse
from app.services.openai_client import OpenAINotConfigured
from app.services.whisper import transcribe_file

router = APIRouter(prefix="/stt", tags=["stt"])

_ALLOWED_SUFFIXES = {
    ".wav",
    ".mp3",
    ".m4a",
    ".webm",
    ".ogg",
    ".flac",
    ".mp4",
    ".mpeg",
    ".mpga",
}
_MAX_BYTES = 25 * 1024 * 1024  # 25 MB Whisper API limit


@router.post("", response_model=TranscriptionResponse)
async def transcribe(audio: UploadFile = File(...)) -> TranscriptionResponse:
    filename = audio.filename or "upload"
    suffix = Path(filename).suffix.lower() or ".webm"
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported audio format: {suffix}",
        )

    data = await audio.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="audio file is empty",
        )
    if len(data) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="audio file exceeds 25 MB Whisper limit",
        )

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    try:
        return await transcribe_file(tmp_path)
    except OpenAINotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"transcription failed: {exc}",
        ) from exc
    finally:
        tmp_path.unlink(missing_ok=True)
