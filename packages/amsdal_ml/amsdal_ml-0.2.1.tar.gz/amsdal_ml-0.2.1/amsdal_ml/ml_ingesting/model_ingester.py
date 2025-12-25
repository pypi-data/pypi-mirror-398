from __future__ import annotations

import io
import logging
from collections.abc import AsyncIterator
from collections.abc import Iterable
from typing import IO
from typing import Any
from typing import ClassVar
from typing import Generic
from typing import TypeVar

from amsdal.models.core.file import File
from amsdal_models.querysets.base_queryset import QuerySetBase

from amsdal_ml.ml_ingesting.loaders.loader import Loader
from amsdal_ml.ml_ingesting.pipeline import DefaultIngestionPipeline
from amsdal_ml.ml_ingesting.types import IngestionSource

LoaderT = TypeVar('LoaderT', bound=Loader)


class ModelIngester(Generic[LoaderT]):
    MIN_OBJECTS_FOR_WARNING: ClassVar[int] = 3

    def __init__(
        self,
        *,
        pipeline: DefaultIngestionPipeline[LoaderT],
        base_tags: Iterable[str] | None = None,
        base_metadata: dict[str, Any] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.pipeline = pipeline
        self.base_tags = list(base_tags or [])
        self.base_metadata = dict(base_metadata or {})
        self.logger = logger or logging.getLogger(__name__)

    async def aingest(
        self,
        objects: Iterable[Any] | AsyncIterator[Any],
        *,
        fields: Iterable[str] | None = None,
        tags: Iterable[str] | None = None,
    ) -> list[Any]:
        results: list[Any] = []
        count_objects = 0
        fields_set = set(fields) if fields else None

        self.logger.debug("Starting async ingest; fields=%s", fields_set)

        async for instance in self._amaterialize(objects):
            count_objects += 1
            object_class, object_id = self._resolve_link(instance)
            self.logger.debug(
                "Async ingest instance %s:%s; model_fields=%s",
                object_class,
                object_id,
                getattr(instance.__class__, "model_fields", None),
            )

            found_any = False
            async for payload in self._aiter_values(instance, fields_set):
                found_any = True
                field_name, field_title, stream, filename, kind = payload
                source = self._build_source(object_class, object_id, field_name, field_title, filename)
                run_tags = self._build_tags(tags, field_name, kind)
                try:
                    chunk_res = await self.pipeline.arun(
                        stream,
                        filename=filename,
                        tags=run_tags,
                        source=source,
                    )
                    results.extend(chunk_res)
                except Exception as exc:  # noqa: BLE001
                    self._warn_skip(object_class, field_name, exc)

            if not found_any and count_objects <= self.MIN_OBJECTS_FOR_WARNING:
                self.logger.info("  -> No ingestible fields found in %s:%s", object_class, object_id)

        if count_objects == 0:
            self.logger.warning("ModelIngester received 0 objects to process!")

        self.logger.debug("Async ingest finished; processed=%s results=%s", count_objects, len(results))
        return results

    def ingest(
        self,
        objects: Iterable[Any],
        *,
        fields: Iterable[str] | None = None,
        tags: Iterable[str] | None = None,
    ) -> list[Any]:
        rows = list(self._materialize(objects))
        fields_set = set(fields) if fields else None
        results: list[Any] = []
        self.logger.debug("Starting sync ingest; rows=%s fields=%s", len(rows), fields_set)
        for instance in rows:
            object_class, object_id = self._resolve_link(instance)
            self.logger.debug(
                "Sync ingest instance %s:%s; model_fields=%s",
                object_class,
                object_id,
                getattr(instance.__class__, "model_fields", None),
            )
            found_any = False
            for payload in self._iter_values(instance, fields_set):
                found_any = True
                field_name, field_title, stream, filename, kind = payload
                source = self._build_source(object_class, object_id, field_name, field_title, filename)
                run_tags = self._build_tags(tags, field_name, kind)
                try:
                    results.extend(
                        self.pipeline.run(
                            stream,
                            filename=filename,
                            tags=run_tags,
                            source=source,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    self._warn_skip(object_class, field_name, exc)
            if not found_any:
                self.logger.debug("No ingestible fields in %s:%s", object_class, object_id)

        self.logger.debug("Sync ingest finished; processed=%s results=%s", len(rows), len(results))
        return results

    async def _aiter_values(
        self,
        instance: Any,
        fields_set: set[str] | None,
    ) -> AsyncIterator[tuple[str, str | None, IO[Any], str | None, str]]:
        if isinstance(instance, File):
            try:
                stream, filename = await self._afile_to_stream(instance)
                yield "file", "file", stream, filename, "file"
            except Exception as exc:
                self._warn_skip("File", str(getattr(instance, "filename", instance)), exc)
            return

        model_fields = getattr(instance.__class__, "model_fields", None) or {}
        if not model_fields:
            return

        for name, info in model_fields.items():
            if fields_set is not None and name not in fields_set:
                continue
            val = getattr(instance, name, None)
            try:
                payload = await self._avalue_to_stream(val)
                if payload is None:
                    continue
                stream, filename, kind = payload
                title = getattr(info, "title", None) or name
                yield name, title, stream, filename, kind
            except Exception as exc:
                self._warn_skip(instance.__class__.__name__, name, exc)

    def _iter_values(
        self,
        instance: Any,
        fields_set: set[str] | None,
    ) -> Iterable[tuple[str, str | None, IO[Any], str | None, str]]:
        if isinstance(instance, File):
            try:
                stream, filename = self._file_to_stream(instance)
                return [("file", "file", stream, filename, "file")]
            except Exception as exc:
                self._warn_skip("File", str(getattr(instance, "filename", instance)), exc)
                return []

        model_fields = getattr(instance.__class__, "model_fields", None) or {}
        if not model_fields:
            return []

        items: list[tuple[str, str | None, IO[Any], str | None, str]] = []
        for name, info in model_fields.items():
            if fields_set is not None and name not in fields_set:
                continue
            val = getattr(instance, name, None)
            try:
                payload = self._value_to_stream(val)
                if payload is None:
                    continue
                stream, filename, kind = payload
                title = getattr(info, "title", None) or name
                items.append((name, title, stream, filename, kind))
            except Exception as exc:
                self._warn_skip(instance.__class__.__name__, name, exc)
        return items

    def _build_source(
        self,
        object_class: str,
        object_id: str,
        field_name: str,
        field_title: str | None,
        filename: str | None,
    ) -> IngestionSource:
        meta = dict(self.base_metadata)
        meta.setdefault("field", field_name)
        if field_title:
            meta.setdefault("field_title", field_title)
        if filename:
            meta.setdefault("filename", filename)
        return IngestionSource(
            object_class=object_class,
            object_id=object_id,
            tags=list(self.base_tags),
            metadata=meta,
        )

    def _build_tags(self, extra: Iterable[str] | None, field_name: str, kind: str) -> list[str]:
        tags = list(extra or [])
        tags.append(kind)
        tags.append(f"field:{field_name}")
        return tags

    def _resolve_link(self, instance: Any) -> tuple[str, str]:
        cls = instance.__class__.__name__
        oid = getattr(instance, "object_id", None)
        if oid is None:
            oid = getattr(instance, "id", None)
        if oid is None:
            oid = id(instance)
        return cls, str(oid)

    def _warn_skip(self, object_class: str, field_name: str, exc: Exception) -> None:
        self.logger.warning("Skipping %s.%s: %s", object_class, field_name, exc)

    def _materialize(self, objects: Any) -> Iterable[Any]:
        if isinstance(objects, QuerySetBase):
            return objects.execute()  # type: ignore[attr-defined]
        return list(objects)

    async def _amaterialize(self, objects: Any) -> AsyncIterator[Any]:
        if isinstance(objects, QuerySetBase):
            result = await objects.aexecute()  # type: ignore[attr-defined]
            for item in result:
                yield item
            return

        for item in objects:
            yield item

    def _file_to_stream(self, file_obj: File) -> tuple[IO[Any], str | None]:
        content = file_obj.read_bytes()
        return io.BytesIO(content), getattr(file_obj, "filename", None)

    async def _afile_to_stream(self, file_obj: File) -> tuple[IO[Any], str | None]:
        content = await file_obj.aread_bytes()
        return io.BytesIO(content), getattr(file_obj, "filename", None)

    def _value_to_stream(self, val: Any) -> tuple[IO[Any], str | None, str] | None:
        if val is None:
            return None
        if isinstance(val, File):
            stream, filename = self._file_to_stream(val)
            return stream, filename, "file"
        if isinstance(val, (bytes, bytearray)):
            return io.BytesIO(val), None, "file"
        if isinstance(val, str):
            return io.StringIO(val), None, "text"
        return None

    async def _avalue_to_stream(self, val: Any) -> tuple[IO[Any], str | None, str] | None:
        if val is None:
            return None
        if isinstance(val, File):
            stream, filename = await self._afile_to_stream(val)
            return stream, filename, "file"
        if isinstance(val, (bytes, bytearray)):
            return io.BytesIO(val), None, "file"
        if isinstance(val, str):
            return io.StringIO(val), None, "text"
        return None
