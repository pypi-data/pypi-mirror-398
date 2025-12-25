from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import IO
from typing import Any

from amsdal_ml.ml_ingesting.types import LoadedDocument


class Loader(ABC):
    @abstractmethod
    def load(
        self,
        file: IO[Any],
        *,
        filename: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LoadedDocument: ...

    @abstractmethod
    async def aload(
        self,
        file: IO[Any],
        *,
        filename: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LoadedDocument: ...
