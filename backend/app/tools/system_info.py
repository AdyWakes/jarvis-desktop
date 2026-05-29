"""Expose host system metrics to the agent."""

from __future__ import annotations

import platform
import shutil
from typing import Any

import psutil
from pydantic import BaseModel

from app.tools.base import Tool


class SystemInfoArgs(BaseModel):
    pass


class SystemInfoTool(Tool):
    name = "system_info"
    description = (
        "Return CPU, memory, disk, and OS information about the host machine. "
        "Use when the user asks about system health or resources."
    )
    parameters_model = SystemInfoArgs

    async def run(self) -> dict[str, Any]:
        vm = psutil.virtual_memory()
        disk = shutil.disk_usage("/")
        return {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_percent": psutil.cpu_percent(interval=0.2),
            "cpu_count": psutil.cpu_count(logical=True),
            "memory": {
                "total_mb": round(vm.total / 1024 / 1024, 1),
                "available_mb": round(vm.available / 1024 / 1024, 1),
                "percent": vm.percent,
            },
            "disk": {
                "total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
                "free_gb": round(disk.free / 1024 / 1024 / 1024, 1),
                "percent": round((disk.used / disk.total) * 100, 1),
            },
        }
