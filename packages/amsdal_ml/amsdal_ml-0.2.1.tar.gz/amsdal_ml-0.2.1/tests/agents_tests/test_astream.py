import inspect

import pytest

from amsdal_ml.agents.default_qa_agent import DefaultQAAgent

from .test_fakes import FakeModel
from .test_fakes import FakeRetrieverTool
from .test_fakes import FakeToolClient
from .test_fakes import final_answer
from .test_fakes import tool_call


async def _normalize_aiter(val):
    """Turn coroutine-or-iterator into an async iterator for test use."""
    if inspect.iscoroutine(val):
        val = await val
    return val


@pytest.mark.asyncio
async def test_astream_async_tool_then_final():
    scripted = [
        tool_call('retriever.search'),  # {"query":"q"}
        final_answer('AsyncDone'),
    ]
    model = FakeModel(async_mode=True, scripted=scripted)
    tool = FakeRetrieverTool()
    client = FakeToolClient(tool=tool, alias='retriever')
    agent = DefaultQAAgent(model=model, tools=[client])

    received: list[str] = []
    stream = await _normalize_aiter(agent.astream('q'))
    async for c in stream:
        received.append(c)

    assert ''.join(received).strip() == 'AsyncDone'  # noqa: S101
    assert len(tool.calls) == 1  # noqa: S101
    assert tool.calls[0]['query'] == 'q'  # noqa: S101
