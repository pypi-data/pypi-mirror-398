from __future__ import annotations

import asyncio
import io
import logging
from collections.abc import Sequence
from typing import Any
from typing import BinaryIO
from typing import Literal

from openai import AsyncOpenAI

from amsdal_ml.fileio.base_loader import FILE_ID
from amsdal_ml.fileio.base_loader import BaseFileLoader
from amsdal_ml.fileio.base_loader import FileAttachment
from amsdal_ml.fileio.base_loader import FileData
from amsdal_ml.fileio.base_loader import FileItem

logger = logging.getLogger(__name__)

AllowedPurpose = Literal['assistants', 'batch', 'fine-tune', 'vision', 'user_data', 'evals']


class OpenAIFileLoader(BaseFileLoader):
    """
    Loader which uploads files into OpenAI Files API and returns openai_file_id.
    """

    def __init__(self, client: AsyncOpenAI, *, purpose: AllowedPurpose = 'assistants') -> None:
        self.client = client
        self.purpose: AllowedPurpose = purpose  # mypy: Literal union, matches SDK

    async def _upload_one(self, file: BinaryIO, *, filename: str | None, filedata: FileData | None) -> FileAttachment:
        try:
            if hasattr(file, 'seek'):
                file.seek(0)
        except Exception as exc:  # pragma: no cover
            logger.debug('seek(0) failed for %r: %s', filename or file, exc)

        buf = file if isinstance(file, io.BytesIO) else io.BytesIO(file.read())

        up = await self.client.files.create(file=(filename or 'upload.bin', buf), purpose=self.purpose)

        meta: dict[str, Any] = {
            'filename': filename,
            'provider': 'openai',
            'file': {
                'id': up.id,
                'bytes': getattr(up, 'bytes', None),
                'purpose': getattr(up, 'purpose', self.purpose),
                'created_at': getattr(up, 'created_at', None),
                'status': getattr(up, 'status', None),
                'status_details': getattr(up, 'status_details', None),
            },
        }
        if filedata is not None:
            meta['filedata'] = filedata.model_dump()

        return FileAttachment(type=FILE_ID, content=up.id, metadata=meta)

    async def load(self, item: FileItem) -> FileAttachment:
        return await self._upload_one(item.file, filename=item.filename, filedata=item.filedata)

    async def load_batch(self, items: Sequence[FileItem]) -> list[FileAttachment]:
        tasks = [
            asyncio.create_task(self._upload_one(it.file, filename=it.filename, filedata=it.filedata)) for it in items
        ]
        return await asyncio.gather(*tasks)
