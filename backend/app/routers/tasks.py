"""Direct REST access to the task memory store (used by the dashboard sidebar)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.memory import TaskStore
from app.core.schemas import TaskItem

router = APIRouter(prefix="/tasks", tags=["tasks"])
_store = TaskStore()


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    notes: str | None = Field(default=None, max_length=4000)


@router.get("", response_model=list[TaskItem])
async def list_tasks(status_filter: str | None = None) -> list[TaskItem]:
    return await _store.list(status=status_filter)


@router.post("", response_model=TaskItem, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate) -> TaskItem:
    return await _store.add(title=payload.title, notes=payload.notes)


@router.post("/{task_id}/complete", response_model=TaskItem)
async def complete_task(task_id: int) -> TaskItem:
    task = await _store.complete(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    ok = await _store.delete(task_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
