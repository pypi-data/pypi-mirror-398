from __future__ import annotations

from collections.abc import Iterable
from typing import IO
from typing import Any
from typing import Generic
from typing import TypeVar

from amsdal_ml.ml_ingesting.embedders.embedder import Embedder
from amsdal_ml.ml_ingesting.embedding_data import EmbeddingData
from amsdal_ml.ml_ingesting.loaders.loader import Loader
from amsdal_ml.ml_ingesting.pipeline_interface import IngestionPipeline
from amsdal_ml.ml_ingesting.processors.cleaner import Cleaner
from amsdal_ml.ml_ingesting.splitters.splitter import Splitter
from amsdal_ml.ml_ingesting.stores.store import EmbeddingStore
from amsdal_ml.ml_ingesting.types import IngestionSource
from amsdal_ml.ml_ingesting.types import LoadedDocument

LoaderT = TypeVar('LoaderT', bound=Loader)


class DefaultIngestionPipeline(IngestionPipeline, Generic[LoaderT]):
    loader: LoaderT

    def __init__(
        self,
        *,
        loader: LoaderT,
        cleaner: Cleaner,
        splitter: Splitter,
        embedder: Embedder,
        store: EmbeddingStore,
    ) -> None:
        self.loader = loader
        self.cleaner = cleaner
        self.splitter = splitter
        self.embedder = embedder
        self.store = store

    def _combine_tags(self, base: Iterable[str] | None, extra: Iterable[str] | None) -> list[str]:
        out: list[str] = []
        for tag in list(base or []) + list(extra or []):
            if tag not in out:
                out.append(tag)
        return out

    def _ensure_source(self, source: IngestionSource | None) -> IngestionSource:
        if source is None:
            msg = 'source is required for ingestion pipeline'
            raise RuntimeError(msg)
        return source

    def _merge_metadata(
        self,
        source_meta: dict[str, Any],
        doc_meta: dict[str, Any],
        filename: str | None = None,
    ) -> dict[str, Any]:
        merged = {**source_meta, **doc_meta}
        if filename and 'filename' not in merged:
            merged['filename'] = filename
        return merged

    def _embed_chunks(self, chunks, tags: list[str], base_metadata: dict[str, Any]) -> list[EmbeddingData]:
        embeddings: list[EmbeddingData] = []
        for idx, chunk in enumerate(chunks):
            vector = self.embedder.embed(chunk.text)
            merged_tags = self._combine_tags(tags, chunk.tags)
            metadata = {**base_metadata, **dict(chunk.metadata)}
            embeddings.append(
                EmbeddingData(
                    chunk_index=idx,
                    raw_text=chunk.text,
                    embedding=vector,
                    tags=merged_tags,
                    metadata=metadata,
                )
            )
        return embeddings

    async def _aembed_chunks(self, chunks, tags: list[str], base_metadata: dict[str, Any]) -> list[EmbeddingData]:
        embeddings: list[EmbeddingData] = []
        for idx, chunk in enumerate(chunks):
            vector = await self.embedder.aembed(chunk.text)
            merged_tags = self._combine_tags(tags, chunk.tags)
            metadata = {**base_metadata, **dict(chunk.metadata)}
            embeddings.append(
                EmbeddingData(
                    chunk_index=idx,
                    raw_text=chunk.text,
                    embedding=vector,
                    tags=merged_tags,
                    metadata=metadata,
                )
            )
        return embeddings

    def run(
        self,
        file: IO[Any],
        *,
        filename: str | None = None,
        tags: Iterable[str] | None = None,
        source: IngestionSource | None = None,
    ) -> list[Any]:
        src = self._ensure_source(source)
        doc = self.loader.load(file, filename=filename, metadata=src.metadata)
        base_metadata = self._merge_metadata(src.metadata, doc.metadata, filename)
        cleaned = self.cleaner.clean(LoadedDocument(pages=doc.pages, metadata=base_metadata))
        chunks = self.splitter.split(cleaned)
        merged_tags = self._combine_tags(src.tags, tags)
        embeddings = self._embed_chunks(chunks, merged_tags, base_metadata)
        return self.store.save(embeddings, source=src)

    async def arun(
        self,
        file: IO[Any],
        *,
        filename: str | None = None,
        tags: Iterable[str] | None = None,
        source: IngestionSource | None = None,
    ) -> list[Any]:
        src = self._ensure_source(source)
        doc = await self.loader.aload(file, filename=filename, metadata=src.metadata)
        base_metadata = self._merge_metadata(src.metadata, doc.metadata, filename)
        cleaned = await self.cleaner.aclean(LoadedDocument(pages=doc.pages, metadata=base_metadata))
        chunks = await self.splitter.asplit(cleaned)
        merged_tags = self._combine_tags(src.tags, tags)
        embeddings = await self._aembed_chunks(chunks, merged_tags, base_metadata)
        return await self.store.asave(embeddings, source=src)

