"""Pydantic data models shared across the API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    """A single message exchanged with the agent."""

    model_config = ConfigDict(populate_by_name=True)

    role: Role
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ToolCallRecord(BaseModel):
    """Trace of a tool invocation for the UI."""

    tool: str
    arguments: dict[str, Any]
    result: Any
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    error: str | None = None


class ChatRequest(BaseModel):
    """Inbound chat request."""

    message: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Outbound chat response."""

    conversation_id: str
    reply: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class ToolDescriptor(BaseModel):
    """Metadata describing a registered tool."""

    name: str
    description: str
    parameters: dict[str, Any]
    enabled: bool = True
    source: str = "builtin"


class TaskItem(BaseModel):
    """A persisted task in the memory store."""

    id: int
    title: str
    notes: str | None = None
    status: Literal["open", "done"] = "open"
    created_at: datetime
    completed_at: datetime | None = None


class SystemStatus(BaseModel):
    """Health and capability summary used by the dashboard."""

    version: str
    uptime_seconds: float
    cpu_percent: float
    memory_percent: float
    openai_configured: bool
    tools: list[ToolDescriptor]


class TranscriptionResponse(BaseModel):
    """Whisper transcription output."""

    text: str
    duration: float | None = None
    language: str | None = None
