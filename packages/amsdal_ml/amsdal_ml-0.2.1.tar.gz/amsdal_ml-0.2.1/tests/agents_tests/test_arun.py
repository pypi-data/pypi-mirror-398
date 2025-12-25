import pytest

from amsdal_ml.agents.default_qa_agent import DefaultQAAgent

from .test_fakes import FakeModel
from .test_fakes import FakeRetrieverTool
from .test_fakes import FakeToolClient
from .test_fakes import final_answer
from .test_fakes import tool_call


@pytest.mark.asyncio
async def test_arun_async_tool_then_final():
    scripted = [
        tool_call('retriever.search'),
        final_answer('AsyncDone'),
    ]
    model = FakeModel(async_mode=True, scripted=scripted)
    tool = FakeRetrieverTool()
    client = FakeToolClient(tool=tool, alias='retriever')
    agent = DefaultQAAgent(model=model, tools=[client])

    out = await agent.arun('q')

    assert out.answer == 'AsyncDone'  # noqa: S101
    assert out.used_tools == ['retriever.search']  # noqa: S101
    assert len(tool.calls) == 1  # noqa: S101
    assert tool.calls[0]['query'] == 'q'  # noqa: S101
