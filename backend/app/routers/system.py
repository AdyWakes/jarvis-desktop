"""Health and status endpoints used by the dashboard's status panel."""

from __future__ import annotations

import time

import psutil
from fastapi import APIRouter, Request

from app import __version__
from app.core.schemas import SystemStatus
from app.services.openai_client import openai_is_configured

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/status", response_model=SystemStatus)
async def status(request: Request) -> SystemStatus:
    started_at: float = request.app.state.started_at
    return SystemStatus(
        version=__version__,
        uptime_seconds=round(time.monotonic() - started_at, 2),
        cpu_percent=psutil.cpu_percent(interval=0.1),
        memory_percent=psutil.virtual_memory().percent,
        openai_configured=openai_is_configured(),
        tools=request.app.state.registry.describe(),
    )
