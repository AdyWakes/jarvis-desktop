"""Cross-platform application launcher tool."""

from __future__ import annotations

import asyncio
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.tools.base import Tool, ToolError

# Common, safe aliases. Users can extend this via a plugin.
_ALIASES: dict[str, dict[str, list[str]]] = {
    "Darwin": {
        "browser": ["open", "-a", "Safari"],
        "chrome": ["open", "-a", "Google Chrome"],
        "firefox": ["open", "-a", "Firefox"],
        "terminal": ["open", "-a", "Terminal"],
        "finder": ["open", "-a", "Finder"],
        "vscode": ["open", "-a", "Visual Studio Code"],
        "calculator": ["open", "-a", "Calculator"],
        "notes": ["open", "-a", "Notes"],
    },
    "Linux": {
        "browser": ["xdg-open", "https://"],
        "chrome": ["google-chrome"],
        "firefox": ["firefox"],
        "terminal": ["x-terminal-emulator"],
        "files": ["xdg-open", str(Path.home())],
        "vscode": ["code"],
        "calculator": ["gnome-calculator"],
    },
    "Windows": {
        "browser": ["cmd", "/c", "start", "", "https://"],
        "chrome": ["cmd", "/c", "start", "", "chrome"],
        "firefox": ["cmd", "/c", "start", "", "firefox"],
        "terminal": ["cmd", "/c", "start", "", "wt.exe"],
        "explorer": ["explorer.exe"],
        "vscode": ["cmd", "/c", "start", "", "code"],
        "calculator": ["cmd", "/c", "start", "", "calc.exe"],
        "notepad": ["notepad.exe"],
    },
}


class AppLauncherArgs(BaseModel):
    name: str = Field(
        description=(
            "Friendly name of the application to open. Examples: 'chrome', "
            "'firefox', 'terminal', 'vscode', 'calculator', or a path to an "
            "executable / file the OS can open."
        )
    )
    arguments: list[str] = Field(
        default_factory=list,
        description="Extra arguments to pass to the application.",
    )


class AppLauncherTool(Tool):
    """Launch desktop applications on the host machine."""

    name = "open_application"
    description = (
        "Open a desktop application by friendly name (e.g. 'chrome', 'terminal') "
        "or by absolute path. Returns the PID on success."
    )
    parameters_model = AppLauncherArgs

    async def run(self, name: str, arguments: list[str]) -> dict[str, Any]:
        system = platform.system()
        cmd = self._resolve(system, name, arguments)
        if cmd is None:
            raise ToolError(
                f"could not resolve application '{name}' on {system}. "
                "Try an absolute path or a known alias."
            )

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                start_new_session=True,
            )
        except FileNotFoundError as exc:
            raise ToolError(f"executable not found: {cmd[0]}") from exc
        except OSError as exc:
            raise ToolError(f"failed to launch '{name}': {exc}") from exc

        return {"launched": " ".join(cmd), "pid": proc.pid, "platform": system}

    def _resolve(self, system: str, name: str, arguments: list[str]) -> list[str] | None:
        # Absolute path or existing file
        candidate = Path(name).expanduser()
        if candidate.exists():
            return self._open_path(system, candidate, arguments)

        alias_table = _ALIASES.get(system, {})
        alias = alias_table.get(name.lower())
        if alias:
            return [*alias, *arguments]

        # Fallback: trust that the binary is on PATH
        if shutil.which(name):
            return [name, *arguments]

        return None

    @staticmethod
    def _open_path(system: str, path: Path, arguments: list[str]) -> list[str]:
        if system == "Darwin":
            return ["open", str(path), *arguments]
        if system == "Windows":
            return ["cmd", "/c", "start", "", str(path), *arguments]
        # Linux & others
        opener = shutil.which("xdg-open") or "xdg-open"
        # If it's an executable, run it directly
        if os.access(path, os.X_OK) and path.is_file():
            return [str(path), *arguments]
        return [opener, str(path), *arguments]


def _platform_module() -> str:  # pragma: no cover - utility
    return sys.platform
