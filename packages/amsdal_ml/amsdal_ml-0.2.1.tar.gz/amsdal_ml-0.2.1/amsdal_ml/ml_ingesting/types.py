from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import Field


class LoadedPage(BaseModel):
    page_number: int | None = Field(default=None, title='1-based page number if available')
    text: str = Field(..., min_length=1, title='Extracted page text')
    metadata: dict[str, Any] = Field(default_factory=dict, title='Page-level metadata')

    def as_text(self) -> str:
        return self.text


class LoadedDocument(BaseModel):
    pages: list[LoadedPage] = Field(default_factory=list, title='Pages in original order')
    metadata: dict[str, Any] = Field(default_factory=dict, title='Document-level metadata')

    def join(self, *, separator: str = '\n\n') -> str:
        return separator.join(page.text for page in self.pages)


class TextChunk(BaseModel):
    index: int = Field(..., title='Chunk order in document')
    text: str = Field(..., min_length=1, title='Chunk text destined for embedding')
    tags: list[str] = Field(default_factory=list, title='Tags to persist with embeddings')
    metadata: dict[str, Any] = Field(default_factory=dict, title='Arbitrary chunk metadata')


class IngestionSource(BaseModel):
    object_class: str = Field(..., title='Linked object class for embeddings')
    object_id: str = Field(..., title='Linked object ID for embeddings')
    tags: list[str] = Field(default_factory=list, title='Base tags applied to all chunks')
    metadata: dict[str, Any] = Field(default_factory=dict, title='Arbitrary source metadata')


__all__ = ['IngestionSource', 'LoadedDocument', 'LoadedPage', 'TextChunk']
