from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path

from amsdal_ml.ml_ingesting.loaders.loader import Loader
from amsdal_ml.ml_ingesting.loaders.pdf_loader import PdfLoader
from amsdal_ml.ml_ingesting.types import IngestionSource
from amsdal_ml.ml_ingesting.types import LoadedDocument


class FolderLoader:
    """Generic folder loader that delegates file parsing to a Loader."""

    def __init__(self, *, loader: Loader) -> None:
        self.loader = loader

    def _iter_paths(self, folder: Path) -> Iterator[Path]:
        for path in folder.rglob('*'):
            if path.is_file() and self._accepts(path):
                yield path

    def _accepts(self, _path: Path) -> bool:
        return True

    def _load_path(self, path: Path, *, source: IngestionSource | None) -> LoadedDocument:
        with path.open('rb') as f:
            doc = self.loader.load(f, filename=path.name, metadata=(source.metadata if source else None))
            doc.metadata.setdefault('filename', path.name)
            doc.metadata.setdefault('path', str(path))
            return doc

    def load_all(self, folder: str | Path, *, source: IngestionSource | None = None) -> list[LoadedDocument]:
        root = Path(folder)
        docs: list[LoadedDocument] = []
        for path in self._iter_paths(root):
            docs.append(self._load_path(path, source=source))
        return docs

    async def aload_all(self, folder: str | Path, *, source: IngestionSource | None = None) -> list[LoadedDocument]:
        root = Path(folder)
        tasks = [asyncio.to_thread(self._load_path, path, source=source) for path in self._iter_paths(root)]
        return await asyncio.gather(*tasks)


class PdfFolderLoader(FolderLoader):
    def __init__(self, *, pdf_loader: Loader | None = None) -> None:
        super().__init__(loader=pdf_loader or PdfLoader())

    def _accepts(self, path: Path) -> bool:
        return path.suffix.lower() == '.pdf'
