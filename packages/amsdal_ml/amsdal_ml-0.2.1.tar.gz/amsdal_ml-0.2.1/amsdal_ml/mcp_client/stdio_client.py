from __future__ import annotations

import asyncio
import base64
import logging
import os
from collections.abc import Iterable
from contextlib import AsyncExitStack
from typing import Any

from amsdal_utils.config.manager import AmsdalConfigManager
from mcp import ClientSession
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError

from amsdal_ml.mcp_client.base import ToolClient
from amsdal_ml.mcp_client.base import ToolInfo

logger = logging.getLogger(__name__)


class StdioClient(ToolClient):
    """
    MCP over STDIO client.
    """

    def __init__(
        self,
        alias: str,
        module_or_cmd: str,
        *args: str,
        persist_session: bool = True,
        send_amsdal_config: bool = True,
    ):
        self.alias = alias
        if module_or_cmd in ('python', 'python3'):
            self._command = module_or_cmd
            self._args = list(args)
        else:
            self._command = 'python'
            self._args = ['-m', module_or_cmd]
        if send_amsdal_config:
            self._args.append('--amsdal-config')
            self._args.append(self._build_amsdal_config_arg())
        self._persist = persist_session
        self._lock = asyncio.Lock()
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None
        self._tool_cache: list[ToolInfo] | None = None

    async def _open_session(self) -> tuple[AsyncExitStack, ClientSession]:
        stack = AsyncExitStack()
        params = StdioServerParameters(command=self._command, args=self._args, env=os.environ.copy())
        rx, tx = await stack.enter_async_context(stdio_client(params))
        s = await stack.enter_async_context(ClientSession(rx, tx))
        await s.initialize()
        return stack, s

    async def _ensure_session(self) -> ClientSession:
        if not self._persist:
            # One-off session (opened and immediately closed by caller)
            stack, s = await self._open_session()
            await stack.aclose()
            return s

        async with self._lock:
            if self._session is not None and self._stack is not None:
                return self._session
            self._stack, self._session = await self._open_session()
            return self._session

    async def _reset_session(self) -> None:
        async with self._lock:
            try:
                if self._stack is not None:
                    await self._stack.aclose()
            finally:
                self._stack = None
                self._session = None

    @staticmethod
    def _convert_tools(alias: str, resp_tools: Iterable[Any]) -> list[ToolInfo]:
        return [
            ToolInfo(
                alias=alias,
                name=t.name,
                description=(getattr(t, 'description', None) or ''),
                input_schema=(getattr(t, 'inputSchema', None) or {}),
            )
            for t in resp_tools
        ]

    async def list_tools(self) -> list[ToolInfo]:
        if self._tool_cache is not None:
            return self._tool_cache

        if not self._persist:
            async with AsyncExitStack() as stack:
                params = StdioServerParameters(command=self._command, args=self._args, env=os.environ.copy())
                rx, tx = await stack.enter_async_context(stdio_client(params))
                s = await stack.enter_async_context(ClientSession(rx, tx))
                await s.initialize()
                resp = await s.list_tools()
                tools_list = self._convert_tools(self.alias, resp.tools)
                self._tool_cache = tools_list
                return tools_list

        # Persistent session path
        s = await self._ensure_session()
        try:
            resp = await s.list_tools()
        except McpError:
            await self._reset_session()
            s = await self._ensure_session()
            resp = await s.list_tools()

        tools_list = self._convert_tools(self.alias, resp.tools)
        self._tool_cache = tools_list
        return tools_list

    @staticmethod
    async def _call_with_timeout(coro, *, timeout: float | None):
        return await (asyncio.wait_for(coro, timeout=timeout) if timeout else coro)

    async def call(self, tool_name: str, args: dict[str, Any], *, timeout: float | None = None) -> Any:
        if not self._persist:
            async with AsyncExitStack() as stack:
                params = StdioServerParameters(command=self._command, args=self._args, env=os.environ.copy())
                rx, tx = await stack.enter_async_context(stdio_client(params))
                s = await stack.enter_async_context(ClientSession(rx, tx))
                await s.initialize()
                logger.debug("Calling tool: %s with args: %s", tool_name, args)
                res = await self._call_with_timeout(s.call_tool(tool_name, args), timeout=timeout)
                return getattr(res, 'content', res)

        # Persistent session path
        s = await self._ensure_session()
        try:
            res = await self._call_with_timeout(s.call_tool(tool_name, args), timeout=timeout)
            return getattr(res, 'content', res)
        except (TimeoutError, McpError):
            await self._reset_session()
            s = await self._ensure_session()
            res = await self._call_with_timeout(s.call_tool(tool_name, args), timeout=timeout)
            return getattr(res, 'content', res)

    def _build_amsdal_config_arg(self) -> str:
        """
        Build a JSON string argument representing the current Amsdal configuration.
        This can be passed to the subprocess to ensure it has the same configuration context.
        """
        config = AmsdalConfigManager().get_config()
        return base64.b64encode(config.model_dump_json().encode('utf-8')).decode('utf-8')
