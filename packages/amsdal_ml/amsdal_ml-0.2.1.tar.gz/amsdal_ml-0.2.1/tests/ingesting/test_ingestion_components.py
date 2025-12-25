from __future__ import annotations

import io
from collections.abc import Sequence
from typing import Any

import pytest

from amsdal_ml.ml_ingesting import IngestionSource
from amsdal_ml.ml_ingesting import LoadedDocument
from amsdal_ml.ml_ingesting import LoadedPage
from amsdal_ml.ml_ingesting import TextChunk
from amsdal_ml.ml_ingesting.embedders.embedder import Embedder
from amsdal_ml.ml_ingesting.embedders.openai_embedder import OpenAIEmbedder
from amsdal_ml.ml_ingesting.embedding_data import EmbeddingData
from amsdal_ml.ml_ingesting.loaders.loader import Loader
from amsdal_ml.ml_ingesting.loaders.pdf_loader import PdfLoader
from amsdal_ml.ml_ingesting.pipeline import DefaultIngestionPipeline
from amsdal_ml.ml_ingesting.processors.cleaner import Cleaner
from amsdal_ml.ml_ingesting.processors.text_cleaner import TextCleaner
from amsdal_ml.ml_ingesting.splitters.splitter import Splitter
from amsdal_ml.ml_ingesting.splitters.token_splitter import TokenSplitter
from amsdal_ml.ml_ingesting.stores.embedding_data import EmbeddingDataStore
from amsdal_ml.ml_ingesting.stores.store import EmbeddingStore

EXPECTED_PAGE_NUMBER = 2


class _FakePdfPage:
    def __init__(self, text: str) -> None:
        self._text = text

    def get_text(self, *_: Any, **__: Any) -> str:
        return self._text


class _FakePdfDoc:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    def __init__(self):
        self._pages = [_FakePdfPage('Hello PDF'), _FakePdfPage('')]
        self.metadata = {'Author': 'Tester'}

    def __iter__(self):
        return iter(self._pages)

    def close(self) -> None:  # noqa: D401
        """No-op close for compatibility."""


def test_pdf_loader_uses_reader(monkeypatch):
    monkeypatch.setattr('amsdal_ml.ml_ingesting.loaders.pdf_loader.pymupdf.open', lambda *_, **__: _FakePdfDoc())
    loader = PdfLoader()
    buf = io.BytesIO(b'%PDF-1.4 test')
    doc = loader.load(buf, filename='doc.pdf', metadata={'source': 'unit'})
    assert len(doc.pages) == 1
    assert doc.pages[0].page_number == 1
    assert doc.pages[0].text == 'Hello PDF'
    assert doc.metadata['Author'] == 'Tester'
    assert doc.metadata['source'] == 'unit'
    assert doc.metadata['filename'] == 'doc.pdf'


def test_text_cleaner_normalizes_and_drops_empty():
    doc = LoadedDocument(
        pages=[
            LoadedPage(page_number=1, text='Hello\tworld\r\n', metadata={'page_number': 1}),
            LoadedPage(page_number=2, text=' ', metadata={'page_number': 2}),
        ],
        metadata={'foo': 'bar'},
    )
    cleaner = TextCleaner()
    cleaned = cleaner.clean(doc)
    assert len(cleaned.pages) == 1
    assert cleaned.pages[0].text == 'Hello world'
    assert cleaned.metadata['foo'] == 'bar'


def test_token_splitter_preserves_metadata():
    doc = LoadedDocument(
        pages=[LoadedPage(page_number=1, text=' '.join(['w'] * 40), metadata={'page_number': 1})],
        metadata={'filename': 'file.pdf'},
    )
    splitter = TokenSplitter(max_tokens=10, overlap_tokens=5, token_len_fn=lambda _: 1)
    chunks = splitter.split(doc)
    assert chunks, 'chunks should not be empty'
    assert chunks[0].metadata['filename'] == 'file.pdf'
    assert chunks[0].metadata['page_number'] == 1
    assert chunks[0].index == 0
    assert all(ch.text for ch in chunks)


