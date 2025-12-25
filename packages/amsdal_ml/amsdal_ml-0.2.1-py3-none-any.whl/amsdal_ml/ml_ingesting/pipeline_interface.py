from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Iterable
from typing import IO
from typing import Any

from amsdal_ml.ml_ingesting.types import IngestionSource


class IngestionPipeline(ABC):
    @abstractmethod
    def run(
        self,
        file: IO[Any],
        *,
        filename: str | None = None,
        tags: Iterable[str] | None = None,
        source: IngestionSource | None = None,
    ) -> list[Any]: ...

    @abstractmethod
    async def arun(
        self,
        file: IO[Any],
        *,
        filename: str | None = None,
        tags: Iterable[str] | None = None,
        source: IngestionSource | None = None,
    ) -> list[Any]: ...
