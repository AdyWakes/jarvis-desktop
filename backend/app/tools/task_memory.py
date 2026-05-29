"""Tools that read and write the persistent task list."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.core.memory import TaskStore
from app.tools.base import Tool, ToolError

_store = TaskStore()


class AddTaskArgs(BaseModel):
    title: str = Field(min_length=1, max_length=256, description="Short task title.")
    notes: str | None = Field(
        default=None,
        max_length=4000,
        description="Optional longer description or context.",
    )


class ListTasksArgs(BaseModel):
    status: str | None = Field(
        default=None,
        description="Filter: 'open', 'done', or omit for all tasks.",
    )


class CompleteTaskArgs(BaseModel):
    task_id: int = Field(ge=1, description="ID of the task to mark complete.")


class DeleteTaskArgs(BaseModel):
    task_id: int = Field(ge=1, description="ID of the task to delete.")


class AddTaskTool(Tool):
    name = "add_task"
    description = "Add a new task to the user's persistent to-do list."
    parameters_model = AddTaskArgs

    async def run(self, title: str, notes: str | None) -> dict[str, Any]:
        task = await _store.add(title=title, notes=notes)
        return task.model_dump(mode="json")


class ListTasksTool(Tool):
    name = "list_tasks"
    description = "List tasks from the persistent to-do list. Optional status filter."
    parameters_model = ListTasksArgs

    async def run(self, status: str | None) -> dict[str, Any]:
        if status and status not in {"open", "done"}:
            raise ToolError("status must be 'open' or 'done'")
        tasks = await _store.list(status=status)
        return {
            "count": len(tasks),
            "tasks": [t.model_dump(mode="json") for t in tasks],
        }


class CompleteTaskTool(Tool):
    name = "complete_task"
    description = "Mark a task as done by its numeric ID."
    parameters_model = CompleteTaskArgs

    async def run(self, task_id: int) -> dict[str, Any]:
        task = await _store.complete(task_id)
        if task is None:
            raise ToolError(f"no task with id {task_id}")
        return task.model_dump(mode="json")


class DeleteTaskTool(Tool):
    name = "delete_task"
    description = "Permanently delete a task by its numeric ID."
    parameters_model = DeleteTaskArgs

    async def run(self, task_id: int) -> dict[str, Any]:
        ok = await _store.delete(task_id)
        if not ok:
            raise ToolError(f"no task with id {task_id}")
        return {"deleted": task_id}
