import pytest

from amsdal_ml.agents.default_qa_agent import DefaultQAAgent

from .test_fakes import FakeModel
from .test_fakes import FakeRetrieverTool
from .test_fakes import FakeToolClient
from .test_fakes import tool_call


@pytest.mark.asyncio
async def test_tool_called_with_expected_args_single_step_async():
    scripted = [
        tool_call(
            "retriever.search",
            '{"query":"q","k":7,"include_tags":["a"],"exclude_tags":["b"]}',
        )
    ]
    model = FakeModel(async_mode=True, scripted=scripted)
    tool = FakeRetrieverTool()
    client = FakeToolClient(tool=tool, alias="retriever")
    agent = DefaultQAAgent(model=model, tools=[client], max_steps=1)

    out = await agent.arun("question?")
    assert out.answer.lower().startswith("agent stopped")  # noqa: S101
    assert out.used_tools == ["retriever.search"]  # noqa: S101

    assert len(tool.calls) == 1  # noqa: S101
    call_kwargs = tool.calls[0]
    assert call_kwargs == {
        "query": "q",
        "k": 7,
        "include_tags": ["a"],
        "exclude_tags": ["b"],
    }  # noqa: S101
