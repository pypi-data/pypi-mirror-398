from __future__ import annotations

import inspect
import json
import re
from collections.abc import AsyncIterator
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import no_type_check

from amsdal_ml.agents.agent import Agent
from amsdal_ml.agents.agent import AgentOutput
from amsdal_ml.agents.mcp_client_tool import ClientToolProxy
from amsdal_ml.agents.python_tool import PythonTool
from amsdal_ml.agents.python_tool import _PythonToolProxy
from amsdal_ml.fileio.base_loader import FileAttachment
from amsdal_ml.mcp_client.base import ToolClient
from amsdal_ml.mcp_client.base import ToolInfo
from amsdal_ml.ml_models.models import MLModel
from amsdal_ml.prompts import get_prompt

# ---------- STRICT ReAct REGEX ----------
_TOOL_CALL_RE = re.compile(
    r'Thought:\s*Do I need to use a tool\?\s*Yes[\.\!]?\s*'
    r'Action:\s*(?P<action>[^\n]+)\s*'
    r'Action Input:\s*(?P<input>\{.*\})\s*',
    re.DOTALL | re.IGNORECASE,
)

_FINAL_RE = re.compile(
    r'(?:Thought:\s*Do I need to use a tool\?\s*No[\.\!]?\s*)?'
    r'Final Answer:\s*(?P<answer>.+)',
    re.DOTALL | re.IGNORECASE,
)
# ---------- constants ----------

_MAX_PARSE_RETRIES = 5


# ---------- STRICT ReAct REGEX ----------


@dataclass
class Route:
    name: str
    match: Callable[[str], bool]
    handler: Callable[[str], AgentOutput]


class ParseErrorMode(Enum):
    RAISE = 'raise'
    RETRY = 'retry'


