from __future__ import annotations

import asyncio
from typing import IO
from typing import Any

from amsdal_ml.ml_ingesting.loaders.loader import Loader
from amsdal_ml.ml_ingesting.types import LoadedDocument
from amsdal_ml.ml_ingesting.types import LoadedPage


class TextLoader(Loader):
    def __init__(self, *, encoding: str = 'utf-8', errors: str = 'ignore') -> None:
        self.encoding = encoding
        self.errors = errors

    def _read_text(self, file: IO[Any]) -> str:
        data = file.read()
        if isinstance(data, bytes):
            return data.decode(self.encoding, errors=self.errors)
        return str(data)

    def load(
        self,
        file: IO[Any],
        *,
        filename: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LoadedDocument:
        text = self._read_text(file)
        doc_meta = dict(metadata or {})
        if filename:
            doc_meta.setdefault('filename', filename)
        page = LoadedPage(page_number=None, text=text, metadata={})
        return LoadedDocument(pages=[page], metadata=doc_meta)

    async def aload(
        self,
        file: IO[Any],
        *,
        filename: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LoadedDocument:
        return await asyncio.to_thread(self.load, file, filename=filename, metadata=metadata)
