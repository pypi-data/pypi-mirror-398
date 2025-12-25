from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncIterator
from collections.abc import Iterator
from typing import Any
from typing import Literal
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from amsdal_ml.fileio.base_loader import FileAttachment


class AgentMessage(BaseModel):
    role: Literal['SYSTEM', 'USER', 'ASSISTANT']
    content: str


class AgentOutput(BaseModel):
    answer: str
    used_tools: list[str] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)


class Agent(ABC):
    @abstractmethod
    async def arun(
        self,
        user_query: str,
        *,
        attachments: Optional[list[FileAttachment]] = None,
    ) -> AgentOutput: ...

    @abstractmethod
    async def astream(
        self,
        user_query: str,
        *,
        attachments: Optional[list[FileAttachment]] = None,
    ) -> AsyncIterator[str]: ...

    def run(
        self,
        user_query: str,
        *,
        attachments: Optional[list[FileAttachment]] = None,
    ) -> AgentOutput:
        msg = 'This agent is async-only. Use arun().'
        raise NotImplementedError(msg)

    def stream(
        self,
        user_query: str,
        *,
        attachments: Optional[list[FileAttachment]] = None,
    ) -> Iterator[str]:
        msg = 'This agent is async-only. Use astream().'
        raise NotImplementedError(msg)
