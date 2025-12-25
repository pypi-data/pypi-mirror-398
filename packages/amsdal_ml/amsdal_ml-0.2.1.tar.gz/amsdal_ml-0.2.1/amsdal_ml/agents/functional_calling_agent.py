from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import no_type_check

from amsdal_ml.agents.agent import Agent
from amsdal_ml.agents.agent import AgentOutput
from amsdal_ml.agents.mcp_client_tool import ClientToolProxy
from amsdal_ml.agents.python_tool import PythonTool
from amsdal_ml.agents.python_tool import _PythonToolProxy
from amsdal_ml.agents.tool_adapters import ToolAdapter
from amsdal_ml.agents.tool_adapters import get_tool_adapter
from amsdal_ml.fileio.base_loader import PLAIN_TEXT
from amsdal_ml.fileio.base_loader import FileAttachment
from amsdal_ml.mcp_client.base import ToolClient
from amsdal_ml.mcp_client.base import ToolInfo
from amsdal_ml.ml_models.models import MLModel
from amsdal_ml.ml_models.models import StructuredMessage
from amsdal_ml.ml_models.utils import ResponseFormat


class FunctionalCallingAgent(Agent):
    """
    An agent that uses the native function calling capabilities of LLMs (e.g., OpenAI)
    to execute tools and answer user queries.

    Attributes:
        model (MLModel): The LLM model instance to use (must support function calling).
        max_steps (int): Maximum number of tool execution steps allowed.
        per_call_timeout (float | None): Timeout in seconds for each tool execution.
    """

    def __init__(
        self,
        *,
        model: MLModel,
        tools: list[PythonTool | ToolClient] | None = None,
        max_steps: int = 6,
        per_call_timeout: float | None = 20.0,
        adapter: ToolAdapter | None = None,
    ):
        """
        Initialize the FunctionalCallingAgent.

        Args:
            model: The LLM model to use.
            tools: A list of tools (PythonTool or ToolClient) available to the agent.
            max_steps: The maximum number of iterations (model -> tool -> model) allowed.
            per_call_timeout: Timeout for individual tool calls.
            adapter: Optional tool adapter. If None, will auto-detect based on LLM type.
        """
        self._tools: list[PythonTool | ToolClient] = tools or []
        self._indexed_tools: dict[str, ClientToolProxy | _PythonToolProxy] = {}
        self.model = model
        self.model.setup()
        self.max_steps = max_steps
        self.per_call_timeout = per_call_timeout
        self._is_tools_index_built = False
        self.adapter = adapter or get_tool_adapter(model)
        self._response_format: ResponseFormat = self._select_response_format()

    async def arun(
        self,
        user_query: str,
        *,
        history: list[StructuredMessage] | None = None,
        attachments: list[FileAttachment] | None = None,
    ) -> AgentOutput:
        """
        Run the agent asynchronously to answer a user query.

        This method executes the main loop:
        1. Send query and tools to the model.
        2. If model requests tool calls, execute them and report back.
        3. Repeat until the model provides a final answer or max_steps is reached.

        Args:
            user_query: The question or instruction from the user.
            history: Optional chat history to continue the conversation.
            attachments: Optional list of files/documents to include in context.

        Returns:
            AgentOutput: The final answer and metadata about used tools.
        """
        if not self._is_tools_index_built:
            await self._build_clients_index()

        content = self._merge_attachments(user_query, attachments)
        messages = history.copy() if history else []

        #TODO: JSON markdown tables support for nlqretriever
        #if self._response_format == ResponseFormat.JSON_OBJECT:
        #    messages.append({'role': 'system', 'content': 'Please respond in json format.'})

        messages.append({self.model.role_field: self.model.input_role, self.model.content_field: content})  # type: ignore[misc]
        used_tools: list[str] = []
        tools_schema = self.adapter.get_tools_schema(self._indexed_tools)

        for _ in range(self.max_steps):
            response_str = await self.model.ainvoke(
                input=messages,
                tools=tools_schema if tools_schema else None,
                response_format=self._response_format,
            )

            try:
                response_data = json.loads(response_str)
            except json.JSONDecodeError:
                response_data = {self.model.role_field: self.model.output_role, self.model.content_field: response_str}

            messages.append(response_data)

            content_text, tool_calls = self.adapter.parse_response(response_data)

            if not tool_calls:
                return AgentOutput(answer=content_text or '', used_tools=used_tools)

            for tool_call in tool_calls:
                function_name, arguments_str, call_id = self.adapter.get_tool_call_info(tool_call)

                used_tools.append(function_name)

                try:
                    args = json.loads(arguments_str)
                    tool = self._indexed_tools[function_name]
                    result = await tool.run(args)

                    if isinstance(result, (dict, list)):
                        content_str = json.dumps(result, ensure_ascii=False)
                    else:
                        content_str = str(result)
                except Exception as e:
                    content_str = f'Error: {e!s}'

                messages.append({
                    self.model.role_field: self.model.tool_role,  # type: ignore[misc]
                    self.model.tool_call_id_field: call_id,
                    self.model.tool_name_field: function_name,
                    self.model.content_field: content_str,
                })

        return AgentOutput(
            answer='Agent stopped due to iteration limit.',
            used_tools=used_tools,
        )

    @no_type_check
    async def astream(
        self,
        user_query: str,
        *,
        history: list[StructuredMessage] | None = None,
        attachments: list[FileAttachment] | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream the agent's response asynchronously.

        Currently, this method buffers the full execution and yields the final answer
        at once. True streaming of intermediate steps is not yet implemented.

        Args:
            user_query: The question or instruction from the user.
            history: Optional chat history to continue the conversation.
            attachments: Optional list of files/documents.

        Yields:
            str: Chunks of the final answer (currently just the full answer).
        """
        output = await self.arun(user_query, history=history, attachments=attachments)
        yield output.answer

    def _select_response_format(self) -> ResponseFormat:
        """
        Select the best response format supported by the model.

        Returns:
            ResponseFormat: PLAIN_TEXT to allow raw Markdown tables.
        """
        return ResponseFormat.PLAIN_TEXT

    async def _build_clients_index(self) -> None:
        """
        Build the internal index of tools.

        Iterates through the provided tools, resolving ToolClients into individual
        callable proxies and indexing PythonTools directly.
        """
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
                proxy = _PythonToolProxy(tool, timeout=self.per_call_timeout)  # type: ignore[assignment]
                self._indexed_tools[tool.name] = proxy
            else:
                msg = f'Unsupported tool type: {type(tool)}'
                raise TypeError(msg)

        self._is_tools_index_built = True

    def _merge_attachments(self, query: str, attachments: list[FileAttachment] | None) -> str:
        """
        Merge plain text attachments into the user query.

        Args:
            query: The original user query.
            attachments: Optional list of file attachments.

        Returns:
            str: The query augmented with attachment content.
        """
        if not attachments:
            return query
        extras = [str(a.content) for a in attachments if a.type == PLAIN_TEXT]
        if not extras:
            return query
        return f'{query}\n\n[ATTACHMENTS]\n' + '\n\n'.join(extras)
