"""Command routing layer.

The router gives fast, deterministic responses for common intents without
hitting the LLM. Anything it can't handle falls through to the agent.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.core.registry import ToolRegistry
from app.core.schemas import ToolCallRecord
from app.tools.base import Tool, ToolError

RouteHandler = Callable[[re.Match[str], ToolRegistry], Awaitable["RouteResult"]]


@dataclass
class RouteResult:
    """Result returned by a deterministic route."""

    reply: str
    tool_calls: list[ToolCallRecord]


@dataclass
class Route:
    """A regex-based intent route."""

    name: str
    pattern: re.Pattern[str]
    handler: RouteHandler
    description: str


class CommandRouter:
    """Tries deterministic regex routes before falling back to the LLM."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        self._routes: list[Route] = []
        self._register_defaults()

    def add_route(
        self,
        name: str,
        pattern: str,
        handler: RouteHandler,
        description: str = "",
    ) -> None:
        self._routes.append(
            Route(
                name=name,
                pattern=re.compile(pattern, re.IGNORECASE),
                handler=handler,
                description=description,
            )
        )

    def routes(self) -> list[Route]:
        return list(self._routes)

    async def try_handle(self, message: str) -> RouteResult | None:
        for route in self._routes:
            match = route.pattern.search(message)
            if match:
                return await route.handler(match, self.registry)
        return None

    # --- default routes ----------------------------------------------------

    def _register_defaults(self) -> None:
        self.add_route(
            "open_app",
            r"^(?:open|launch|start)\s+(?:the\s+)?(?P<name>[\w\-./ ]+?)\s*$",
            _route_open_app,
            "Open an application by name.",
        )
        self.add_route(
            "list_tasks",
            r"^(?:show|list|what(?:'s| is))\s+(?:my\s+)?(?:open\s+)?tasks?\??$",
            _route_list_tasks,
            "List open tasks.",
        )
        self.add_route(
            "add_task",
            r"^(?:add|remind me to|create a task to)\s+(?P<title>.+?)\s*$",
            _route_add_task,
            "Add a task to the persistent list.",
        )
        self.add_route(
            "system_info",
            r"^(?:system\s+(?:status|info|health)|how(?:'s| is)\s+my\s+system)\??$",
            _route_system_info,
            "Report system status.",
        )


# --- handlers --------------------------------------------------------------


async def _invoke(tool: Tool, args: dict) -> ToolCallRecord:
    from datetime import datetime

    record = ToolCallRecord(tool=tool.name, arguments=args, result=None)
    try:
        record.result = await tool.safe_run(args)
    except ToolError as exc:
        record.error = str(exc)
    finally:
        record.finished_at = datetime.utcnow()
    return record


async def _route_open_app(match: re.Match[str], registry: ToolRegistry) -> RouteResult:
    tool = registry.get("open_application")
    name = match.group("name").strip()
    if tool is None:
        return RouteResult(
            reply="The application launcher tool is disabled.",
            tool_calls=[],
        )
    call = await _invoke(tool, {"name": name, "arguments": []})
    if call.error:
        return RouteResult(reply=f"Couldn't open {name!r}: {call.error}", tool_calls=[call])
    return RouteResult(reply=f"Opened {name}.", tool_calls=[call])


async def _route_list_tasks(_: re.Match[str], registry: ToolRegistry) -> RouteResult:
    tool = registry.get("list_tasks")
    if tool is None:
        return RouteResult(reply="Task memory is disabled.", tool_calls=[])
    call = await _invoke(tool, {"status": "open"})
    if call.error:
        return RouteResult(reply=f"Couldn't list tasks: {call.error}", tool_calls=[call])
    result = call.result or {}
    tasks = result.get("tasks", [])
    if not tasks:
        return RouteResult(reply="You have no open tasks.", tool_calls=[call])
    lines = [f"#{t['id']} — {t['title']}" for t in tasks]
    return RouteResult(
        reply="Open tasks:\n" + "\n".join(lines),
        tool_calls=[call],
    )


async def _route_add_task(match: re.Match[str], registry: ToolRegistry) -> RouteResult:
    tool = registry.get("add_task")
    title = match.group("title").strip().rstrip(".!?")
    if tool is None:
        return RouteResult(reply="Task memory is disabled.", tool_calls=[])
    call = await _invoke(tool, {"title": title, "notes": None})
    if call.error:
        return RouteResult(reply=f"Couldn't add task: {call.error}", tool_calls=[call])
    task_id = (call.result or {}).get("id")
    return RouteResult(reply=f"Added task #{task_id}: {title}", tool_calls=[call])


async def _route_system_info(_: re.Match[str], registry: ToolRegistry) -> RouteResult:
    tool = registry.get("system_info")
    if tool is None:
        return RouteResult(reply="System info tool is unavailable.", tool_calls=[])
    call = await _invoke(tool, {})
    if call.error or call.result is None:
        return RouteResult(reply="Couldn't gather system info.", tool_calls=[call])
    r = call.result
    reply = (
        f"CPU {r['cpu_percent']}% across {r['cpu_count']} cores. "
        f"Memory {r['memory']['percent']}% used "
        f"({r['memory']['available_mb']} MB free). "
        f"Disk {r['disk']['percent']}% used ({r['disk']['free_gb']} GB free)."
    )
    return RouteResult(reply=reply, tool_calls=[call])
