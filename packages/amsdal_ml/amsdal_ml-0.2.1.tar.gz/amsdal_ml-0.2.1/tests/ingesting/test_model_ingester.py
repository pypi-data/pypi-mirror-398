from __future__ import annotations

import asyncio
import io
from typing import Any
from typing import ClassVar

from amsdal.models.core.file import File

from amsdal_ml.ml_ingesting import ModelIngester
from amsdal_ml.ml_ingesting.loaders.pdf_loader import PdfLoader
from amsdal_ml.ml_ingesting.loaders.text_loader import TextLoader
from amsdal_ml.ml_ingesting.pipeline_interface import IngestionPipeline

EXPECTED_PDF_COUNT = 2


class _FakeFile(File):
    def __init__(self, filename: str, data: bytes = b'%PDF-1.4 test') -> None:
        super().__init__(filename=filename)
        self.data = data

    def open(self, mode: str = 'rb'):  # noqa: ARG002
        return io.BytesIO(self.data or b'')

    def read_bytes(self) -> bytes:
        return self.data or b''

    async def aread_bytes(self) -> bytes:
        return self.data or b''


class _Field:
    def __init__(self, title: str | None = None) -> None:
        self.title = title
        self.annotation = File


class _FakeModel:
    model_fields: ClassVar[dict[str, Any]] = {
        'brochure_file': _Field('Brochure'),
        'contract_file': _Field('Contract'),
        'notes': _Field('Notes'),
    }

    def __init__(self) -> None:
        self.object_id = 'obj-1'
        self.brochure_file = _FakeFile('brochure.pdf')
        self.contract_file = _FakeFile('contract.pdf')
        self.notes = _FakeFile('notes.txt', data=b'text data')


class _Pipeline(IngestionPipeline):
    def __init__(self, loader=None):
        self.calls: list[dict[str, Any]] = []
        self.loader = loader

    def run(self, file, *, filename=None, tags=None, source=None):  # noqa: ANN001
        content = file.read()
        if self.loader and isinstance(self.loader, PdfLoader) and not content.startswith(b'%PDF'):
            return []
        payload = {
            'filename': filename,
            'tags': list(tags or []),
            'source': source,
            'content': content,
        }
        self.calls.append(payload)
        return [payload]

    async def arun(self, file, *, filename=None, tags=None, source=None):  # noqa: ANN001
        return self.run(file, filename=filename, tags=tags, source=source)


def test_model_ingester_ingests_pdf_fields_by_default():
    pipeline = _Pipeline(loader=PdfLoader())
    ingester = ModelIngester(
        pipeline=pipeline,  # type: ignore[arg-type]
        base_tags=['base'],
        base_metadata={'kind': 'product'}
    )  # type: ignore[var-annotated]

    model = _FakeModel()
    result = ingester.ingest([model])

    assert len(result) == EXPECTED_PDF_COUNT
    filenames = {call['filename'] for call in pipeline.calls}
    assert filenames == {'brochure.pdf', 'contract.pdf'}

    for call in pipeline.calls:
        assert call['source'].object_class == _FakeModel.__name__
        assert call['source'].object_id == 'obj-1'
        assert call['source'].tags == ['base']
        assert call['source'].metadata['kind'] == 'product'
        assert call['source'].metadata['field'] in {'brochure_file', 'contract_file'}
        assert 'file' in call['tags']
        assert f"field:{call['source'].metadata['field']}" in call['tags']


def test_model_ingester_respects_fields_and_skips_non_pdf():
    pipeline = _Pipeline(loader=PdfLoader())
    ingester = ModelIngester(pipeline=pipeline)  # type: ignore[arg-type,var-annotated]

    model = _FakeModel()
    result = ingester.ingest([model], fields=['contract_file'])

    assert len(result) == 1
    assert pipeline.calls[0]['filename'] == 'contract.pdf'
    assert pipeline.calls[0]['source'].metadata['field'] == 'contract_file'
    assert 'field:contract_file' in pipeline.calls[0]['tags']
    result = ingester.ingest([model], fields=['notes'])
    assert result == []


def test_model_ingester_async_path():
    pipeline = _Pipeline(loader=PdfLoader())
    ingester = ModelIngester(pipeline=pipeline, base_tags=['base'])  # type: ignore[arg-type,var-annotated]
    model = _FakeModel()

    result = asyncio.run(ingester.aingest([model], tags=['extra']))

    assert len(result) == EXPECTED_PDF_COUNT
    for call in pipeline.calls:
        assert 'extra' in call['tags']
        assert 'file' in call['tags']
        assert call['source'].tags == ['base']


def test_model_ingester_with_text_loader():
    pipeline = _Pipeline(loader=TextLoader())
    ingester = ModelIngester(pipeline=pipeline, base_tags=['text'])  # type: ignore[arg-type,var-annotated]

    model = _FakeModel()
    result = ingester.ingest([model], fields=['notes'])

    assert len(result) == 1
    assert pipeline.calls[0]['filename'] == 'notes.txt'
    assert pipeline.calls[0]['source'].metadata['field'] == 'notes'
    assert 'file' in pipeline.calls[0]['tags']
    assert 'field:notes' in pipeline.calls[0]['tags']
