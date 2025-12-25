from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Iterable
from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class Document(BaseModel):
    page_content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Retriever(ABC):
    @abstractmethod
    async def invoke(self, query: str) -> list[Document]: ...


class RetrievalChunk(BaseModel):
    object_class: str = Field(...)
    object_id: str = Field(...)
    chunk_index: int = Field(...)
    raw_text: str = Field(...)
    distance: float = Field(...)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MLRetriever(ABC):
    @abstractmethod
    def similarity_search(
        self,
        query: str,
        *,
        k: int = 8,
        include_tags: Optional[Iterable[str]] = None,
        exclude_tags: Optional[Iterable[str]] = None,
    ) -> list[RetrievalChunk]: ...

    @abstractmethod
    async def asimilarity_search(
        self,
        query: str,
        *,
        k: int = 8,
        include_tags: Optional[Iterable[str]] = None,
        exclude_tags: Optional[Iterable[str]] = None,
    ) -> list[RetrievalChunk]: ...
