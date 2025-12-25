from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Protocol
from typing import runtime_checkable


@dataclass
class ToolInfo:
    alias: str
    name: str
    description: str
    input_schema: dict[str, Any]


@runtime_checkable
class ToolClient(Protocol):
    alias: str

    async def list_tools(self) -> list[ToolInfo]: ...
    async def call(self, tool_name: str, args: dict[str, Any], *, timeout: float | None = None) -> Any: ...