class DefaultQAAgent(Agent):
    def __init__(
        self,
        *,
        model: MLModel,
        tools: list[PythonTool | ToolClient] | None = None,
        max_steps: int = 6,
        on_parse_error: ParseErrorMode = ParseErrorMode.RAISE,
        enable_stop_guard: bool = True,
        per_call_timeout: float | None = 20.0,
    ):
        self._tools: list[PythonTool | ToolClient] = tools or []
        self._indexed_tools: dict[str, ClientToolProxy | _PythonToolProxy] = {}

        self.model = model
        self.model.setup()
        self.max_steps = max_steps
        self.per_call_timeout = per_call_timeout
        self.on_parse_error = on_parse_error
        self.enable_stop_guard = enable_stop_guard

        self._is_tools_index_built = False

    # ---------- tools helpers ----------
    def _get_tool(self, name: str) -> Any:
        """
        Look up tools ONLY among client-indexed tools.
        Expected names are qualified: '<alias>.<tool_name>'.
        """
        if not self._is_tools_index_built:
            msg = 'Tool index not built. Ensure arun()/astream() was used.'
            raise RuntimeError(msg)
        if name in self._indexed_tools:
            return self._indexed_tools[name]
        available = sorted(self._indexed_tool_names())
        msg = f'Unknown tool: {name}. Available: {", ".join(available)}'
        raise KeyError(msg)

    def _indexed_tool_names(self) -> list[str]:
        return list(self._indexed_tools.keys()) if self._is_tools_index_built else []

    def _tool_names(self) -> str:
        return ', '.join(sorted(self._indexed_tool_names()))

    def _tool_descriptions(self) -> str:
        parts: list[str] = []
        if self._is_tools_index_built:
            for qn, t in self._indexed_tools.items():
                desc = t.description or 'No description.'
                try:
                    schema_json = json.dumps(t.parameters or {}, ensure_ascii=False)
                except Exception:
                    schema_json = str(t.parameters)
                parts.append(f'- {qn}: {desc}\n  Args JSON schema: {schema_json}')
        return '\n'.join(parts)

    async def _build_clients_index(self):
        self._indexed_tools.clear()

        for tool in self._tools:
            if isinstance(tool, ToolClient):
                infos: list[ToolInfo] = await tool.list_tools()
                for ti in infos:
                    qname = f'{ti.alias}.{ti.name}'
                    proxy = ClientToolProxy(
                        client=tool,
                        alias=ti.alias,
                        name=ti.name,
                        schema=ti.input_schema or {},
                        description=ti.description or '',
                    )
                    proxy.set_timeout(self.per_call_timeout)
                    self._indexed_tools[qname] = proxy
            elif isinstance(tool, PythonTool):
                if tool.name in self._indexed_tools:
                    msg = f'Tool name conflict: {tool.name} is already defined.'
                    raise ValueError(msg)
                proxy = _PythonToolProxy(tool, timeout=self.per_call_timeout) # type: ignore[assignment]
                self._indexed_tools[tool.name] = proxy
            else:
                msg = f'Unsupported tool type: {type(tool)}'
                raise TypeError(msg)

        self._is_tools_index_built = True

    # ---------- prompt composition ----------
    def _react_text(self, user_query: str, scratchpad: str) -> str:
        tmpl = get_prompt('react_chat')
        return tmpl.render_text(
            user_query=user_query,
            tools=self._tool_descriptions(),
            tool_names=self._tool_names(),
            agent_scratchpad=scratchpad,
            chat_history='',
        )

    @staticmethod
    def _stopped_message() -> str:
        return 'Agent stopped due to iteration limit or time limit.'

    def _stopped_response(self, used_tools: list[str]) -> AgentOutput:
        return AgentOutput(answer=self._stopped_message(), used_tools=used_tools, citations=[])

    @staticmethod
    def _serialize_observation(content: Any) -> str:
        if isinstance(content, str | bytes):
            return content if isinstance(content, str) else content.decode('utf-8', errors='ignore')
        try:
            return json.dumps(content, ensure_ascii=False)
        except Exception:
            return str(content)

    # ---------- core run ----------
    def run(self, user_query: str, *, attachments: list[FileAttachment] | None = None) -> AgentOutput:
        msg = 'DefaultQAAgent is async-only for now. Use arun().'
        raise NotImplementedError(msg)

    async def _run_async(self, user_query: str, *, attachments: list[FileAttachment] | None = None) -> AgentOutput:
        if not self._is_tools_index_built:
            await self._build_clients_index()

        scratch = ''
        used_tools: list[str] = []
        parse_retries = 0

        for _ in range(self.max_steps):
            prompt = self._react_text(user_query, scratch)
            out = await self.model.ainvoke(prompt, attachments=attachments)
            print('Model output:', out)  # noqa: T201
            print('promt:', prompt)  # noqa: T201
            m_final = _FINAL_RE.search(out or '')
            if m_final:
                return AgentOutput(
                    answer=(m_final.group('answer') or '').strip(),
                    used_tools=used_tools,
                    citations=[],
                )

            m_tool = _TOOL_CALL_RE.search(out or '')
            if not m_tool:
                parse_retries += 1
                if self.on_parse_error == ParseErrorMode.RAISE or parse_retries >= _MAX_PARSE_RETRIES:
                    msg = f'Invalid ReAct output. Expected EXACT format (Final or Tool-call). Got:\n{out}'
                    raise ValueError(msg)

                scratch += (
                    '\nThought: Previous output violated the strict format. '
                    'Reply again using EXACTLY one of the two specified formats.\n'
                )
                continue

            action = m_tool.group('action').strip()
            raw_input = m_tool.group('input').strip()

            try:
                args = json.loads(raw_input)
                if not isinstance(args, dict):
                    msg = 'Action Input must be a JSON object.'
                    raise ValueError(msg)
            except Exception as e:
                parse_retries += 1
                if self.on_parse_error == ParseErrorMode.RAISE or parse_retries >= _MAX_PARSE_RETRIES:
                    msg = f'Invalid Action Input JSON: {raw_input!r} ({e})'
                    raise ValueError(msg) from e
                scratch += '\nThought: Action Input must be a ONE-LINE JSON object. Retry with correct JSON.\n'
                continue

            tool = self._get_tool(action)

            try:
                result = await tool.run(args, context=None, convert_result=True)
                print('Similarity search result:', result)  # noqa: T201
            except Exception as e:
                # unified error payload
                err = {
                    'error': {
                        'type': e.__class__.__name__,
                        'server': getattr(tool, 'alias', 'local'),
                        'tool': getattr(tool, 'name', getattr(tool, 'qualified', 'unknown')),
                        'message': str(e),
                        'retryable': False,
                    }
                }
                result = err

            used_tools.append(action)
            observation = self._serialize_observation(result)

            scratch += (
                '\nThought: Do I need to use a tool? Yes'
                f'\nAction: {action}'
                f'\nAction Input: {raw_input}'
                f'\nObservation: {observation}\n'
            )

        return self._stopped_response(used_tools)

    # ---------- public APIs ----------
    async def arun(self, user_query: str, *, attachments: list[FileAttachment] | None = None) -> AgentOutput:
        return await self._run_async(user_query, attachments=attachments)

    # ---------- streaming ----------
    @no_type_check
    async def astream(self, user_query: str, *, attachments: list[FileAttachment] | None = None) -> AsyncIterator[str]:
        if not self._is_tools_index_built:
            await self._build_clients_index()

        scratch = ''
        used_tools: list[str] = []
        parse_retries = 0

        for _ in range(self.max_steps):
            prompt = self._react_text(user_query, scratch)

            buffer = ''

            # Normalize model.astream: it might be an async iterator already,
            # or a coroutine (or nested coroutines) that resolves to one.
            _val = self.model.astream(prompt, attachments=attachments)
            while inspect.iscoroutine(_val):
                _val = await _val

            # Optional guard (helpful during tests)
            if not hasattr(_val, '__aiter__'):
                msg = f'model.astream() did not yield an AsyncIterator; got {type(_val)!r}'
                raise TypeError(msg)

            model_stream = _val  # now an AsyncIterator[str]

            async for chunk in model_stream:
                buffer += chunk

            m_final = _FINAL_RE.search(buffer or '')
            if m_final:
                answer = (m_final.group('answer') or '').strip()
                if answer:
                    yield answer
                return

            m_tool = _TOOL_CALL_RE.search(buffer or '')
            if not m_tool:
                parse_retries += 1
                if self.on_parse_error == ParseErrorMode.RAISE or parse_retries >= _MAX_PARSE_RETRIES:
                    msg = f'Invalid ReAct output (stream). Expected EXACT format. Got:\n{buffer}'
                    raise ValueError(msg)
                scratch += (
                    '\nThought: Previous output violated the strict format. '
                    'Reply again using EXACTLY one of the two specified formats.\n'
                )
                continue

            action = m_tool.group('action').strip()
            raw_input = m_tool.group('input').strip()

            try:
                args = json.loads(raw_input)
                if not isinstance(args, dict):
                    msg = 'Action Input must be a JSON object.'
                    raise ValueError(msg)
            except Exception as e:
                parse_retries += 1
                if self.on_parse_error == ParseErrorMode.RAISE or parse_retries >= _MAX_PARSE_RETRIES:
                    msg = f'Invalid Action Input JSON: {raw_input!r} ({e})'
                    raise ValueError(msg) from e
                scratch += '\nThought: Action Input must be a ONE-LINE JSON object. Retry with correct JSON.\n'
                continue

            tool = self._get_tool(action)

            try:
                result = await tool.run(args, context=None, convert_result=True)
            except Exception as e:
                result = {
                    'error': {
                        'type': e.__class__.__name__,
                        'server': getattr(tool, 'alias', 'local'),
                        'tool': getattr(tool, 'name', getattr(tool, 'qualified', 'unknown')),
                        'message': str(e),
                        'retryable': False,
                    }
                }

            used_tools.append(action)
            observation = self._serialize_observation(result)

            scratch += (
                '\nThought: Do I need to use a tool? Yes'
                f'\nAction: {action}'
                f'\nAction Input: {raw_input}'
                f'\nObservation: {observation}\n'
            )

        yield self._stopped_message()
