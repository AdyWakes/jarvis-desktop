from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from app.main import create_app


async def test_health_and_status() -> None:
    app = create_app()
    async with (
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
        _lifespan(app),
    ):
        health = await client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}

        status = await client.get("/status")
        assert status.status_code == 200
        body = status.json()
        assert body["version"]
        assert "tools" in body
        assert isinstance(body["tools"], list)


async def test_tools_listing() -> None:
    app = create_app()
    async with (
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
        _lifespan(app),
    ):
        resp = await client.get("/tools")
        assert resp.status_code == 200
        names = {t["name"] for t in resp.json()}
        assert "system_info" in names


class _lifespan:
    def __init__(self, app) -> None:
        self.app = app
        self._cm = None

    async def __aenter__(self):
        from contextlib import AsyncExitStack

        self._stack = AsyncExitStack()
        await self._stack.__aenter__()
        # Manually run the lifespan context attached to the app
        self._cm = self.app.router.lifespan_context(self.app)
        await self._cm.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._cm.__aexit__(exc_type, exc, tb)
        await self._stack.__aexit__(exc_type, exc, tb)
