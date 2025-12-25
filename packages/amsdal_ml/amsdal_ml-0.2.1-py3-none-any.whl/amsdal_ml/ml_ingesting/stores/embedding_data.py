from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from typing import cast

from amsdal_ml.ml_ingesting.embedding_data import EmbeddingData
from amsdal_ml.ml_ingesting.stores.store import EmbeddingStore
from amsdal_ml.ml_ingesting.types import IngestionSource
from amsdal_ml.models.embedding_model import EmbeddingModel


class EmbeddingDataStore(EmbeddingStore):
    def __init__(self, *, model_cls=EmbeddingModel) -> None:
        self.model_cls = model_cls

    def _merge_tags(self, base: list[str], extra: list[str]) -> list[str]:
        merged = list(base)
        for tag in extra:
            if tag not in merged:
                merged.append(tag)
        return merged

    def _build_objects(self, embeddings: Sequence[EmbeddingData], source: IngestionSource) -> list[Any]:
        base_tags = list(source.tags)
        base_meta = dict(source.metadata)
        objs = []
        for record in embeddings:
            tags = self._merge_tags(base_tags, list(record.tags))
            meta = dict(base_meta)
            meta.update(record.metadata or {})
            objs.append(
                self.model_cls(
                    data_object_class=source.object_class,
                    data_object_id=source.object_id,
                    chunk_index=record.chunk_index,
                    raw_text=record.raw_text,
                    embedding=record.embedding,
                    tags=tags,
                    ml_metadata=meta,
                )
            )
        return objs

    def save(self, embeddings: Sequence[EmbeddingData], *, source: IngestionSource | None = None) -> list[Any]:
        if source is None:
            msg = 'source is required to save embeddings'
            raise RuntimeError(msg)
        objs = self._build_objects(embeddings, source)
        manager = cast(Any, self.model_cls.objects)
        manager.bulk_create(objs)
        return objs

    async def asave(
        self, embeddings: Sequence[EmbeddingData], *, source: IngestionSource | None = None
    ) -> list[Any]:
        if source is None:
            msg = 'source is required to save embeddings'
            raise RuntimeError(msg)
        objs = self._build_objects(embeddings, source)
        manager = cast(Any, self.model_cls.objects)
        await manager.bulk_acreate(objs)
        return objs
