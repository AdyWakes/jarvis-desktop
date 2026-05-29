"""Persistent storage for conversation history and task memory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import get_settings
from app.core.schemas import ChatMessage, TaskItem


class Base(DeclarativeBase):
    pass


class ConversationRow(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tool_call_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TaskRow(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine():
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.db_url, future=True)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


async def init_db() -> None:
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def session_scope() -> AsyncIterator[AsyncSession]:
    _get_engine()
    assert _session_factory is not None
    async with _session_factory() as session:
        yield session


class ConversationStore:
    """Persists chat history per conversation."""

    async def append(self, conversation_id: str, message: ChatMessage) -> None:
        async for session in session_scope():
            row = ConversationRow(
                conversation_id=conversation_id,
                role=message.role,
                content=message.content,
                name=message.name,
                tool_call_id=message.tool_call_id,
                created_at=message.created_at,
            )
            session.add(row)
            await session.commit()

    async def history(self, conversation_id: str, limit: int = 50) -> list[ChatMessage]:
        async for session in session_scope():
            stmt = (
                select(ConversationRow)
                .where(ConversationRow.conversation_id == conversation_id)
                .order_by(ConversationRow.id.asc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [
                ChatMessage(
                    role=row.role,
                    content=row.content,
                    name=row.name,
                    tool_call_id=row.tool_call_id,
                    created_at=row.created_at,
                )
                for row in rows
            ]
        return []

    async def clear(self, conversation_id: str) -> None:
        async for session in session_scope():
            stmt = select(ConversationRow).where(ConversationRow.conversation_id == conversation_id)
            result = await session.execute(stmt)
            for row in result.scalars().all():
                await session.delete(row)
            await session.commit()


class TaskStore:
    """CRUD for the assistant's task memory."""

    async def add(self, title: str, notes: str | None = None) -> TaskItem:
        async for session in session_scope():
            row = TaskRow(title=title, notes=notes, status="open")
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _to_task(row)
        raise RuntimeError("session_scope yielded no session")

    async def list(self, status: str | None = None) -> list[TaskItem]:
        async for session in session_scope():
            stmt = select(TaskRow).order_by(TaskRow.created_at.desc())
            if status:
                stmt = stmt.where(TaskRow.status == status)
            result = await session.execute(stmt)
            return [_to_task(r) for r in result.scalars().all()]
        return []

    async def complete(self, task_id: int) -> TaskItem | None:
        async for session in session_scope():
            row = await session.get(TaskRow, task_id)
            if row is None:
                return None
            row.status = "done"
            row.completed_at = datetime.utcnow()
            await session.commit()
            await session.refresh(row)
            return _to_task(row)
        return None

    async def delete(self, task_id: int) -> bool:
        async for session in session_scope():
            row = await session.get(TaskRow, task_id)
            if row is None:
                return False
            await session.delete(row)
            await session.commit()
            return True
        return False


def _to_task(row: TaskRow) -> TaskItem:
    return TaskItem(
        id=row.id,
        title=row.title,
        notes=row.notes,
        status=row.status,
        created_at=row.created_at,
        completed_at=row.completed_at,
    )
