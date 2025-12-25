from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from amsdal_ml.ml_ingesting.types import LoadedDocument


class Cleaner(ABC):
    @abstractmethod
    def clean(self, doc: LoadedDocument) -> LoadedDocument: ...

    @abstractmethod
    async def aclean(self, doc: LoadedDocument) -> LoadedDocument: ...
