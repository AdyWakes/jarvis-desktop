"""Tool registry and plugin discovery."""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import pkgutil
from collections.abc import Iterable
from pathlib import Path

from app.config import Settings, get_settings
from app.core.schemas import ToolDescriptor
from app.logging_config import get_logger
from app.tools import (
    AddTaskTool,
    AppLauncherTool,
    BrowserTool,
    CompleteTaskTool,
    DeleteTaskTool,
    FileSummarizerTool,
    ListTasksTool,
    SystemInfoTool,
)
from app.tools.base import Tool

log = get_logger(__name__)


class ToolRegistry:
    """In-memory map of name -> Tool."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            log.warning("tool.duplicate", name=tool.name)
            return
        self._tools[tool.name] = tool
        log.info("tool.registered", name=tool.name, source=tool.source)

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def describe(self) -> list[ToolDescriptor]:
        return [
            ToolDescriptor(
                name=t.name,
                description=t.description,
                parameters=t.parameters_model.model_json_schema(),
                enabled=True,
                source=t.source,
            )
            for t in self._tools.values()
        ]

    def openai_schemas(self) -> list[dict]:
        return [t.to_openai_schema() for t in self._tools.values()]


def build_default_registry(settings: Settings | None = None) -> ToolRegistry:
    settings = settings or get_settings()
    registry = ToolRegistry()

    if settings.enable_app_launcher:
        registry.register(AppLauncherTool())
    if settings.enable_browser:
        registry.register(BrowserTool())
    if settings.enable_file_summarizer:
        registry.register(FileSummarizerTool())
    if settings.enable_task_memory:
        registry.register(AddTaskTool())
        registry.register(ListTasksTool())
        registry.register(CompleteTaskTool())
        registry.register(DeleteTaskTool())

    registry.register(SystemInfoTool())

    for tool in _discover_plugins(settings.plugin_dir):
        tool.source = "plugin"
        registry.register(tool)

    return registry


def _discover_plugins(plugin_dir: str) -> Iterable[Tool]:
    """Load plugins from `plugin_dir`.

    A plugin is a Python module that exposes either:
      * a top-level `TOOLS` iterable of Tool instances, or
      * one or more `Tool` subclasses (instantiated with no args)
    """
    base = Path(plugin_dir)
    if not base.exists():
        return []

    discovered: list[Tool] = []

    # Try package-style import first (works when plugin_dir is inside app/)
    package_name = ".".join(base.parts[-2:]) if base.parts[-2] == "app" else None
    if package_name:
        try:
            pkg = importlib.import_module(package_name)
            for mod_info in pkgutil.iter_modules(pkg.__path__):
                if mod_info.name.startswith("_"):
                    continue
                module = importlib.import_module(f"{package_name}.{mod_info.name}")
                discovered.extend(_collect_from_module(module))
        except ModuleNotFoundError:
            pass

    # Filesystem-style fallback for arbitrary directories
    for path in base.glob("*.py"):
        if path.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(f"jarvis_plugin_{path.stem}", path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            log.warning("plugin.load_failed", path=str(path), error=str(exc))
            continue
        discovered.extend(_collect_from_module(module))

    # Deduplicate by tool name (package-style first wins)
    by_name: dict[str, Tool] = {}
    for tool in discovered:
        by_name.setdefault(tool.name, tool)
    return by_name.values()


def _collect_from_module(module: object) -> list[Tool]:
    found: list[Tool] = []
    explicit = getattr(module, "TOOLS", None)
    if explicit:
        for item in explicit:
            if isinstance(item, Tool):
                found.append(item)
        return found

    for _, obj in inspect.getmembers(module, inspect.isclass):
        if obj is Tool:
            continue
        if not issubclass(obj, Tool):
            continue
        if inspect.isabstract(obj):
            continue
        if obj.__module__ != getattr(module, "__name__", None):
            continue
        try:
            found.append(obj())
        except Exception as exc:
            log.warning("plugin.instantiate_failed", cls=obj.__name__, error=str(exc))
    return found
