"""Summarize the contents of a local file using OpenAI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.services.openai_client import get_openai_client
from app.tools.base import Tool, ToolError

_MAX_RAW_CHARS = 60_000


class FileSummarizerArgs(BaseModel):
    path: str = Field(description="Absolute or user-relative path to the file to summarize.")
    instructions: str | None = Field(
        default=None,
        description="Optional extra instructions (e.g. 'focus on action items').",
    )
    max_words: int = Field(
        default=200,
        ge=20,
        le=2000,
        description="Target maximum number of words in the summary.",
    )


class FileSummarizerTool(Tool):
    """Read a text-like file and produce a concise summary."""

    name = "summarize_file"
    description = (
        "Read a local file (txt, md, log, csv, json, pdf, docx) and return a "
        "concise summary. Use this whenever the user asks to summarize, "
        "review, or extract key points from a document on disk."
    )
    parameters_model = FileSummarizerArgs

    async def run(
        self,
        path: str,
        instructions: str | None,
        max_words: int,
    ) -> dict[str, Any]:
        resolved = Path(path).expanduser()
        if not resolved.exists():
            raise ToolError(f"file not found: {resolved}")
        if not resolved.is_file():
            raise ToolError(f"not a regular file: {resolved}")

        content = _read_file(resolved)
        if not content.strip():
            raise ToolError(f"file appears empty or unreadable: {resolved}")

        truncated = False
        if len(content) > _MAX_RAW_CHARS:
            content = content[:_MAX_RAW_CHARS]
            truncated = True

        client = get_openai_client()
        from app.config import get_settings

        settings = get_settings()
        prompt = _build_prompt(resolved, content, instructions, max_words, truncated)
        response = await client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise summarizer. Produce concise, faithful "
                        "summaries grounded only in the provided document."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        summary = (response.choices[0].message.content or "").strip()
        return {
            "path": str(resolved),
            "summary": summary,
            "characters_analyzed": len(content),
            "truncated": truncated,
        }


def _build_prompt(
    path: Path,
    content: str,
    instructions: str | None,
    max_words: int,
    truncated: bool,
) -> str:
    extra = f"\n\nAdditional instructions: {instructions}" if instructions else ""
    notice = (
        "\n\n(Note: the document was truncated to fit the context window.)" if truncated else ""
    )
    return (
        f"Summarize the document below in at most {max_words} words. "
        "Capture the main thesis, key findings, and any concrete action items.\n"
        f"Filename: {path.name}{extra}{notice}\n\n---\n{content}\n---"
    )


def _read_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix == ".docx":
        return _read_docx(path)
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ToolError(f"failed to read {path}: {exc}") from exc


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise ToolError("pypdf is not installed") from exc

    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise ToolError(f"failed to open PDF: {exc}") from exc

    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(pages)


def _read_docx(path: Path) -> str:
    try:
        from docx import Document
    except ImportError as exc:  # pragma: no cover
        raise ToolError("python-docx is not installed") from exc

    try:
        doc = Document(str(path))
    except Exception as exc:
        raise ToolError(f"failed to open DOCX: {exc}") from exc
    return "\n".join(p.text for p in doc.paragraphs)
