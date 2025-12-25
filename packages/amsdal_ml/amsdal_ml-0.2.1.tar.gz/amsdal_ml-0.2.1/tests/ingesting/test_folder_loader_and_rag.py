from __future__ import annotations

from pathlib import Path

from amsdal_ml.ml_ingesting import IngestionSource
from amsdal_ml.ml_ingesting.embedders.embedder import Embedder
from amsdal_ml.ml_ingesting.loaders import PdfFolderLoader
from amsdal_ml.ml_ingesting.loaders import PdfLoader
from amsdal_ml.ml_ingesting.pipeline import DefaultIngestionPipeline
from amsdal_ml.ml_ingesting.processors import TextCleaner
from amsdal_ml.ml_ingesting.splitters import TokenSplitter
from amsdal_ml.ml_ingesting.stores import EmbeddingDataStore
from amsdal_ml.ml_retrievers import OpenAIRetriever
from amsdal_ml.ml_retrievers import RetrievalChunk

NUM_PDFS = 2


class _DummyManager:
    def __init__(self):
        self.saved = []

    def bulk_create(self, objs):  # noqa: ANN001
        self.saved.extend(objs)
        return objs

    async def bulk_acreate(self, objs):  # pragma: no cover - async path not used here
        self.saved.extend(objs)
        return objs

    def all(self):  # pragma: no cover - used via retriever
        return []


class _DummyModel:
    objects = _DummyManager()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _FakeRetriever(OpenAIRetriever):
    def __init__(self, *, rows):
        super().__init__(embedder=None)
        self._rows = rows

    def _embed_query(self, text: str):  # noqa: ANN001
        return [0.0]

    async def _aembed_query(self, text: str):  # noqa: ANN001
        return [0.0]

    def similarity_search(self, *_, **__):  # noqa: ANN001
        return self._rows


def test_folder_loader_and_pipeline_and_retrieval(tmp_path):
    fixtures = Path(__file__).parent.parent / 'test_files' / 'pdf'
    target = tmp_path / 'pdf'
    target.mkdir(parents=True, exist_ok=True)
    for pdf in fixtures.glob('*.pdf'):
        target.joinpath(pdf.name).write_bytes(pdf.read_bytes())

    loader = PdfFolderLoader()
    docs = loader.load_all(target)
    assert len(docs) == NUM_PDFS
    assert all(d.pages for d in docs)
    assert all('filename' in d.metadata for d in docs)

    cleaner = TextCleaner()
    splitter = TokenSplitter(max_tokens=200, overlap_tokens=20)

    class _Embedder(Embedder):
        def __init__(self):
            self.calls = 0

        def embed(self, text: str):  # noqa: ANN001
            self.calls += 1
            return [1.0, 0.0, 0.0]

        async def aembed(self, text: str):  # noqa: ANN001
            return self.embed(text)

    embedder = _Embedder()
    store = EmbeddingDataStore(model_cls=_DummyModel)

    pipeline = DefaultIngestionPipeline(
        loader=PdfLoader(),
        cleaner=cleaner,
        splitter=splitter,
        embedder=embedder,
        store=store,
    )

    source = IngestionSource(object_class='PDF', object_id='batch-1', tags=['pdf'], metadata={})

    for doc in docs:
        pdf_path = target / doc.metadata['filename']
        with pdf_path.open('rb') as f:
            pipeline.run(f, filename=doc.metadata.get('filename'), tags=['batch'], source=source)

    assert store.model_cls.objects.saved, 'embeddings should be saved'
    assert all(getattr(o, 'tags', []) for o in store.model_cls.objects.saved)
    assert all(getattr(o, 'ml_metadata', {}).get('filename') for o in store.model_cls.objects.saved)

    rows = [
        RetrievalChunk(
            object_class='PDF',
            object_id='batch-1',
            chunk_index=0,
            raw_text='withdrawal charge schedule',
            distance=0.1,
            tags=['pdf', 'batch'],
            metadata={'filename': 'Aspida.pdf'},
        )
    ]
    retriever = _FakeRetriever(rows=rows)
    results = retriever.similarity_search('withdrawal charge')
    assert results[0].metadata['filename'] == 'Aspida.pdf'
