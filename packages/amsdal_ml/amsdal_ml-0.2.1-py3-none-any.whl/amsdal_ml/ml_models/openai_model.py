from __future__ import annotations

import asyncio
import os
import warnings
from collections.abc import AsyncIterator
from collections.abc import Iterator
from collections.abc import Sequence
from typing import Any
from typing import Optional
from typing import cast

import openai
from openai import AsyncOpenAI
from openai import AsyncStream
from openai import OpenAI
from openai import Stream

from amsdal_ml.fileio.base_loader import FILE_ID
from amsdal_ml.fileio.base_loader import PLAIN_TEXT
from amsdal_ml.fileio.base_loader import FileAttachment
from amsdal_ml.ml_config import ml_config
from amsdal_ml.ml_models.models import LLModelInput
from amsdal_ml.ml_models.models import MLModel
from amsdal_ml.ml_models.models import ModelAPIError
from amsdal_ml.ml_models.models import ModelConnectionError
from amsdal_ml.ml_models.models import ModelError
from amsdal_ml.ml_models.models import ModelRateLimitError
from amsdal_ml.ml_models.models import StructuredMessage
from amsdal_ml.ml_models.utils import ResponseFormat


class OpenAIModel(MLModel):
    """OpenAI LLM wrapper using a single Responses API pathway for all modes."""

    def __init__(
        self,
        *,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> None:
        self.client: Optional[OpenAI | AsyncOpenAI] = None
        self.async_mode: bool = bool(ml_config.async_mode)
        self.model_name: str = model_name or ml_config.llm_model_name
        self.temperature: float = (
            temperature if temperature is not None else ml_config.llm_temperature
        )
        self._api_key: Optional[str] = None

    @property
    def supported_formats(self) -> set[ResponseFormat]:
        """OpenAI supports PLAIN_TEXT, JSON_OBJECT and JSON_SCHEMA formats."""
        return {
            ResponseFormat.PLAIN_TEXT,
            ResponseFormat.JSON_OBJECT,
            ResponseFormat.JSON_SCHEMA,
        }

    @property
    def input_role(self) -> str:
        """Return 'user' for OpenAI."""
        return "user"

    @property
    def output_role(self) -> str:
        """Return 'assistant' for OpenAI."""
        return "assistant"

    @property
    def tool_role(self) -> str:
        """Return 'tool' for OpenAI."""
        return "tool"

    @property
    def system_role(self) -> str:
        """Return 'system' for OpenAI."""
        return "system"

    @property
    def content_field(self) -> str:
        """Return 'content' for OpenAI."""
        return "content"

    @property
    def role_field(self) -> str:
        """Return 'role' for OpenAI."""
        return "role"

    @property
    def tool_call_id_field(self) -> str:
        """Return 'tool_call_id' for OpenAI."""
        return "tool_call_id"

    @property
    def tool_name_field(self) -> str:
        """Return 'name' for OpenAI."""
        return "name"

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
        if self.async_mode:
            msg = "Async mode is enabled. Use 'ainvoke' instead."
            raise RuntimeError(msg)
        if not isinstance(self.client, OpenAI):
            msg = "Sync client is not initialized. Call setup() first."
            raise RuntimeError(msg)

        atts = self._validate_attachments(attachments)
        api_response_format = self._map_response_format(response_format, schema)

        if self._has_file_ids(atts):
            input_content = self._build_input_content(input, atts)
            return self._call_responses(
                input_content, response_format=api_response_format
            )

        if isinstance(input, str):
            final_prompt = self._merge_plain_text(input, atts)
            return self._call_chat(
                [{"role": "user", "content": final_prompt}],
                response_format=api_response_format,
                tools=tools,
                tool_choice=tool_choice,
            )

        messages = list(input)
        attachments_text = self._merge_plain_text("", atts)
        if attachments_text:
            messages.append({"role": "user", "content": attachments_text})

        return self._call_chat(
            messages,
            response_format=api_response_format,
            tools=tools,
            tool_choice=tool_choice,
        )

    def stream(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        attachments: list[FileAttachment] | None = None,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> Iterator[str]:
        if self.async_mode:
            msg = "Async mode is enabled. Use 'astream' instead."
            raise RuntimeError(msg)
        if not isinstance(self.client, OpenAI):
            msg = "Sync client is not initialized. Call setup() first."
            raise RuntimeError(msg)

        atts = self._validate_attachments(attachments)
        api_response_format = self._map_response_format(response_format, schema)

        if self._has_file_ids(atts):
            input_content = self._build_input_content(input, atts)
            for chunk in self._call_responses_stream(
                input_content, response_format=api_response_format
            ):
                yield chunk
            return

        if isinstance(input, str):
            final_prompt = self._merge_plain_text(input, atts)
            for chunk in self._call_chat_stream(
                [{"role": "user", "content": final_prompt}],
                response_format=api_response_format,
                tools=tools,
                tool_choice=tool_choice,
            ):
                yield chunk
            return

        messages = list(input)
        attachments_text = self._merge_plain_text("", atts)
        if attachments_text:
            messages.append({"role": "user", "content": attachments_text})

        for chunk in self._call_chat_stream(
            messages,
            response_format=api_response_format,
            tools=tools,
            tool_choice=tool_choice,
        ):
            yield chunk

    # ---------- Public async API ----------
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
        if not self.async_mode:
            msg = "Async mode is disabled. Use 'invoke' instead."
            raise RuntimeError(msg)
        self._ensure_async_client()
        if not isinstance(self.client, AsyncOpenAI):
            msg = "Async client is not initialized. Call setup() first."
            raise RuntimeError(msg)

        atts = self._validate_attachments(attachments)
        api_response_format = self._map_response_format(response_format, schema)

        if self._has_file_ids(atts):
            input_content = self._build_input_content(input, atts)
            return await self._acall_responses(
                input_content, response_format=api_response_format
            )

        if isinstance(input, str):
            final_prompt = self._merge_plain_text(input, atts)
            return await self._acall_chat(
                [{"role": "user", "content": final_prompt}],
                response_format=api_response_format,
                tools=tools,
                tool_choice=tool_choice,
            )

        messages = list(input)
        attachments_text = self._merge_plain_text("", atts)
        if attachments_text:
            messages.append({"role": "user", "content": attachments_text})

        return await self._acall_chat(
            messages,
            response_format=api_response_format,
            tools=tools,
            tool_choice=tool_choice,
        )

    async def astream(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        attachments: list[FileAttachment] | None = None,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        if not self.async_mode:
            msg = "Async mode is disabled. Use 'stream' instead."
            raise RuntimeError(msg)
        self._ensure_async_client()
        if not isinstance(self.client, AsyncOpenAI):
            msg = "Async client is not initialized. Call setup() first."
            raise RuntimeError(msg)

        atts = self._validate_attachments(attachments)
        api_response_format = self._map_response_format(response_format, schema)

        if self._has_file_ids(atts):
            input_content = self._build_input_content(input, atts)
            async for chunk in self._acall_responses_stream(
                input_content, response_format=api_response_format
            ):
                yield chunk
            return

        if isinstance(input, str):
            final_prompt = self._merge_plain_text(input, atts)
            async for chunk in self._acall_chat_stream(
                [{"role": "user", "content": final_prompt}],
                response_format=api_response_format,
                tools=tools,
                tool_choice=tool_choice,
            ):
                yield chunk
            return

        messages = list(input)
        attachments_text = self._merge_plain_text("", atts)
        if attachments_text:
            messages.append({"role": "user", "content": attachments_text})

        async for chunk in self._acall_chat_stream(
            messages,
            response_format=api_response_format,
            tools=tools,
            tool_choice=tool_choice,
        ):
            yield chunk

    # ---------- lifecycle ----------
    def setup(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY") or ml_config.resolved_openai_key
        if not api_key:
            msg = "OPENAI_API_KEY is required. Set it via env or ml_config.api_keys.openai."
            raise RuntimeError(msg)
        self._api_key = api_key

        try:
            if self.async_mode:
                try:
                    asyncio.get_running_loop()
                    self._ensure_async_client()
                except RuntimeError:
                    self.client = None
            else:
                self.client = OpenAI(api_key=self._api_key)
        except Exception as e:  # pragma: no cover
            raise self._map_openai_error(e) from e

    def _map_response_format(
        self, response_format: ResponseFormat | None, schema: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if response_format is None or response_format == ResponseFormat.PLAIN_TEXT:
            return None

        if response_format == ResponseFormat.JSON_OBJECT:
            return {"type": "json_object"}

        if response_format == ResponseFormat.JSON_SCHEMA:
            if self.model_name and self.model_name in [
                'gpt-4', 'gpt-4-0613', 'gpt-4-0314', 'gpt-3.5-turbo',
                'gpt-3.5-turbo-0125', 'gpt-3.5-turbo-1106', 'gpt-3.5-turbo-instruct',
                'gpt-4-0125-preview', 'gpt-4-1106-vision-preview', 'chatgpt-4o-latest',
                'gpt-4-turbo', 'gpt-4-turbo-2024-04-09', 'gpt-4-turbo-preview',
                'gpt-4-0125-preview', 'gpt-4-1106-vision-preview'
            ]:
                warnings.warn(
                    f"Model '{self.model_name}' may not support the JSON Schema format. "
                    "Consider using a newer model like 'gpt-4o' for guaranteed compatibility.",
                    UserWarning,
                    stacklevel=2
                )
                return None
            if not schema:
                msg = "`schema` is required for `JSON_SCHEMA` format."
                raise ValueError(msg)
            return {
                "type": "json_schema",
                "json_schema": schema
            }

        return None

    def _ensure_async_client(self) -> None:
        if self.client is None:
            try:
                self.client = AsyncOpenAI(api_key=self._api_key)
            except Exception as e:  # pragma: no cover
                raise self._map_openai_error(e) from e

    def teardown(self) -> None:
        self.client = None

    def _require_sync_client(self) -> OpenAI:
        if not isinstance(self.client, OpenAI):
            msg = "Sync client is not initialized. Call setup() first."
            raise RuntimeError(msg)
        return self.client

    def _require_async_client(self) -> AsyncOpenAI:
        if not isinstance(self.client, AsyncOpenAI):
            msg = "Async client is not initialized. Call setup() first."
            raise RuntimeError(msg)
        return self.client

    # ---------- attachments ----------
    def supported_attachments(self) -> set[str]:
        # Universal kinds supported by this model
        return {PLAIN_TEXT, FILE_ID}

    def _validate_attachments(
        self, attachments: list[FileAttachment] | None
    ) -> list[FileAttachment]:
        atts = attachments or []
        kinds = {a.type for a in atts}
        unsupported = kinds - self.supported_attachments()
        if unsupported:
            msg = f'{self.__class__.__name__} does not support attachments: {", ".join(sorted(unsupported))}'
            raise ModelAPIError(msg)

        foreign = [
            a
            for a in atts
            if a.type == FILE_ID and (a.metadata or {}).get("provider") != "openai"
        ]
        if foreign:
            provs = {(a.metadata or {}).get("provider", "unknown") for a in foreign}
            msg = (
                f"{self.__class__.__name__} only supports FILE_ID with provider='openai'. "
                f'Got providers: {", ".join(sorted(provs))}'
            )
            raise ModelAPIError(msg)

        return atts

    @staticmethod
    def _has_file_ids(atts: list[FileAttachment]) -> bool:
        return any(a.type == FILE_ID for a in atts)

    def _build_input_content(
        self, input: LLModelInput, atts: list[FileAttachment],  # noqa: A002
    ) -> list[StructuredMessage]:
        if isinstance(input, str):
            parts: list[dict[str, Any]] = [{"type": "input_text", "text": input}]
            for a in atts:
                if a.type == PLAIN_TEXT:
                    parts.append({"type": "input_text", "text": str(a.content)})
                elif a.type == FILE_ID:
                    parts.append({"type": "input_file", "file_id": str(a.content)})
            return [{"role": "user", "content": parts}]

        messages = cast(list[StructuredMessage], [dict(msg) for msg in input])
        parts = []
        for a in atts:
            if a.type == PLAIN_TEXT:
                parts.append({"type": "input_text", "text": str(a.content)})
            elif a.type == FILE_ID:
                parts.append({"type": "input_file", "file_id": str(a.content)})

        if parts:
            messages.append({"role": "user", "content": parts})

        return messages

    def _merge_plain_text(self, prompt: str, atts: list[FileAttachment]) -> str:
        extras = [str(a.content) for a in atts if a.type == PLAIN_TEXT]
        if not extras:
            return prompt
        return f"{prompt}\n\n[ATTACHMENTS]\n" + "\n\n".join(extras)

    # ---------- error mapping ----------
    @staticmethod
    def _map_openai_error(err: Exception) -> ModelError:
        if isinstance(err, openai.RateLimitError):
            return ModelRateLimitError(str(err))
        if isinstance(err, openai.APIConnectionError):
            return ModelConnectionError(str(err))
        if isinstance(err, openai.APIStatusError):
            status = getattr(err, "status_code", None)
            resp = getattr(err, "response", None)
            payload_repr = None
            try:
                payload_repr = resp.json() if resp is not None else None
            except Exception:
                payload_repr = None
            return ModelAPIError(
                f"OpenAI API status error ({status}). payload={payload_repr!r}"
            )
        if isinstance(err, openai.APIError):
            return ModelAPIError(str(err))
        return ModelAPIError(str(err))

    # ---------- Sync core callers ----------
    def _call_chat(
        self,
        messages: Sequence[StructuredMessage],
        response_format: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> str:
        client = self._require_sync_client()
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        try:
            resp = client.chat.completions.create(**kwargs)
        except Exception as e:
            raise self._map_openai_error(e) from e

        if tools:
            return resp.choices[0].message.model_dump_json()

        return resp.choices[0].message.content or ""

    def _call_chat_stream(
        self,
        messages: Sequence[StructuredMessage],
        response_format: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> Iterator[str]:
        client = self._require_sync_client()
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "stream": True,
        }
        if response_format:
            kwargs["response_format"] = response_format
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        try:
            stream = client.chat.completions.create(**kwargs)
        except Exception as e:
            raise self._map_openai_error(e) from e

        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    def _call_responses(
        self, input_content: Sequence[StructuredMessage], response_format: dict[str, Any] | None = None
    ) -> str:
        client = self._require_sync_client()
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "input": cast(Any, input_content),
            "temperature": self.temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            resp: Any = client.responses.create(**kwargs)
        except Exception as e:
            raise self._map_openai_error(e) from e

        return (getattr(resp, "output_text", None) or "").strip()

    def _call_responses_stream(
        self, input_content: Sequence[StructuredMessage], response_format: dict[str, Any] | None = None
    ) -> Iterator[str]:
        client = self._require_sync_client()
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "input": cast(Any, input_content),
            "temperature": self.temperature,
            "stream": True,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            stream_or_resp = client.responses.create(**kwargs)
        except Exception as e:
            raise self._map_openai_error(e) from e

        if isinstance(stream_or_resp, Stream):
            for ev in stream_or_resp:
                delta = getattr(getattr(ev, "delta", None), "content", None)
                if delta:
                    yield delta
        else:
            text = (getattr(stream_or_resp, "output_text", None) or "").strip()
            if text:
                yield text

    # ---------- Async core callers ----------
    async def _acall_chat(
        self,
        messages: Sequence[StructuredMessage],
        response_format: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> str:
        client = self._require_async_client()
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        try:
            resp = await client.chat.completions.create(**kwargs)
        except Exception as e:
            raise self._map_openai_error(e) from e

        if tools:
            return resp.choices[0].message.model_dump_json()

        return resp.choices[0].message.content or ""

    async def _acall_chat_stream(
        self,
        messages: Sequence[StructuredMessage],
        response_format: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        client = self._require_async_client()
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "stream": True,
        }
        if response_format:
            kwargs["response_format"] = response_format
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        try:
            stream = await client.chat.completions.create(**kwargs)
        except Exception as e:
            raise self._map_openai_error(e) from e

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    async def _acall_responses(
        self, input_content: Sequence[StructuredMessage], response_format: dict[str, Any] | None = None
    ) -> str:
        client = self._require_async_client()
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "input": cast(Any, input_content),
            "temperature": self.temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            resp: Any = await client.responses.create(**kwargs)
        except Exception as e:
            raise self._map_openai_error(e) from e

        return (getattr(resp, "output_text", None) or "").strip()

    async def _acall_responses_stream(
        self, input_content: Sequence[StructuredMessage], response_format: dict[str, Any] | None = None
    ) -> AsyncIterator[str]:
        client = self._require_async_client()
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "input": cast(Any, input_content),
            "temperature": self.temperature,
            "stream": True,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            stream_or_resp = await client.responses.create(**kwargs)
        except Exception as e:
            raise self._map_openai_error(e) from e

        if isinstance(stream_or_resp, AsyncStream):
            async for ev in stream_or_resp:
                delta = getattr(getattr(ev, "delta", None), "content", None)
                if delta:
                    yield delta
        else:
            text = (getattr(stream_or_resp, "output_text", None) or "").strip()
            if text:
                yield text
