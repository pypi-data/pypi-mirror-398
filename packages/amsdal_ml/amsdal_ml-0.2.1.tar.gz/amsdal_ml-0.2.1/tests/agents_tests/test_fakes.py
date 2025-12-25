from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from collections.abc import Iterator
from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from amsdal_ml.fileio.base_loader import FileAttachment
from amsdal_ml.mcp_client.base import ToolClient
from amsdal_ml.mcp_client.base import ToolInfo
from amsdal_ml.ml_models.models import LLModelInput
from amsdal_ml.ml_models.models import MLModel
from amsdal_ml.ml_models.utils import ResponseFormat

# ---- Fake LLM model ----


def _chunk_cycle(text: str) -> list[str]:
    sizes = [3, 4, 5]
    res: list[str] = []
    pos, i, n = 0, 0, len(text)
    while pos < n:
        sz = sizes[i % len(sizes)]
        res.append(text[pos : pos + sz])
        pos += sz
        i += 1
    return res


class FakeModel(MLModel):
    def __init__(self, *, async_mode: bool, scripted: list[str] | None = None, responses: dict[str, str] | None = None):
        self.async_mode = async_mode
        self._scripted = list(scripted) if scripted else []
        self._responses = responses or {}

    @property
    def supported_formats(self) -> set[ResponseFormat]:
        return {ResponseFormat.JSON_OBJECT, ResponseFormat.JSON_SCHEMA, ResponseFormat.PLAIN_TEXT}

    @property
    def input_role(self) -> str:
        return "user"

    @property
    def output_role(self) -> str:
        return "assistant"

    @property
    def tool_role(self) -> str:
        return "tool"

    @property
    def system_role(self) -> str:
        return "system"

    @property
    def content_field(self) -> str:
        return "content"

    @property
    def role_field(self) -> str:
        return "role"

    @property
    def tool_call_id_field(self) -> str:
        return "tool_call_id"

    @property
    def tool_name_field(self) -> str:
        return "name"

    def setup(self) -> None:  # pragma: no cover
        ...

    def teardown(self) -> None:  # pragma: no cover
        ...

    def _get_response(self, prompt: str) -> str:
        for key, response in self._responses.items():
            if key in prompt:
                return response
        if self._scripted:
            return self._scripted.pop(0)
        return '{"filters": []}'

    def invoke(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        attachments: Optional[list[FileAttachment]] = None,
        response_format: Optional[ResponseFormat] = None,
        schema: Optional[dict[str, Any]] = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> str:
        _ = attachments, response_format, schema, tools, tool_choice  # silence unused
        if self.async_mode:
            msg = "async_mode=True, use ainvoke()"
            raise RuntimeError(msg)
        if isinstance(input, str):
            messages = [{"role": "user", "content": input}]
        else:
            messages = list(input)  # type: ignore[arg-type]
        prompt = messages[-1][self.content_field] if messages else ""
        return self._get_response(prompt)

    async def ainvoke(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        attachments: Optional[list[FileAttachment]] = None,
        response_format: Optional[ResponseFormat] = None,
        schema: Optional[dict[str, Any]] = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> str:
        _ = attachments, response_format, schema, tools, tool_choice  # silence unused
        if not self.async_mode:
            msg = "async_mode=False, use invoke()"
            raise RuntimeError(msg)
        await asyncio.sleep(0)
        if isinstance(input, str):
            messages = [{"role": "user", "content": input}]
        else:
            messages = list(input)  # type: ignore[arg-type]
        prompt = messages[-1][self.content_field] if messages else ""
        return self._get_response(prompt)

    def stream(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        attachments: Optional[list[FileAttachment]] = None,
        response_format: Optional[ResponseFormat] = None,
        schema: Optional[dict[str, Any]] = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> Iterator[str]:
        _ = attachments, response_format, schema, tools, tool_choice
        if self.async_mode:
            msg = "async_mode=True, use astream()"
            raise RuntimeError(msg)
        if not self._scripted and not self._responses:
            return
        text = self.invoke(input)
        yield from _chunk_cycle(text)

    async def astream(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        attachments: Optional[list[FileAttachment]] = None,
        response_format: Optional[ResponseFormat] = None,
        schema: Optional[dict[str, Any]] = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        _ = attachments, response_format, schema, tools, tool_choice
        if not self.async_mode:
            msg = "async_mode=False, use stream()"
            raise RuntimeError(msg)

        if not self._scripted and not self._responses:
            return

        text = await self.ainvoke(input)
        for chunk in _chunk_cycle(text):
            await asyncio.sleep(0)
            yield chunk


# ---- Fake tool schema + tool ----
class _FakeRetrieverArgs(BaseModel):
    query: str = Field(
        ..., description="User search query for semantic similarity retrieval"
    )
    k: int = Field(ge=1, default=3)
    include_tags: list[str] = Field(default_factory=list)
    exclude_tags: list[str] = Field(default_factory=list)


class _ToolResult(BaseModel):
    name: str
    content: Any
    meta: dict[str, Any] = {}


class FakeRetrieverTool:
    """
    Duck-typed MCP tool:
      - name
      - function_spec()
      - call()/acall() -> obj from .content
    """

    name = "retriever.search"
    description = "Search by semantic similarity"
    args_schema = _FakeRetrieverArgs

    def __init__(self):
        self.calls: list[dict[str, Any]] = []

    def function_spec(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema.model_json_schema(),
            "return_direct": False,
        }

    def call(self, **kwargs: Any) -> _ToolResult:
        args = self.args_schema.model_validate(kwargs).model_dump()
        self.calls.append(args.copy())
        return _ToolResult(
            name=self.name, content=[{"text": "chunk-A"}], meta={"k": args.get("k")}
        )

    async def acall(self, **kwargs: Any) -> _ToolResult:
        return self.call(**kwargs)


class FakeToolClient(ToolClient):
    def __init__(self, tool: FakeRetrieverTool | None = None, alias: str = "retriever"):
        self._tool = tool or FakeRetrieverTool()
        self.alias: str = alias  # writeable attribute to match base

    async def list_tools(self) -> list[ToolInfo]:
        return [
            ToolInfo(
                alias=self.alias,
                name="search",
                description=self._tool.description,
                input_schema=self._tool.function_spec().get("parameters", {}),
            )
        ]

    async def call(
        self, _tool_name: str, args: dict[str, Any], *, timeout: float | None = None
    ):
        _unused_timeout = timeout
        return await self._tool.acall(**args)


# ---- Helpers for ReAct markup ----
def tool_call(action: str, arg_json: str = '{"query":"q"}') -> str:
    return f"Thought: Do I need to use a tool? Yes\nAction: {action}\nAction Input: {arg_json}\n"


def final_answer(text: str) -> str:
    return f"Thought: Do I need to use a tool? No\nFinal Answer: {text}\n"


def functional_tool_call(action: str, arg_json: str = '{"query":"q"}', call_id: str = "call_123") -> str:
    return json.dumps({
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": action,
                    "arguments": arg_json
                }
            }
        ]
    })
