from __future__ import annotations

import asyncio
import re

from amsdal_ml.ml_ingesting.processors.cleaner import Cleaner
from amsdal_ml.ml_ingesting.types import LoadedDocument
from amsdal_ml.ml_ingesting.types import LoadedPage

_CONTROL_CHARS = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_MULTI_SPACE = re.compile(r'\s{2,}')


def _normalize_text(text: str) -> str:
    text = _CONTROL_CHARS.sub(' ', text)
    text = text.replace('\r', ' ').replace('\t', ' ')
    text = _MULTI_SPACE.sub(' ', text)
    return text.strip()


class TextCleaner(Cleaner):
    def __init__(self, *, drop_empty_pages: bool = True) -> None:
        self.drop_empty_pages = drop_empty_pages

    def clean(self, doc: LoadedDocument) -> LoadedDocument:
        pages: list[LoadedPage] = []
        for page in doc.pages:
            cleaned = _normalize_text(page.text)
            if not cleaned and self.drop_empty_pages:
                continue
            pages.append(
                LoadedPage(
                    page_number=page.page_number,
                    text=cleaned,
                    metadata=dict(page.metadata),
                )
            )
        meta = dict(doc.metadata)
        return LoadedDocument(pages=pages, metadata=meta)

    async def aclean(self, doc: LoadedDocument) -> LoadedDocument:
        return await asyncio.to_thread(self.clean, doc)
