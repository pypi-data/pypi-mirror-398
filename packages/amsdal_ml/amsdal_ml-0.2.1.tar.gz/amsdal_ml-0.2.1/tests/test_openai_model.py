# ruff: noqa: S101

import asyncio

import httpx
import openai
import pytest

from amsdal_ml.ml_models.models import ModelAPIError
from amsdal_ml.ml_models.models import ModelConnectionError
from amsdal_ml.ml_models.models import ModelRateLimitError

TEMPERATURE_FOR_TEST = 0.7  # avoid PLR2004 "magic value"


@pytest.mark.usefixtures('patch_openai')
class TestOpenAIModel:
    def test_invoke_sync(self):
        from amsdal_ml.ml_config import ml_config

        ml_config.async_mode = False

        from amsdal_ml.ml_models.openai_model import OpenAIModel

        m = OpenAIModel()
        m.setup()
        out = m.invoke('hi')
        assert out == 'stubbed-sync'
        m.teardown()

    @pytest.mark.asyncio
    async def test_ainvoke_async(self):
        from amsdal_ml.ml_config import ml_config

        ml_config.async_mode = True

        from amsdal_ml.ml_models.openai_model import OpenAIModel

        m = OpenAIModel()
        m.setup()
        out = await m.ainvoke('hi')
        assert out == 'stubbed-async'
        m.teardown()

    def test_stream_sync(self):
        from amsdal_ml.ml_config import ml_config

        ml_config.async_mode = False

        from amsdal_ml.ml_models.openai_model import OpenAIModel

        m = OpenAIModel()
        m.setup()
        chunks = list(m.stream('stream it'))
        assert ''.join(chunks) == 'Hello world'
        m.teardown()

    @pytest.mark.asyncio
    async def test_astream_async(self):
        from amsdal_ml.ml_config import ml_config

        ml_config.async_mode = True

        from amsdal_ml.ml_models.openai_model import OpenAIModel

        m = OpenAIModel()
        m.setup()
        received = []
        async for c in m.astream('stream it'):
            received.append(c)
        assert ''.join(received) == 'Hello async world'
        m.teardown()

    def test_wrong_calls_raise(self):
        from amsdal_ml.ml_config import ml_config
        from amsdal_ml.ml_models.openai_model import OpenAIModel

        ml_config.async_mode = True
        m = OpenAIModel()
        m.setup()
        with pytest.raises(RuntimeError):
            m.invoke('should fail')
        m.teardown()

        ml_config.async_mode = False
        m = OpenAIModel()
        m.setup()

        async def _call():
            with pytest.raises(RuntimeError):
                await m.ainvoke('should fail')

        asyncio.run(_call())
        m.teardown()

    def test_invoke_with_messages_list(self):
        from amsdal_ml.ml_config import ml_config
        from amsdal_ml.ml_models.models import StructuredMessage

        ml_config.async_mode = False

        from amsdal_ml.ml_models.openai_model import OpenAIModel

        m = OpenAIModel()
        m.setup()
        messages: list[StructuredMessage] = [{'role': 'user', 'content': 'hi'}]
        out = m.invoke(messages)
        assert out == 'stubbed-sync'
        m.teardown()

    @pytest.mark.asyncio
    async def test_ainvoke_with_messages_list(self):
        from amsdal_ml.ml_config import ml_config
        from amsdal_ml.ml_models.models import StructuredMessage

        ml_config.async_mode = True

        from amsdal_ml.ml_models.openai_model import OpenAIModel

        m = OpenAIModel()
        m.setup()
        messages: list[StructuredMessage] = [{'role': 'user', 'content': 'hi'}]
        out = await m.ainvoke(messages)
        assert out == 'stubbed-async'
        m.teardown()


