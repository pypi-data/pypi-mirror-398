from __future__ import annotations

from contextlib import AsyncExitStack
from typing import Any
from typing import Optional

from mcp import ClientSession
from mcp.client.sse import sse_client

from amsdal_ml.mcp_client.base import ToolClient
from amsdal_ml.mcp_client.base import ToolInfo


class HttpClient(ToolClient):
    def __init__(self, *, alias: str, url: str, headers: Optional[dict[str, str]] = None):
        self.alias = alias
        self.url = url
        self.headers = headers or {}

    async def _session(self):
        stack = AsyncExitStack()
        rx, tx = await stack.enter_async_context(sse_client(self.url, headers=self.headers))
        s = await stack.enter_async_context(ClientSession(rx, tx))
        await s.initialize()
        return stack, s

    async def list_tools(self) -> list[ToolInfo]:
        stack, s = await self._session()
        try:
            resp = await s.list_tools()
            out: list[ToolInfo] = []
            for t in resp.tools:
                out.append(
                    ToolInfo(
                        alias=self.alias,
                        name=t.name,
                        description=t.description or '',
                        input_schema=(getattr(t, 'inputSchema', None) or {}),
                    )
                )
            return out
        finally:
            await stack.aclose()

    async def call(
        self,
        tool_name: str,
        args: dict[str, Any],
        *,
        timeout: float | None = None,
    ) -> Any:
        _ = timeout  # ARG002
        stack, s = await self._session()
        try:
            res = await s.call_tool(tool_name, args)
            return getattr(res, 'content', res)
        finally:
            await stack.aclose()
