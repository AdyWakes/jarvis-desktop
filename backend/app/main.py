"""FastAPI application entrypoint."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.core.agent import Agent
from app.core.memory import ConversationStore, init_db
from app.core.registry import build_default_registry
from app.core.router import CommandRouter
from app.logging_config import configure_logging, get_logger
from app.routers import chat as chat_router
from app.routers import stt as stt_router
from app.routers import system as system_router
from app.routers import tasks as tasks_router
from app.routers import tools as tools_router

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()

    await init_db()
    registry = build_default_registry(settings)
    command_router = CommandRouter(registry)
    agent = Agent(registry=registry, router=command_router, store=ConversationStore())

    app.state.settings = settings
    app.state.registry = registry
    app.state.command_router = command_router
    app.state.agent = agent
    app.state.started_at = time.monotonic()

    log.info(
        "app.startup",
        version=__version__,
        tools=[t.name for t in registry.all()],
        openai_configured=bool(settings.openai_api_key),
    )

    yield

    log.info("app.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Jarvis Desktop Assistant",
        version=__version__,
        description=(
            "Backend for a Jarvis-style desktop assistant. Exposes chat, "
            "speech-to-text, task memory, and direct tool invocation."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _agent_dependency() -> Agent:
        return app.state.agent

    app.dependency_overrides[chat_router.get_agent] = _agent_dependency

    app.include_router(system_router.router)
    app.include_router(chat_router.router)
    app.include_router(stt_router.router)
    app.include_router(tasks_router.router)
    app.include_router(tools_router.router)

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {
            "name": "jarvis-desktop",
            "version": __version__,
            "docs": "/docs",
        }

    return app


app = create_app()
