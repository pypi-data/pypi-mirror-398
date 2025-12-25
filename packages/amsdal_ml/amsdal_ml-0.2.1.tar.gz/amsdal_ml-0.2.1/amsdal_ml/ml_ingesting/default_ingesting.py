from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any
from typing import cast

from amsdal_ml.models.embedding_model import EmbeddingModel

from .embedding_data import EmbeddingData
from .ingesting import MLIngesting

logger = logging.getLogger(__name__)

# ---- constants (to avoid "magic values") -------------------------------------
_MIN_WORDS_PER_SENT = 4


class DepthLimitReached(str):
    def __str__(self) -> str:
        return 'Truncated due to reached depth limit'


@dataclass
class VisitedObject:
    obj: Any

    def __str__(self) -> str:
        return f'Recursion reference to object {self.obj}'


class MissingRelation(str):
    def __str__(self) -> str:
        return 'Relation not present'


class NoChildren(str):
    def __str__(self) -> str:
        return 'No nested data'


# UP007: use X | Y style
Marker = DepthLimitReached | VisitedObject | MissingRelation | NoChildren


class DefaultIngesting(MLIngesting):
    def __init__(
        self,
        *,
        max_depth: int = 2,
        max_chunks: int = 10,
        max_tokens_per_chunk: int = 800,
        tags: Iterable[str] | None = None,
        tags_fn: Callable[[], Iterable[str]] | None = None,
        atags_fn: Callable[[], Awaitable[Iterable[str]]] | None = None,
        token_len_fn: Callable[[str], int] | None = None,
        header_fn: Callable[[Any, list[str]], str] | None = None,
        facts_transform: Callable[[list[str | Marker]], list[str | Marker]] | None = None,
        afacts_transform: Callable[[list[str | Marker]], Awaitable[list[str | Marker]]] | None = None,
    ):
        self.max_depth = max_depth
        self.max_chunks = max_chunks
        self.max_tokens_per_chunk = max_tokens_per_chunk

        self._tags = list(tags or [])
        self._tags_fn = tags_fn
        self._atags_fn = atags_fn
        self._token_len_fn = token_len_fn or (lambda t: max(1, len(t) // 4))
        self._header_fn = header_fn or self._default_header

        self._facts_transform = facts_transform
        self._afacts_transform = afacts_transform

    def _default_header(self, instance: Any, facts: list[str]) -> str:
        doc = getattr(instance.__class__, '__doc__', '') or f'Instance of {instance.__class__.__name__}'
        return (doc.strip() + '\n\nKey facts:\n' + '\n'.join(facts)).strip()

    def _walk_sync(self, obj: Any, depth: int, visited: set[tuple[str, str]]) -> list[str | Marker]:
        if depth > self.max_depth:
            return [DepthLimitReached('')]
        key = (obj.__class__.__name__, str(getattr(obj, 'object_id', id(obj))))
        if key in visited:
            return [VisitedObject(obj)]
        visited.add(key)

        out: list[str | Marker] = []
        fields = getattr(obj.__class__, 'model_fields', {})
        for name, field in getattr(fields, 'items', lambda: [])():
            try:
                v = getattr(obj, name)
                title = getattr(field, 'title', None) or name.replace('_', ' ').capitalize()
                if v is None:
                    continue
                if isinstance(v, str | int | float | bool | date):
                    out.append(f'{title}: {v}')
                elif hasattr(v.__class__, 'model_fields'):
                    sub = self._walk_sync(v, depth + 1, visited)
                    out.append(f'{title} → {"; ".join(map(str, sub))}' if sub else str(NoChildren('')))
                elif isinstance(v, list):
                    simple = [str(x) for x in v if isinstance(x, str | int | float)]
                    if simple:
                        out.append(f'{title}: {", ".join(simple)}')
            except Exception as e:  # noqa: BLE001
                logger.warning(f'[walk_sync] field {name}: {e}')

        fks = getattr(obj.__class__, 'FOREIGN_KEYS', [])
        if not fks and not out:
            out.append(NoChildren(''))
        for fk in fks:
            try:
                rel = getattr(obj, fk, None)
                if rel is None:
                    out.append(MissingRelation(''))
                    continue
                if isinstance(rel, list):
                    for i, item in enumerate(rel):
                        if hasattr(item.__class__, 'model_fields'):
                            sub = self._walk_sync(item, depth + 1, visited)
                            out.append(f'{fk}[{i}] → {"; ".join(map(str, sub))}')
                elif hasattr(rel.__class__, 'model_fields'):
                    sub = self._walk_sync(rel, depth + 1, visited)
                    out.append(f'{fk} → {"; ".join(map(str, sub))}')
            except Exception as e:  # noqa: BLE001
                logger.warning(f'[walk_sync] FK {fk}: {e}')
        return out

    async def _walk_async(self, obj: Any, depth: int, visited: set[tuple[str, str]]) -> list[str | Marker]:
        if depth > self.max_depth:
            return [DepthLimitReached('')]
        key = (obj.__class__.__name__, str(getattr(obj, 'object_id', id(obj))))
        if key in visited:
            return [VisitedObject(obj)]
        visited.add(key)

        out: list[str | Marker] = []
        fields = getattr(obj.__class__, 'model_fields', {})
        for name, field in getattr(fields, 'items', lambda: [])():
            try:
                v = getattr(obj, name)
                if asyncio.iscoroutine(v):
                    v = await v
                title = getattr(field, 'title', None) or name.replace('_', ' ').capitalize()
                if v is None:
                    continue
                if isinstance(v, str | int | float | bool | date):
                    out.append(f'{title}: {v}')
                elif hasattr(v.__class__, 'model_fields'):
                    sub = await self._walk_async(v, depth + 1, visited)
                    out.append(f'{title} → {"; ".join(map(str, sub))}' if sub else str(NoChildren('')))
                elif isinstance(v, list):
                    simple = [str(x) for x in v if isinstance(x, str | int | float)]
                    if simple:
                        out.append(f'{title}: {", ".join(simple)}')
            except Exception as e:  # noqa: BLE001
                logger.warning(f'[walk_async] field {name}: {e}')

        fks = getattr(obj.__class__, 'FOREIGN_KEYS', [])
        if not fks and not out:
            out.append(NoChildren(''))
        for fk in fks:
            try:
                rel = getattr(obj, fk, None)
                if asyncio.iscoroutine(rel):
                    rel = await rel
                if rel is None:
                    out.append(MissingRelation(''))
                    continue
                if isinstance(rel, list):
                    for i, item in enumerate(rel):
                        if hasattr(item.__class__, 'model_fields'):
                            sub = await self._walk_async(item, depth + 1, visited)
                            out.append(f'{fk}[{i}] → {"; ".join(map(str, sub))}')
                elif hasattr(rel.__class__, 'model_fields'):
                    sub = await self._walk_async(rel, depth + 1, visited)
                    out.append(f'{fk} → {"; ".join(map(str, sub))}')
            except Exception as e:  # noqa: BLE001
                logger.warning(f'[walk_async] FK {fk}: {e}')
        return out

    def collect_facts(self, instance: Any) -> list[str | Marker]:
        """Return raw facts (strings and Markers) without stringification."""
        return self._walk_sync(instance, 0, set())

    async def acollect_facts(self, instance: Any) -> list[str | Marker]:
        """Async version of collect_facts()."""
        return await self._walk_async(instance, 0, set())

    def generate_text(self, instance: Any) -> str:
        raw: list[str | Marker] = self.collect_facts(instance)
        if self._facts_transform:
            raw = self._facts_transform(raw)
        facts = [str(x) for x in raw]
        return self._header_fn(instance, facts)

    async def agenerate_text(self, instance: Any) -> str:
        raw: list[str | Marker] = await self.acollect_facts(instance)
        if self._afacts_transform:
            raw = await self._afacts_transform(raw)
        elif self._facts_transform:
            raw = self._facts_transform(raw)
        facts = [str(x) for x in raw]
        return self._header_fn(instance, facts)

    def get_tags(self) -> list[str]:
        if self._tags_fn:
            return list(self._tags_fn())
        return list(self._tags)

    async def aget_tags(self) -> list[str]:
        if self._atags_fn:
            return list(await self._atags_fn())
        if self._tags_fn:
            return list(self._tags_fn())
        return list(self._tags)

    def _split(self, text: str, max_sentences: int = 7) -> list[str]:
        sents = re.split(r'(?<=[.!?])\s+', text.strip())
        sents = [s.strip() for s in sents if len(s.split()) >= _MIN_WORDS_PER_SENT]
        chunks: list[str] = []
        cur: list[str] = []
        for s in sents:
            proposal = (' '.join([*cur, s])).strip()
            if self._token_len_fn(proposal) <= self.max_tokens_per_chunk and len(cur) < max_sentences:
                cur.append(s)
            else:
                if cur:
                    ch = ' '.join(cur).strip()
                    if ch and not ch.endswith('.'):
                        ch += '.'
                    chunks.append(ch)
                cur = [s]
        if cur:
            ch = ' '.join(cur).strip()
            if ch and not ch.endswith('.'):
                ch += '.'
            chunks.append(ch)
        return chunks

    def _resolve_link(self, instance: Any) -> tuple[str, str]:
        cls = instance.__class__.__name__
        oid = getattr(instance, 'object_id', None)
        if oid is None:
            oid = str(getattr(instance, 'id', None) or id(instance))
        return cls, str(oid)

    def _make_records(self, chunks: list[str], vectors: list[list[float]], tags: list[str]) -> list[EmbeddingData]:
        out: list[EmbeddingData] = []
        for i, (t, v) in enumerate(zip(chunks[: self.max_chunks], vectors, strict=False)):
            out.append(EmbeddingData(chunk_index=i, raw_text=t, embedding=v, tags=tags))
        return out

    def generate_embeddings(
        self, instance: Any, embed_func: Callable[[str], list[float]] | None = None
    ) -> list[EmbeddingData]:
        if embed_func is None:
            msg = 'embed_func is required for DefaultIngesting.generate_embeddings'
            raise RuntimeError(msg)
        text = self.generate_text(instance)
        chunks = self._split(text)
        tags = self.get_tags()
        vectors = [embed_func(ch) for ch in chunks[: self.max_chunks]]
        return self._make_records(chunks, vectors, tags)

    async def agenerate_embeddings(
        self, instance: Any, embed_func: Callable[[str], Awaitable[list[float]]] | None = None
    ) -> list[EmbeddingData]:
        if embed_func is None:
            msg = 'embed_func is required for DefaultIngesting.agenerate_embeddings'
            raise RuntimeError(msg)
        text = await self.agenerate_text(instance)
        chunks = self._split(text)
        tags = await self.aget_tags()
        vectors: list[list[float]] = []
        for ch in chunks[: self.max_chunks]:
            vectors.append(await embed_func(ch))
        return self._make_records(chunks, vectors, tags)

    def save(self, records: Sequence[EmbeddingData], instance: Any):
        object_class, object_id = self._resolve_link(instance)
        objs = [
            EmbeddingModel(
                data_object_class=object_class,
                data_object_id=object_id,
                chunk_index=r.chunk_index,
                raw_text=r.raw_text,
                embedding=r.embedding,
                tags=r.tags,
            )
            for r in records
        ]
        manager = cast(Any, EmbeddingModel.objects)
        manager.bulk_create(objs)  # mypy: descriptor looks unbound without this cast
        return objs

    async def asave(self, records: Sequence[EmbeddingData], instance: Any):
        object_class, object_id = self._resolve_link(instance)
        objs = [
            EmbeddingModel(
                data_object_class=object_class,
                data_object_id=object_id,
                chunk_index=r.chunk_index,
                raw_text=r.raw_text,
                embedding=r.embedding,
                tags=r.tags,
            )
            for r in records
        ]
        manager = cast(Any, EmbeddingModel.objects)
        await manager.bulk_acreate(objs)  # ditto for async
        return objs