@pytest.mark.usefixtures('patch_openai')
def test_model_args_are_forwarded(monkeypatch):
    from amsdal_ml.ml_config import ml_config

    ml_config.async_mode = False
    ml_config.llm_model_name = 'gpt-x'
    ml_config.llm_temperature = TEMPERATURE_FOR_TEST

    import amsdal_ml.ml_models.openai_model as mod

    calls = {}

    # mypy-safe runtime lookup (fixture injects this at runtime)
    chat_cls = mod.FakeSyncChat  # type: ignore[attr-defined]
    orig = chat_cls.completions_create

    def spy(self, **kwargs):
        calls.update(kwargs)
        return orig(self, **kwargs)

    monkeypatch.setattr(chat_cls, 'completions_create', spy)

    from amsdal_ml.ml_models.openai_model import OpenAIModel

    m = OpenAIModel()
    m.setup()
    m.invoke('hi')
    m.teardown()

    assert calls['model'] == 'gpt-x'
    assert calls['temperature'] == TEMPERATURE_FOR_TEST


def test_setup_raises_if_key_absent(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    from amsdal_ml.ml_config import ml_config

    ml_config.openai_api_key = None

    from amsdal_ml.ml_models.openai_model import OpenAIModel

    m = OpenAIModel()
    with pytest.raises(RuntimeError):
        m.setup()


def test_setup_uses_ml_config_key_when_env_absent(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    from amsdal_ml.ml_config import ml_config

    ml_config.openai_api_key = 'sk-test-from-config'

    from amsdal_ml.ml_models.openai_model import OpenAIModel

    m = OpenAIModel()
    m.setup()
    m.teardown()


dummy_request = httpx.Request('GET', 'https://example.com')
dummy_response = httpx.Response(500, request=dummy_request)


@pytest.mark.parametrize(
    'vendor_exc_factory, expected_model_exc',
    [
        (
            lambda: openai.RateLimitError(message='rate', response=dummy_response, body=None),
            ModelRateLimitError,
        ),
        (
            lambda: openai.APIConnectionError(message='conn', request=dummy_request),
            ModelConnectionError,
        ),
        (
            # v1 APIStatusError does not accept 'status_code' kw; status is in response
            lambda: openai.APIStatusError(
                message='status',
                response=dummy_response,
                body=None,
            ),
            ModelAPIError,
        ),
        (
            # v1 APIError requires a request arg
            lambda: openai.APIError(message='generic', request=dummy_request, body=None),
            ModelAPIError,
        ),
    ],
)
@pytest.mark.usefixtures('patch_openai')
def test_invoke_maps_vendor_errors(monkeypatch, vendor_exc_factory, expected_model_exc):
    from amsdal_ml.ml_config import ml_config

    ml_config.async_mode = False

    import amsdal_ml.ml_models.openai_model as mod

    def boom(*_a, **_kw):
        raise vendor_exc_factory()

    chat_cls = mod.FakeSyncChat  # type: ignore[attr-defined]
    monkeypatch.setattr(chat_cls, 'completions_create', boom)

    from amsdal_ml.ml_models.openai_model import OpenAIModel

    m = OpenAIModel()
    m.setup()
    with pytest.raises(expected_model_exc):
        m.invoke('hi')
    m.teardown()


@pytest.mark.parametrize('tool_choice', ['auto', {'type': 'function', 'function': {'name': 'test_func'}}])
@pytest.mark.usefixtures('patch_openai')
def test_tool_choice_forwarded(monkeypatch, tool_choice):
    from amsdal_ml.ml_config import ml_config

    ml_config.async_mode = False

    import amsdal_ml.ml_models.openai_model as mod

    calls = {}

    # mypy-safe runtime lookup (fixture injects this at runtime)
    chat_cls = mod.FakeSyncChat  # type: ignore[attr-defined]
    orig = chat_cls.completions_create

    def spy(self, **kwargs):
        calls.update(kwargs)
        return orig(self, **kwargs)

    monkeypatch.setattr(chat_cls, 'completions_create', spy)

    from amsdal_ml.ml_models.openai_model import OpenAIModel

    m = OpenAIModel()
    m.setup()
    m.invoke('hi', tool_choice=tool_choice)
    m.teardown()

    assert calls['tool_choice'] == tool_choice
