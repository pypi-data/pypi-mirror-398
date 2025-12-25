from __future__ import annotations

import math
from abc import ABC
from abc import abstractmethod

from amsdal_models.classes.annotations import CosineDistance

from amsdal_ml.ml_ingesting.embedders.embedder import Embedder
from amsdal_ml.models.embedding_model import EmbeddingModel

from .retriever import MLRetriever
from .retriever import RetrievalChunk


def _default_num_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class DefaultRetriever(MLRetriever, ABC):
    def __init__(
        self,
        *,
        embedding_model_cls=EmbeddingModel,
        max_context_tokens: int = 1800,
        num_tokens_fn=_default_num_tokens,
        embedder: Embedder | None = None,
    ):
        self.embedding_model_cls = embedding_model_cls
        self.max_context_tokens = max_context_tokens
        self.num_tokens_fn = num_tokens_fn
        self.embedder = embedder

    @abstractmethod
    def _embed_query(self, text: str) -> list[float]: ...

    @abstractmethod
    async def _aembed_query(self, text: str) -> list[float]: ...

    def _filter_rows_by_tags(self, rows, include_tags, exclude_tags):
        if not include_tags and not exclude_tags:
            return rows
        inc = set(include_tags or [])
        exc = set(exclude_tags or [])
        out = []
        for r in rows:
            tags = set(r.tags or [])
            if inc and not inc.issubset(tags):
                continue
            if exc and (exc & tags):
                continue
            out.append(r)
        return out

    def similarity_search(self, query: str, *, k=8, include_tags=None, exclude_tags=None) -> list[RetrievalChunk]:
        vec = self._embed_query(query)
        qs = (
            self.embedding_model_cls.objects.all()
            .annotate(distance=CosineDistance('embedding', vec))
            .order_by('distance')
        )

        pre = max(k * 5, 100)
        rows = list(qs[:pre].execute())

        rows = self._filter_rows_by_tags(rows, include_tags, exclude_tags)
        rows = rows[:k]

        return [
            RetrievalChunk(
                object_class=r.data_object_class,
                object_id=r.data_object_id,
                chunk_index=r.chunk_index,
                raw_text=(r.raw_text or '').strip(),
                distance=float(getattr(r, 'distance', math.inf)),
                tags=list(r.tags or []),
                metadata=dict(getattr(r, 'ml_metadata', {}) or {}),
            )
            for r in rows
        ]

    async def asimilarity_search(
        self,
        query: str,
        *,
        k=8,
        include_tags=None,
        exclude_tags=None,
    ) -> list[RetrievalChunk]:
        vec = await self._aembed_query(query)
        qs = (
            self.embedding_model_cls.objects.all()
            .annotate(distance=CosineDistance('embedding', vec))
            .order_by('distance')
        )

        pre = max(k * 5, 100)
        rows = await qs.aexecute()
        rows = rows[:pre]

        rows = self._filter_rows_by_tags(rows, include_tags, exclude_tags)
        rows = rows[:k]

        return [
            RetrievalChunk(
                object_class=r.data_object_class,
                object_id=r.data_object_id,
                chunk_index=r.chunk_index,
                raw_text=(r.raw_text or '').strip(),
                distance=float(getattr(r, 'distance', math.inf)),
                tags=list(r.tags or []),
                metadata=dict(getattr(r, 'ml_metadata', {}) or {}),
            )
            for r in rows
        ]
