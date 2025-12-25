from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any
from typing import BinaryIO
from typing import Optional

from pydantic import BaseModel

PLAIN_TEXT = 'plain_text'
FILE_ID = 'file_id'


class FileData(BaseModel):
    name: str
    size: int | None = None
    mime: Optional[str] = None


@dataclass
class FileAttachment:
    type: str  # one of: PLAIN_TEXT, FILE_ID
    content: Any
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FileItem:
    file: BinaryIO
    filename: str | None = None
    filedata: FileData | None = None

    @staticmethod
    def from_path(path: str, *, filedata: FileData | None = None) -> FileItem:
        # Caller is responsible for lifecycle; loaders may close after upload.
        f = open(path, 'rb')
        return FileItem(file=f, filename=path.split('/')[-1], filedata=filedata)

    @staticmethod
    def from_bytes(data: bytes, *, filename: str | None = None, filedata: FileData | None = None) -> FileItem:
        import io

        return FileItem(file=io.BytesIO(data), filename=filename, filedata=filedata)

    @staticmethod
    def from_str(text: str, *, filename: str | None = None, filedata: FileData | None = None) -> FileItem:
        import io

        return FileItem(file=io.BytesIO(text.encode('utf-8')), filename=filename, filedata=filedata)


class BaseFileLoader(ABC):
    @abstractmethod
    async def load(self, item: FileItem) -> FileAttachment:
        """Upload a single file and return an attachment reference."""

    @abstractmethod
    async def load_batch(self, items: list[FileItem]) -> list[FileAttachment]:
        """Upload multiple files; input and output are lists for simplicity."""
