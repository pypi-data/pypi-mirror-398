from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from amsdal_ml.ml_ingesting.types import LoadedDocument
from amsdal_ml.ml_ingesting.types import TextChunk


class Splitter(ABC):
    @abstractmethod
    def split(self, doc: LoadedDocument) -> list[TextChunk]: ...

    @abstractmethod
    async def asplit(self, doc: LoadedDocument) -> list[TextChunk]: ...
