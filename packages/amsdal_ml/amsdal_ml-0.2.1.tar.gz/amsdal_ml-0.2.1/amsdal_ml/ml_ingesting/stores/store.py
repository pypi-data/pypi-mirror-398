from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence
from typing import Any

from amsdal_ml.ml_ingesting.embedding_data import EmbeddingData
from amsdal_ml.ml_ingesting.types import IngestionSource


class EmbeddingStore(ABC):
    @abstractmethod
    def save(self, embeddings: Sequence[EmbeddingData], *, source: IngestionSource | None = None) -> list[Any]: ...

    @abstractmethod
    async def asave(
        self,
        embeddings: Sequence[EmbeddingData],
        *,
        source: IngestionSource | None = None,
    ) -> list[Any]: ...
