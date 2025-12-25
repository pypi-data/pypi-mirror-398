from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Awaitable
from collections.abc import Callable
from collections.abc import Sequence
from typing import Any
from typing import Protocol
from typing import TypeVar
from typing import runtime_checkable

from .embedding_data import EmbeddingData


@runtime_checkable
class SupportsSave(Protocol):
    def save(self) -> None: ...
    async def asave(self) -> None: ...


M = TypeVar('M', bound=SupportsSave)


class MLIngesting(ABC):
    @abstractmethod
    def generate_text(self, instance: Any) -> str: ...
    @abstractmethod
    async def agenerate_text(self, instance: Any) -> str: ...

    @abstractmethod
    def get_tags(self) -> list[str]: ...
    @abstractmethod
    async def aget_tags(self) -> list[str]: ...

    @abstractmethod
    def generate_embeddings(
        self,
        instance: Any,
        embed_func: Callable[[str], list[float]] | None = None,
    ) -> list[EmbeddingData]: ...
    @abstractmethod
    async def agenerate_embeddings(
        self,
        instance: Any,
        embed_func: Callable[[str], Awaitable[list[float]]] | None = None,
    ) -> list[EmbeddingData]: ...

    @abstractmethod
    def save(self, records: Sequence[EmbeddingData], instance: Any) -> list[EmbeddingData]: ...
    @abstractmethod
    async def asave(self, records: Sequence[EmbeddingData], instance: Any) -> list[EmbeddingData]: ...
