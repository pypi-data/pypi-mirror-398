from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncIterator
from typing import Any
from typing import Required
from typing import TypedDict

from amsdal_ml.fileio.base_loader import PLAIN_TEXT
from amsdal_ml.fileio.base_loader import FileAttachment
from amsdal_ml.ml_models.utils import ResponseFormat


class StructuredMessage(TypedDict, total=False):
    """Base structure for a message in LLM conversations.

    Attributes:
        role: The role of the message sender (e.g., 'user', 'assistant', 'system').
        content: The content of the message, can be str or list of multimodal parts.
        tool_call_id: ID of the tool call (for tool messages).
        name: Name of the tool (for tool messages).
    """
    role: Required[str]
    content: Required[Any]
    tool_call_id: str
    name: str


LLModelInput = str | list[StructuredMessage]


class ModelError(Exception):
    """Base exception for all ML models."""


class ModelConnectionError(ModelError):
    """Network or connection failure to the provider (timeouts, DNS, TLS, etc.)."""


class ModelRateLimitError(ModelError):
    """Provider's rate limit reached (HTTP 429)."""


class ModelAPIError(ModelError):
    """API responded with an error (any 4xx/5xx, except 429)."""


class MLModel(ABC):
    @property
    @abstractmethod
    def supported_formats(self) -> set[ResponseFormat]:
        """Return a set of supported response formats for this model."""
        raise NotImplementedError

    @abstractmethod
    def setup(self) -> None:
        """Initialize any clients or resources needed before inference."""
        raise NotImplementedError

    @abstractmethod
    def teardown(self) -> None:
        """Clean up resources after use."""
        raise NotImplementedError

    def supported_attachments(self) -> set[str]:
        """Return a set of universal attachment kinds, e.g. {PLAIN_TEXT, FILE_ID}."""
        return {PLAIN_TEXT}

    @property
    @abstractmethod
    def input_role(self) -> str:
        """Return the role for user input messages."""
        raise NotImplementedError

    @property
    @abstractmethod
    def output_role(self) -> str:
        """Return the role for model output messages."""
        raise NotImplementedError

    @property
    @abstractmethod
    def tool_role(self) -> str:
        """Return the role for tool result messages."""
        raise NotImplementedError

    @property
    @abstractmethod
    def system_role(self) -> str:
        """Return the role for system messages."""
        raise NotImplementedError

    @property
    @abstractmethod
    def content_field(self) -> str:
        """Return the field name for message content (e.g., 'content' for OpenAI, 'parts' for Gemini)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def role_field(self) -> str:
        """Return the field name for message role (e.g., 'role' for most models)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def tool_call_id_field(self) -> str:
        """Return the field name for tool call ID (e.g., 'tool_call_id' for OpenAI)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def tool_name_field(self) -> str:
        """Return the field name for tool name (e.g., 'name' for OpenAI)."""
        raise NotImplementedError

    @abstractmethod
    def invoke(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        attachments: list[FileAttachment] | None = None,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> str:
        """Run synchronous inference with the model."""
        raise NotImplementedError

    @abstractmethod
    async def ainvoke(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        attachments: list[FileAttachment] | None = None,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> str:
        """Run asynchronous inference with the model."""
        raise NotImplementedError

    @abstractmethod
    def stream(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        attachments: list[FileAttachment] | None = None,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ):
        """Stream synchronous inference results from the model."""
        raise NotImplementedError

    @abstractmethod
    def astream(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        attachments: list[FileAttachment] | None = None,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream asynchronous inference results as an async generator.

        Subclasses should implement this like:

            async def astream(... ) -> AsyncIterator[str]:
                yield "chunk"
        """
        raise NotImplementedError
