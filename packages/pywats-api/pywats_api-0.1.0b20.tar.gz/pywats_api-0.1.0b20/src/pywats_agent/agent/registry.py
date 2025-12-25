from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Type

from .tooling import AgentTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Type[AgentTool]] = {}

    def register(self, tool_cls: Type[AgentTool]) -> None:
        name = getattr(tool_cls, "name", None)
        if not name:
            raise ValueError("Tool class must define 'name'")
        if name in self._tools:
            raise ValueError(f"Tool '{name}' already registered")
        self._tools[name] = tool_cls

    def register_many(self, tool_classes: Iterable[Type[AgentTool]]) -> None:
        for cls in tool_classes:
            self.register(cls)

    def get(self, name: str) -> Type[AgentTool]:
        return self._tools[name]

    def list_names(self) -> list[str]:
        return sorted(self._tools.keys())

    def definitions(self, *, enabled_tools: Iterable[str] | None = None) -> list[dict[str, Any]]:
        if enabled_tools is None:
            names = self.list_names()
        else:
            names = list(enabled_tools)
        return [self._tools[name].openai_definition() for name in names]


@dataclass(frozen=True)
class ToolProfile:
    name: str
    enabled_tools: tuple[str, ...]
