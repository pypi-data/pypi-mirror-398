from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class Embedder(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]: ...

    @abstractmethod
    async def aembed(self, text: str) -> list[float]: ...
