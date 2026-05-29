"""Inspect and directly invoke tools (useful for debugging and plugin testing)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.core.schemas import ToolDescriptor
from app.tools.base import ToolError

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolInvokeRequest(BaseModel):
    arguments: dict[str, Any] = {}


@router.get("", response_model=list[ToolDescriptor])
async def list_tools(request: Request) -> list[ToolDescriptor]:
    return request.app.state.registry.describe()


@router.post("/{tool_name}/run")
async def run_tool(
    tool_name: str,
    payload: ToolInvokeRequest,
    request: Request,
) -> dict[str, Any]:
    tool = request.app.state.registry.get(tool_name)
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unknown tool: {tool_name}",
        )
    try:
        result = await tool.safe_run(payload.arguments)
    except ToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"tool": tool_name, "result": result}
