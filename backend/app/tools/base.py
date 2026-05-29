"""Base classes for tools that can be invoked by the agent."""

from __future__ import annotations

import abc
import inspect
from typing import Any

from pydantic import BaseModel


class ToolError(RuntimeError):
    """Raised by tools to signal a recoverable failure to the agent."""


class Tool(abc.ABC):
    """Abstract base class for an agent-callable tool.

    Subclasses declare a JSON schema describing their arguments and implement
    `run`. The OpenAI tool-calling format is generated from `to_openai_schema`.
    """

    name: str
    description: str
    parameters_model: type[BaseModel]
    source: str = "builtin"

    @abc.abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Execute the tool. Must be overridden."""

    def to_openai_schema(self) -> dict[str, Any]:
        schema = self.parameters_model.model_json_schema()
        schema.pop("title", None)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }

    async def safe_run(self, arguments: dict[str, Any]) -> Any:
        try:
            parsed = self.parameters_model(**arguments)
        except Exception as exc:
            raise ToolError(f"invalid arguments for {self.name}: {exc}") from exc

        result = self.run(**parsed.model_dump())
        if inspect.isawaitable(result):
            return await result
        return result
