import inspect

import pytest

from amsdal_ml.agents.default_qa_agent import DefaultQAAgent

from .test_fakes import FakeModel
from .test_fakes import FakeRetrieverTool
from .test_fakes import FakeToolClient
from .test_fakes import final_answer


async def _normalize_aiter(val):
    """Turn coroutine-or-iterator into an async iterator for test use."""
    if inspect.iscoroutine(val):
        val = await val
    return val


@pytest.mark.asyncio
async def test_astream_final_only():
    scripted = [final_answer('OK')]
    model = FakeModel(async_mode=True, scripted=scripted)
    tool = FakeRetrieverTool()
    client = FakeToolClient(tool=tool, alias='retriever')
    agent = DefaultQAAgent(model=model, tools=[client])

    received: list[str] = []
    stream = await _normalize_aiter(agent.astream('hi'))
    async for c in stream:
        received.append(c)

    assert ''.join(received).strip() == 'OK'  # noqa: S101
