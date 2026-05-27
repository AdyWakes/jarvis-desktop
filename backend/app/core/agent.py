"""Conversational agent built on OpenAI tool calling.

The agent owns one conversation turn end-to-end:
  1. Load prior history from the conversation store.
  2. Ask the router for a deterministic match (fast path).
  3. If unmatched, call OpenAI with the tool catalog and execute any tool
     calls the model requests until it returns a final message.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, cast

from openai.types.chat import ChatCompletionMessageFunctionToolCall

from app.config import get_settings
from app.core.memory import ConversationStore
from app.core.registry import ToolRegistry
from app.core.router import CommandRouter
from app.core.schemas import ChatMessage, ChatResponse, ToolCallRecord
from app.logging_config import get_logger
from app.services.openai_client import OpenAINotConfigured, get_openai_client
from app.tools.base import ToolError

log = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are Jarvis, a focused, no-nonsense desktop assistant. "
    "You help the user run their computer: opening applications, browsing "
    "the web, summarizing files, and tracking tasks. "
    "Prefer calling tools over guessing. When you do call a tool, pass "
    "concrete, minimal arguments. After tool calls, give the user a short, "
    "direct natural-language answer. Never invent file paths, URLs, or "
    "command output that you did not actually obtain from a tool."
)

_MAX_TOOL_LOOP = 5


class Agent:
    """End-to-end orchestrator for a single chat turn."""

    def __init__(
        self,
        registry: ToolRegistry,
        router: CommandRouter,
        store: ConversationStore | None = None,
    ) -> None:
        self.registry = registry
        self.router = router
        self.store = store or ConversationStore()

    async def handle(
        self,
        message: str,
        conversation_id: str | None = None,
    ) -> ChatResponse:
        conversation_id = conversation_id or uuid.uuid4().hex
        user_msg = ChatMessage(role="user", content=message)
        await self.store.append(conversation_id, user_msg)

        # Fast deterministic path
        route_result = await self.router.try_handle(message)
        if route_result is not None:
            assistant_msg = ChatMessage(role="assistant", content=route_result.reply)
            await self.store.append(conversation_id, assistant_msg)
            return ChatResponse(
                conversation_id=conversation_id,
                reply=route_result.reply,
                tool_calls=route_result.tool_calls,
            )

        # LLM path with tool calling
        try:
            client = get_openai_client()
        except OpenAINotConfigured as exc:
            reply = (
                f"I can't reach the language model: {exc} "
                "Set OPENAI_API_KEY and restart the server."
            )
            await self.store.append(conversation_id, ChatMessage(role="assistant", content=reply))
            return ChatResponse(conversation_id=conversation_id, reply=reply)

        history = await self.store.history(conversation_id, limit=40)
        openai_messages: list[dict[str, Any]] = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            *(_message_to_openai(m) for m in history),
        ]

        settings = get_settings()
        tool_records: list[ToolCallRecord] = []
        final_reply: str | None = None

        for _ in range(_MAX_TOOL_LOOP):
            schemas = self.registry.openai_schemas()
            response = await client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=cast(Any, openai_messages),
                tools=cast(Any, schemas) if schemas else cast(Any, None),
                tool_choice="auto" if schemas else "none",
                temperature=0.3,
            )
            choice = response.choices[0]
            msg = choice.message
            # Only function-style tool calls are supported by the registry.
            calls: list[ChatCompletionMessageFunctionToolCall] = [
                c
                for c in (msg.tool_calls or [])
                if isinstance(c, ChatCompletionMessageFunctionToolCall)
            ]

            assistant_entry: dict[str, Any] = {
                "role": "assistant",
                "content": msg.content or "",
            }
            if calls:
                assistant_entry["tool_calls"] = [
                    {
                        "id": c.id,
                        "type": "function",
                        "function": {
                            "name": c.function.name,
                            "arguments": c.function.arguments,
                        },
                    }
                    for c in calls
                ]
            openai_messages.append(assistant_entry)

            if not calls:
                final_reply = msg.content or ""
                break

            for call in calls:
                tool = self.registry.get(call.function.name)
                record = ToolCallRecord(
                    tool=call.function.name,
                    arguments=_safe_json(call.function.arguments),
                    result=None,
                )
                if tool is None:
                    record.error = f"unknown tool: {call.function.name}"
                else:
                    try:
                        record.result = await tool.safe_run(record.arguments)
                    except ToolError as exc:
                        record.error = str(exc)
                    except Exception as exc:
                        log.exception("tool.exception", tool=tool.name)
                        record.error = f"unexpected error: {exc}"
                record.finished_at = datetime.utcnow()
                tool_records.append(record)

                openai_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.function.name,
                        "content": _serialize_tool_result(record),
                    }
                )

        if final_reply is None:
            final_reply = (
                "I tried several steps but couldn't reach a final answer. "
                "Please rephrase or narrow the request."
            )

        await self.store.append(conversation_id, ChatMessage(role="assistant", content=final_reply))
        return ChatResponse(
            conversation_id=conversation_id,
            reply=final_reply,
            tool_calls=tool_records,
        )


def _message_to_openai(m: ChatMessage) -> dict[str, Any]:
    base: dict[str, Any] = {"role": m.role, "content": m.content}
    if m.name:
        base["name"] = m.name
    if m.tool_call_id:
        base["tool_call_id"] = m.tool_call_id
    return base


def _safe_json(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}
    return loaded if isinstance(loaded, dict) else {"value": loaded}


def _serialize_tool_result(record: ToolCallRecord) -> str:
    payload: dict[str, Any] = {}
    if record.error:
        payload["error"] = record.error
    else:
        payload["result"] = record.result
    try:
        return json.dumps(payload, default=str)
    except (TypeError, ValueError):
        return json.dumps({"error": "result was not JSON-serializable"})
