from __future__ import annotations

from app.core.memory import TaskStore, init_db


async def test_task_lifecycle() -> None:
    await init_db()
    store = TaskStore()

    created = await store.add(title="write docs", notes="cover plugin system")
    assert created.id > 0
    assert created.status == "open"

    listed = await store.list()
    assert any(t.id == created.id for t in listed)

    done = await store.complete(created.id)
    assert done is not None
    assert done.status == "done"
    assert done.completed_at is not None

    assert await store.delete(created.id) is True
    assert await store.delete(created.id) is False
