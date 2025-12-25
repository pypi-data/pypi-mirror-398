from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from amsdal_models.classes.model import Model
from pydantic import Field

from amsdal_ml.agents.default_qa_agent import DefaultQAAgent
from amsdal_ml.agents.python_tool import PythonTool
from amsdal_ml.ml_models.models import LLModelInput
from amsdal_ml.ml_models.models import MLModel
from amsdal_ml.ml_models.utils import ResponseFormat
from amsdal_ml.ml_retrievers.query_retriever import NLQueryRetriever


class Product(Model):
    name: str = Field(...)
    price: float = Field(...)


class MockAgentLLM(MLModel):
    def __init__(self, react_output: str) -> None:
        self._react_output = react_output
        self.async_mode = True

    @property
    def supported_formats(self) -> set[ResponseFormat]:
        return {ResponseFormat.PLAIN_TEXT}

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

    def setup(self) -> None:
        pass

    def teardown(self) -> None:
        pass

    def invoke(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        attachments: list[Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> str:
        return self._react_output

    async def ainvoke(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        attachments: list[Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> str:
        return self._react_output

    def stream(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        attachments: list[Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ):
        yield self._react_output

    async def astream(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        attachments: list[Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ):
        yield self._react_output


class MockRetrieverLLM(MLModel):
    def __init__(self, filter_json: str) -> None:
        self._filter_json = filter_json
        self.async_mode = False

    @property
    def supported_formats(self) -> set[ResponseFormat]:
        return {ResponseFormat.JSON_OBJECT}

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

    def setup(self) -> None:
        pass

    def teardown(self) -> None:
        pass

    def invoke(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        attachments: list[Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> str:
        return self._filter_json

    async def ainvoke(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        attachments: list[Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> str:
        return self._filter_json

    def stream(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        attachments: list[Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ):
        yield self._filter_json

    async def astream(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        attachments: list[Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ):
        yield self._filter_json


@pytest.mark.asyncio
async def test_agent_with_nlq_retriever_tool() -> None:
    expected_llm_calls = 2

    mock_queryset = MagicMock()
    mock_queryset.entity = Product
    mock_queryset._annotations = {}
    mock_queryset.filter.return_value = mock_queryset
    mock_queryset.execute.return_value = [
        Product(name='Laptop', price=1200.0),
        Product(name='Gaming PC', price=2500.0),
    ]

    retriever_llm = MockRetrieverLLM(
        """
        {
            "filters": [
                {"field": "price", "lookup": "gt", "value": 1000}
            ]
        }
        """,
    )

    def search_products(query: str) -> list[Product]:
        retriever: NLQueryRetriever[Product] = NLQueryRetriever(
            llm=retriever_llm,
            queryset=mock_queryset,
        )
        return retriever.executor.search(query)

    tool = PythonTool(
        func=search_products,
        name='search_products',
        description='Searches for products in the database using natural language.',
    )

    react_output = """Thought: Do I need to use a tool? Yes
Action: search_products
Action Input: {"query": "find products more expensive than 1000"}"""
    final_answer_output = """Thought: Do I need to use a tool? No
Final Answer: Found 2 expensive products: Laptop at $1200.0 and Gaming PC at $2500.0."""

    agent_llm = MockAgentLLM(react_output)
    agent_llm.ainvoke = AsyncMock(side_effect=[react_output, final_answer_output])  # type: ignore[method-assign]

    agent = DefaultQAAgent(model=agent_llm, tools=[tool])
    result = await agent.arun('Find expensive products')

    assert 'Laptop' in result.answer
    assert 'Gaming PC' in result.answer
    assert agent_llm.ainvoke.call_count == expected_llm_calls
    mock_queryset.filter.assert_called_with(price__gt=1000)
    mock_queryset.execute.assert_called_once()
