from __future__ import annotations

import asyncio
from collections.abc import Callable

from amsdal_ml.ml_ingesting.splitters.splitter import Splitter
from amsdal_ml.ml_ingesting.types import LoadedDocument
from amsdal_ml.ml_ingesting.types import TextChunk


def _default_token_len(text: str) -> int:
    return max(1, len(text) // 4)


def _words_with_token_counts(text: str, token_fn: Callable[[str], int]) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for word in text.split():
        out.append((word, token_fn(word)))
    return out


def _compute_overlap_step(chunk: list[tuple[str, int]], overlap_tokens: int) -> int:
    tokens = 0
    step = 0
    for _word, tk in reversed(chunk):
        tokens += tk
        step += 1
        if tokens >= overlap_tokens:
            break
    return step


class TokenSplitter(Splitter):
    def __init__(
        self,
        *,
        max_tokens: int = 600,
        overlap_tokens: int = 50,
        token_len_fn: Callable[[str], int] = _default_token_len,
    ) -> None:
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.token_len_fn = token_len_fn

    def _split_page(self, text: str) -> list[str]:
        words = _words_with_token_counts(text, self.token_len_fn)
        chunks: list[str] = []
        start = 0
        n = len(words)
        while start < n:
            tokens = 0
            end = start
            while end < n and (tokens + words[end][1] <= self.max_tokens or tokens == 0):
                tokens += words[end][1]
                end += 1
            chunk_words = [w for w, _ in words[start:end]]
            chunk_text = ' '.join(chunk_words).strip()
            if chunk_text:
                chunks.append(chunk_text)
            if end >= n:
                break
            back = _compute_overlap_step(words[start:end], self.overlap_tokens)
            start = max(start + 1, end - back)
        return chunks

    def split(self, doc: LoadedDocument) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        for page in doc.pages:
            page_chunks = self._split_page(page.text)
            for chunk_text in page_chunks:
                metadata = dict(doc.metadata)
                metadata.update(page.metadata)
                metadata.setdefault('page_number', page.page_number)
                chunks.append(
                    TextChunk(
                        index=len(chunks),
                        text=chunk_text,
                        metadata=metadata,
                        tags=[],
                    )
                )
        return chunks

    async def asplit(self, doc: LoadedDocument) -> list[TextChunk]:
        return await asyncio.to_thread(self.split, doc)
