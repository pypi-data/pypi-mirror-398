import asyncio
import os
import shutil
import tempfile
import types
from collections.abc import AsyncIterator
from enum import Enum
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
import pytest_asyncio
from amsdal.manager import AsyncAmsdalManager
from amsdal.utils.tests.enums import DbExecutionType
from amsdal.utils.tests.enums import LakehouseOption
from amsdal.utils.tests.enums import StateOption
from amsdal.utils.tests.helpers import async_init_manager_and_migrate


class _Msg:
    def __init__(self, content):
        self.content = content


class _ChoiceMsg:
    def __init__(self, content):
        self.message = _Msg(content)


class _Delta:
    def __init__(self, content):
        self.content = content


class _ChoiceDelta:
    def __init__(self, content):
        self.delta = _Delta(content)


class _Resp:
    def __init__(self, content):
        self.choices = [_ChoiceMsg(content)]


class _StreamChunk:
    def __init__(self, content):
        self.choices = [_ChoiceDelta(content)]


class FakeSyncChat:
    def __init__(self, content: str = 'stubbed-sync', stream_chunks: list[str] | None = None):
        self._content = content
        self._stream_chunks = stream_chunks or ['Hello ', 'world']

    def completions_create(self, **kwargs):
        if kwargs.get('stream'):

            def _gen():
                for c in self._stream_chunks:
                    yield _StreamChunk(c)

            return _gen()
        return _Resp(self._content)

    @property
    def completions(self):
        obj = types.SimpleNamespace()
        obj.create = self.completions_create
        return obj


class FakeSyncClient:
    def __init__(self, *_a, **_kw):
        self.chat = FakeSyncChat()


class FakeAsyncChat:
    def __init__(self, content: str = 'stubbed-async', stream_chunks: list[str] | None = None):
        self._content = content
        self._stream_chunks = stream_chunks or ['Hello ', 'async ', 'world']

    async def completions_create(self, **kwargs):
        if kwargs.get('stream'):

            async def _agen():
                for c in self._stream_chunks:
                    await asyncio.sleep(0)
                    yield _StreamChunk(c)

            return _agen()
        return _Resp(self._content)

    @property
    def completions(self):
        obj = types.SimpleNamespace()
        obj.create = self.completions_create
        return obj


class FakeAsyncClient:
    def __init__(self, *_a, **_kw):
        self.chat = FakeAsyncChat()


@pytest.fixture(autouse=True)
def _set_env_key(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test-123')


@pytest.fixture
def patch_openai(monkeypatch):
    import amsdal_ml.ml_models.openai_model as mod

    monkeypatch.setattr(mod, 'OpenAI', FakeSyncClient)
    monkeypatch.setattr(mod, 'AsyncOpenAI', FakeAsyncClient)
    monkeypatch.setattr(mod, 'FakeSyncChat', FakeSyncChat, raising=False)
    monkeypatch.setattr(mod, 'FakeAsyncChat', FakeAsyncChat, raising=False)
    return mod


class DatabaseBackend(Enum):
    SQLITE = 'sqlite'
    POSTGRES = 'postgres'


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        '--database_backend',
        action='store',
        default=DatabaseBackend.SQLITE.value,
        help='Backend to use for lakehouse (sqlite-historical or postgres-historical)',
    )


@pytest.fixture(scope='session')
def database_backend(request: Any) -> DatabaseBackend:
    backend_str = request.config.getoption('--database_backend')
    return DatabaseBackend(backend_str)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment with proper configuration."""
    os.environ['AMSDAL_DISABLE_CLOUD'] = 'true'
    os.environ['AMSDAL_DISABLE_AUTH'] = 'true'

    with mock.patch('amsdal.cloud.services.auth.signup_service.want_signup_input', return_value=False):
        with mock.patch('amsdal.manager.AmsdalManager.authenticate', return_value=None):
            with mock.patch('amsdal.manager.AsyncAmsdalManager.authenticate', return_value=None):
                yield


TESTS_DIR = Path(__file__).parent


def _create_temp_models_dir() -> Path:
    """Create temporary directory with modified internal models located in amsdal_ml/models for testing."""
    temp_dir = Path(tempfile.mkdtemp())

    # Copy the entire amsdal_ml package to temp directory
    source_package = TESTS_DIR.parent / 'amsdal_ml'
    dest_package = temp_dir / 'amsdal_ml'
    shutil.copytree(source_package, dest_package)

    # Modify __module_type__ in model files
    models_dir = dest_package / 'models'
    for model_file in models_dir.glob('*.py'):
        if model_file.name == '__init__.py':
            continue

        content = model_file.read_text()
        if '__module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB' in content:
            modified_content = content.replace(
                '__module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB',
                '__module_type__: ClassVar[ModuleType] = ModuleType.USER'
            )
            model_file.write_text(modified_content)

    return temp_dir


@pytest_asyncio.fixture
async def async_internal_amsdal_manager(database_backend: DatabaseBackend) -> AsyncIterator[AsyncAmsdalManager]:
    """Create async AmsdalManager instance for testing using internal models located in ./amsdal_ml/models"""
    temp_dir = _create_temp_models_dir()
    is_postgres = database_backend == DatabaseBackend.POSTGRES
    lakehouse_option = LakehouseOption.postgres if is_postgres else LakehouseOption.sqlite
    state_option = StateOption.postgres if is_postgres else StateOption.sqlite

    try:
        async with async_init_manager_and_migrate(
            src_dir_path=temp_dir / 'amsdal_ml',
            db_execution_type=DbExecutionType.include_state_db,
            lakehouse_option=lakehouse_option,
            state_option=state_option,
            ACCESS_TOKEN='test_token_for_testing',
        ) as manager:
            yield manager
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest_asyncio.fixture
async def async_test_amsdal_manager(database_backend: DatabaseBackend) -> AsyncIterator[AsyncAmsdalManager]:
    """Create async AmsdalManager instance for testing using test models from fixtures."""
    is_postgres = database_backend == DatabaseBackend.POSTGRES
    lakehouse_option = LakehouseOption.postgres if is_postgres else LakehouseOption.sqlite
    state_option = StateOption.postgres if is_postgres else StateOption.sqlite

    async with async_init_manager_and_migrate(
        src_dir_path=TESTS_DIR / 'fixtures',
        app_models_path=TESTS_DIR / 'fixtures' / 'models',
        db_execution_type=DbExecutionType.include_state_db,
        lakehouse_option=lakehouse_option,
        state_option=state_option,
        ACCESS_TOKEN='test_token_for_testing',
    ) as manager:
        yield manager
