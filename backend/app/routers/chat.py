"""Chat endpoints: REST + WebSocket."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.agent import Agent
from app.core.schemas import ChatRequest, ChatResponse
from app.logging_config import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def get_agent() -> Agent:
    # Resolved by an app-level dependency override; raises if no override is set.
    raise RuntimeError("agent dependency is not configured; create_app() must override get_agent")


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    agent: Agent = Depends(get_agent),
) -> ChatResponse:
    return await agent.handle(payload.message, payload.conversation_id)


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket) -> None:
    """Streaming chat over WebSocket.

    Messages from the client are JSON: `{"message": "...", "conversation_id": "..."}`.
    Server pushes JSON events: `{"type": "tool_call" | "reply" | "error", ...}`.
    """
    agent: Agent = websocket.app.state.agent
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "error": "invalid JSON"})
                continue

            message = payload.get("message")
            conversation_id = payload.get("conversation_id")
            if not isinstance(message, str) or not message.strip():
                await websocket.send_json({"type": "error", "error": "missing or empty 'message'"})
                continue

            try:
                response = await agent.handle(message, conversation_id)
            except Exception as exc:
                log.exception("ws.agent_error")
                await websocket.send_json({"type": "error", "error": str(exc)})
                continue

            for record in response.tool_calls:
                await websocket.send_json(
                    {
                        "type": "tool_call",
                        "tool": record.tool,
                        "arguments": record.arguments,
                        "result": record.result,
                        "error": record.error,
                    }
                )
            await websocket.send_json(
                {
                    "type": "reply",
                    "conversation_id": response.conversation_id,
                    "reply": response.reply,
                }
            )
    except WebSocketDisconnect:
        log.info("ws.disconnect")
