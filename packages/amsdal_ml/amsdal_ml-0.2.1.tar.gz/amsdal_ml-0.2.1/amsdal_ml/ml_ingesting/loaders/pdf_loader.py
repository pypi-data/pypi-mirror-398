from __future__ import annotations

import asyncio
import logging
from typing import IO
from typing import Any

import pymupdf  # type: ignore

from amsdal_ml.ml_ingesting.loaders.loader import Loader
from amsdal_ml.ml_ingesting.types import LoadedDocument
from amsdal_ml.ml_ingesting.types import LoadedPage


def _merge_spaced_characters(text: str) -> str:
    """Collapse sequences like "s h o r t - t e r m" into "short-term".

    Some PDFs return every character as a separate token. We merge contiguous
    single-character tokens (letters/digits and simple inline punctuation) so
    downstream cleaning does not preserve the artificial spaces.
    """

    tokens = text.replace("\n", " ").split()
    merged: list[str] = []
    buffer = ""

    def flush_buffer() -> None:
        nonlocal buffer
        if buffer:
            merged.append(buffer)
            buffer = ""

    for tok in tokens:
        if len(tok) == 1 and (tok.isalnum() or tok in {"'", "-", "&"}):
            buffer += tok
            continue
        flush_buffer()
        merged.append(tok)

    flush_buffer()
    return " ".join(merged)


def _is_noise(
    text: str,
    *,
    min_tokens: int = 20,
    single_char_ratio: float = 0.6,
    single_char_min_count: int = 5,
) -> bool:
    """Heuristic: drop text dominated by single-character tokens.

    We treat as noise when:
    - Most tokens are single characters (ratio >= single_char_ratio), AND
      either the sample is long enough (>= min_tokens) or we have at least a
      few single-character tokens (>= single_char_min_count) even in short text.
    """

    tokens = text.split()
    if not tokens:
        return True

    single_chars = sum(1 for t in tokens if len(t) == 1)
    ratio = single_chars / len(tokens)

    if ratio < single_char_ratio:
        return False

    return len(tokens) >= min_tokens or single_chars >= single_char_min_count


class PdfLoader(Loader):
    def __init__(self, *, extract_metadata: bool = True) -> None:
        self.extract_metadata = extract_metadata
        self.logger = logging.getLogger(__name__)

    def _read_sync(
        self,
        file: IO[Any],
        filename: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> LoadedDocument:
        peek = file.read(4)
        file.seek(0)
        if not (isinstance(peek, bytes) and peek.startswith(b"%PDF")):
            msg = "Not a PDF file"
            raise ValueError(msg)

        data = file.read()

        with pymupdf.open(stream=data, filetype="pdf") as doc:
            pages: list[LoadedPage] = []
            for idx, page in enumerate(doc):
                text_raw = page.get_text("text") or ''
                text = _merge_spaced_characters(text_raw)
                if not text:
                    continue
                if _is_noise(text):
                    self.logger.debug("Skipping page %s as noise (single-char heavy)", idx + 1)
                    continue
                pages.append(
                    LoadedPage(
                        page_number=idx + 1,
                        text=text,
                        metadata={'page_number': idx + 1},
                    )
                )

            doc_meta: dict[str, Any] = {}
            if self.extract_metadata:
                raw_meta = doc.metadata or {}
                for key, value in raw_meta.items():
                    if value is None:
                        continue
                    doc_meta[str(key)] = str(value)

            if metadata:
                doc_meta.update(metadata)
            if filename:
                doc_meta.setdefault('filename', filename)

            return LoadedDocument(pages=pages, metadata=doc_meta)

    def load(
        self,
        file: IO[Any],
        *,
        filename: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> LoadedDocument:
        return self._read_sync(file, filename=filename, metadata=metadata)

    async def aload(
        self, file: IO[Any], *, filename: str | None = None, metadata: dict[str, Any] | None = None
    ) -> LoadedDocument:
        return await asyncio.to_thread(self._read_sync, file, filename, metadata)
