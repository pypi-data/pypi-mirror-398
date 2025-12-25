import json
from typing import Any
from unittest.mock import AsyncMock

import pytest

from amsdal_ml.agents.functional_calling_agent import FunctionalCallingAgent
from amsdal_ml.agents.python_tool import PythonTool
from amsdal_ml.agents.tool_adapters import OpenAIToolAdapter
from amsdal_ml.mcp_client.base import ToolClient
from amsdal_ml.mcp_client.base import ToolInfo
from amsdal_ml.ml_models.models import LLModelInput
from amsdal_ml.ml_models.models import MLModel
from amsdal_ml.ml_models.utils import ResponseFormat


class MockModel(MLModel):
    def __init__(self, responses: list[str], supported_formats: set[ResponseFormat] | None = None):
        self.responses = responses
        self.response_index = 0
        self.calls: list[dict[str, Any]] = []
        self._supported_formats = supported_formats or {ResponseFormat.JSON_OBJECT, ResponseFormat.PLAIN_TEXT}
        self.async_mode = True

    @property
    def supported_formats(self) -> set[ResponseFormat]:
        return self._supported_formats

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
        self.calls.append({
            'input': input,
            'tools': tools,
            'response_format': response_format
        })
        if self.response_index < len(self.responses):
            resp = self.responses[self.response_index]
            self.response_index += 1
            return resp
        return ""

    def invoke(self, *args, **kwargs):
        raise NotImplementedError

    def stream(self, *args, **kwargs):
        raise NotImplementedError

    async def astream(self, *args, **kwargs):
        raise NotImplementedError

@pytest.mark.skip(reason="agent is currently using plain_text only")
@pytest.mark.asyncio
async def test_functional_agent_json_object_flow():
    expected_calls = 2

    tool_call_resp = json.dumps({
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "add",
                    "arguments": json.dumps({"a": 2, "b": 2})
                }
            }
        ]
    })

    final_resp = json.dumps({
        "role": "assistant",
        "content": "The answer is 4.",
        "tool_calls": None
    })

    model = MockModel([tool_call_resp, final_resp])

    async def add(a: int, b: int) -> int:
        return a + b

    tool = PythonTool(func=add, name="add", description="Adds two numbers")

    agent = FunctionalCallingAgent(model=model, tools=[tool])

    output = await agent.arun("What is 2+2?")

    assert output.answer == "The answer is 4."
    assert output.used_tools == ["add"]
    assert len(model.calls) == expected_calls
    assert model.calls[0]['response_format'] == ResponseFormat.JSON_OBJECT


@pytest.mark.asyncio
async def test_functional_agent_plain_text_fallback():
    raw_text_resp = "I am a plain text model."

    model = MockModel(
        [raw_text_resp],
        supported_formats={ResponseFormat.PLAIN_TEXT}
    )

    agent = FunctionalCallingAgent(model=model)

    assert agent._response_format == ResponseFormat.PLAIN_TEXT

    output = await agent.arun("Who are you?")

    assert output.answer == "I am a plain text model."
    assert output.used_tools == []
    assert len(model.calls) == 1
    assert model.calls[0]['response_format'] == ResponseFormat.PLAIN_TEXT


@pytest.mark.asyncio
async def test_functional_agent_malformed_json_fallback():
    malformed_resp = "This is not JSON"

    model = MockModel(
        [malformed_resp],
        supported_formats={ResponseFormat.JSON_OBJECT}
    )

    agent = FunctionalCallingAgent(model=model)

    output = await agent.arun("Say something")

    assert output.answer == "This is not JSON"
    assert len(model.calls) == 1


@pytest.mark.asyncio
async def test_openai_adapter_parsing():
    adapter = OpenAIToolAdapter()

    data_content = {"role": "assistant", "content": "Hello", "tool_calls": None}
    content, tools = adapter.parse_response(data_content)
    assert content == "Hello"
    assert tools is None

    data_tool = {
        "role": "assistant",
        "content": None,
        "tool_calls": [{"id": "1", "function": {"name": "test", "arguments": "{}"}}]
    }
    content, tools = adapter.parse_response(data_tool)
    assert content is None
    assert tools is not None
    assert len(tools) == 1

    name, args, cid = adapter.get_tool_call_info(tools[0])
    assert name == "test"
    assert args == "{}"
    assert cid == "1"


@pytest.mark.asyncio
async def test_client_tool_integration():
    mock_client = AsyncMock(spec=ToolClient)
    mock_client.list_tools.return_value = [
        ToolInfo(name="search", alias="google", description="Search web", input_schema={})
    ]
    mock_client.call.return_value = "Search results"

    tool_call_resp = json.dumps({
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_2",
                "type": "function",
                "function": {
                    "name": "google.search",
                    "arguments": json.dumps({"query": "test"})
                }
            }
        ]
    })

    final_resp = json.dumps({
        "role": "assistant",
        "content": "Found it.",
        "tool_calls": None
    })

    model = MockModel([tool_call_resp, final_resp])

    agent = FunctionalCallingAgent(model=model, tools=[mock_client])

    output = await agent.arun("Search test")

    assert output.answer == "Found it."
    assert output.used_tools == ["google.search"]

    mock_client.call.assert_called_once_with("search", {"query": "test"}, timeout=20.0)
