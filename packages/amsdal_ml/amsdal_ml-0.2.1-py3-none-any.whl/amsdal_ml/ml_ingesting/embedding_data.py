from typing import Any

from pydantic import BaseModel
from pydantic import Field


class EmbeddingData(BaseModel):
    chunk_index: int = Field(..., title='Chunk index')
    raw_text: str = Field(..., title='Raw text used for embedding')
    embedding: list[float] = Field(..., title='Vector embedding')
    tags: list[str] = Field(default_factory=list, title='Embedding tags')
    metadata: dict[str, Any] = Field(default_factory=dict, title='Embedding metadata')
