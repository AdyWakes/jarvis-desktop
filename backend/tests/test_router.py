from __future__ import annotations

import pytest

from app.config import Settings
from app.core.memory import init_db
from app.core.registry import build_default_registry
from app.core.router import CommandRouter


@pytest.fixture
async def router() -> CommandRouter:
    await init_db()
    settings = Settings(OPENAI_API_KEY="sk-test")  # type: ignore[call-arg]
    return CommandRouter(build_default_registry(settings))


async def test_add_and_list_tasks_via_router(router: CommandRouter) -> None:
    add = await router.try_handle("remind me to buy milk")
    assert add is not None
    assert "Added task" in add.reply

    listing = await router.try_handle("list my tasks")
    assert listing is not None
    assert "buy milk" in listing.reply.lower()


async def test_unmatched_returns_none(router: CommandRouter) -> None:
    assert await router.try_handle("what's the meaning of life?") is None


async def test_system_info_route(router: CommandRouter) -> None:
    result = await router.try_handle("system status")
    assert result is not None
    assert "CPU" in result.reply