class _FakeLoader(Loader):
    def __init__(self, doc: LoadedDocument):
        self.doc = doc
        self.called = False

    def load(self, *_, **__):  # noqa: ANN001
        self.called = True
        return self.doc

    async def aload(self, *_, **__):  # noqa: ANN001
        return self.load(*_, **__)


class _FakeCleaner(Cleaner):
    def __init__(self, doc: LoadedDocument):
        self.doc = doc
        self.called = False

    def clean(self, *_):  # noqa: ANN001
        self.called = True
        return self.doc

    async def aclean(self, *_):  # noqa: ANN001
        return self.clean(*_)


class _FakeSplitter(Splitter):
    def __init__(self, chunks: list[TextChunk]):
        self.chunks = chunks
        self.called = False

    def split(self, *_):  # noqa: ANN001
        self.called = True
        return self.chunks

    async def asplit(self, *_):  # noqa: ANN001
        return self.split(*_)


class _FakeEmbedder(Embedder):
    def __init__(self):
        self.calls: list[str] = []

    def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        return [1.0, 0.0, 0.0]

    async def aembed(self, text: str) -> list[float]:
        return self.embed(text)


class _FakeStore(EmbeddingStore):
    def __init__(self):
        self.saved = None

    def save(self, embeddings: Sequence[EmbeddingData], *, source: IngestionSource | None = None) -> list[Any]:
        self.saved = embeddings
        return list(embeddings)

    async def asave(self, embeddings: Sequence[EmbeddingData], *, source: IngestionSource | None = None) -> list[Any]:
        return self.save(embeddings, source=source)


def test_pipeline_assembles_and_saves():
    doc = LoadedDocument(pages=[LoadedPage(page_number=1, text='hello world', metadata={})], metadata={})
    chunks = [TextChunk(index=0, text='hello world', tags=['c'], metadata={'page_number': 1})]

    loader = _FakeLoader(doc)
    cleaner = _FakeCleaner(doc)
    splitter = _FakeSplitter(chunks)
    embedder = _FakeEmbedder()
    store = _FakeStore()

    pipeline = DefaultIngestionPipeline(
        loader=loader,
        cleaner=cleaner,
        splitter=splitter,
        embedder=embedder,
        store=store,
    )

    source = IngestionSource(object_class='Doc', object_id='1', tags=['a'], metadata={'filename': 'f.pdf'})
    result = pipeline.run(io.BytesIO(b'data'), filename='f.pdf', tags=['b'], source=source)

    assert result == store.saved
    assert loader.called and cleaner.called and splitter.called
    assert embedder.calls == ['hello world']
    assert store.saved[0].tags == ['a', 'b', 'c']
    assert store.saved[0].metadata['filename'] == 'f.pdf'
    assert store.saved[0].metadata['page_number'] == 1


class _DummyManager:
    def __init__(self):
        self.saved = None

    def bulk_create(self, objs):  # noqa: ANN001
        self.saved = objs
        return objs


class _DummyModel:
    objects = _DummyManager()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_embedding_store_merges_tags_and_metadata():
    store = EmbeddingDataStore(model_cls=_DummyModel)
    embeddings = [
        EmbeddingData(
            chunk_index=0,
            raw_text='t',
            embedding=[0.1],
            tags=['x'],
            metadata={'page_number': 2},
        )
    ]
    source = IngestionSource(object_class='Doc', object_id='42', tags=['a'], metadata={'filename': 'f.pdf'})

    saved = store.save(embeddings, source=source)
    assert len(saved) == 1
    obj = saved[0]
    assert obj.data_object_class == 'Doc'
    assert obj.data_object_id == '42'
    assert obj.tags == ['a', 'x']
    assert obj.ml_metadata['filename'] == 'f.pdf'
    assert obj.ml_metadata['page_number'] == EXPECTED_PAGE_NUMBER


@pytest.mark.skip(reason='integration: requires real OpenAI key')
def test_openai_embedder_smoke():
    embedder = OpenAIEmbedder()
    vec = embedder.embed('ping')
    assert isinstance(vec, list)
    assert vec, 'embedding should not be empty'
