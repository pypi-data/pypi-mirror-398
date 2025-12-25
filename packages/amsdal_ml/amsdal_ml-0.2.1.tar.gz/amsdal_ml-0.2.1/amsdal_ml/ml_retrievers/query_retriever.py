"""Natural language query interface for Amsdal QuerySets."""

import json
from datetime import date
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from typing import Generic
from typing import Literal
from typing import Optional
from typing import TypeVar
from typing import get_args
from typing import get_origin

from amsdal_models.classes.model import Model
from amsdal_models.querysets.base_queryset import QuerySetBase
from amsdal_utils.query.enums import Lookup
from pydantic import BaseModel

from amsdal_ml.ml_models.models import MLModel
from amsdal_ml.ml_models.utils import ResponseFormat
from amsdal_ml.ml_retrievers.adapters import DefaultRetrieverAdapter
from amsdal_ml.ml_retrievers.adapters import get_retriever_adapter
from amsdal_ml.ml_retrievers.retriever import Document
from amsdal_ml.ml_retrievers.retriever import Retriever
from amsdal_ml.prompts import get_prompt
from amsdal_ml.utils.query_utils import serialize_and_clean_record

T = TypeVar("T", bound=Model)
AmsdalQuerySet = QuerySetBase[T]


class FilterCondition(BaseModel):
    """Single filter condition for database query."""

    field: str
    lookup: str
    value: str | int | float | bool | None | date | datetime | list[str | int | float | bool | date | datetime]


class FilterResponse(BaseModel):
    """Structured response for LLM."""

    filters: list[FilterCondition]


class NLQueryExecutor:
    """
    Natural language query interface for Amsdal QuerySets.

    Converts natural language queries into structured database filters using an LLM.

    Supported Field Types:
    - Primitives: str, int, float, bool
    - Enums: Enum subclasses
    - Literals: Literal[...]
    - Unions: Union of supported types (no mixed with models/dict/lists/tuples/sets)
    - Annotated: Annotated[supported_type, ...]
    - Dates: datetime, date

    Unsupported Field Types (will be skipped):
    - Models: BaseModel/Model subclasses
    - Dicts: dict[...]
    - Lists/Tuples/Sets: list/tuple/set[...]
    - Callables: Callable[...]
    - Unknown types: bytes, custom classes, etc.
    Example:
        >>> llm = OpenAIModel()
        >>> llm.setup()
        >>> base_qs = BaseRateInfo.objects.filter(accessibility__eq='public')
        >>> executor = NLQueryExecutor(
        ...     llm=llm,
        ...     queryset=base_qs,
        ...     base_filters={'status__eq': 'active'},
        ...     fields=['rate', 'premium_band', 'effective_date', 'rate_category'],
        ...     fields_info={'rate': 'Current rate value as decimal (5.15% = 0.0515)'}
        ... )
        >>> results = await executor.execute("show me all high band rates")
    """

    _full_prompt: Optional[str]
    MAX_VALUES_DISPLAY_LIMIT = 100
    MAX_SCHEMA_INSPECTION_DEPTH = 10

    def __init__(
        self,
        llm: MLModel,
        queryset: AmsdalQuerySet[T],
        base_filters: Optional[dict[str, Any]] = None,
        fields: Optional[list[str]] = None,
        fields_info: Optional[dict[str, str]] = None,
        prompt_path: Optional[str | Path] = None,
        llm_response_format: Optional[ResponseFormat] = None,
        adapter: Optional[DefaultRetrieverAdapter] = None,
    ) -> None:
        """
        Initialize NLQueryExecutor.

        Args:
            llm: ML model instance for query interpretation
            queryset: AMSDAL QuerySet
            base_filters: Optional dict of additional base filters to apply to all queries
                         (e.g., {'accessibility__eq': 'public'})
            fields: Optional list of field names to include in search schema.
                   If None, all model fields are used.
            fields_info: Optional dict mapping field names to descriptions.
                        Takes priority over model field titles.
                        Format: {'field_name': 'description text'}
            prompt_path: Optional path to custom prompt file. If None, uses default 'nl_query_filter'
                        which is specifically designed for AMSDAL ORM with comprehensive coverage of all
                        lookup operators, field type conversions, and detailed examples for
                        optimal query interpretation.
            llm_response_format: Optional desired response format. Can be ResponseFormat enum or string
                                ('JSON_SCHEMA', 'JSON_OBJECT', 'PLAIN_TEXT'). If None, will auto-detect best.
            adapter: Optional adapter instance. If None, will auto-detect based on LLM type.
        """
        self.llm = llm
        self.base_queryset = queryset
        self.model_class = queryset.entity
        self.base_filters = base_filters or {}
        self.fields = fields
        self.fields_info = fields_info or {}
        self.prompt_path = prompt_path
        self.adapter = adapter or get_retriever_adapter(llm)
        self.llm_response_format = self._select_response_format(llm_response_format)

        self.search_schema = self._build_search_schema()
        self.system_prompt = self._build_system_prompt()
        self._full_prompt = None

    @property
    def response_schema(self) -> dict[str, Any]:
        """
        Generates a JSON schema for the response.
        """
        base_schema = FilterResponse.model_json_schema()
        return self.adapter.get_response_schema(base_schema)

    async def execute(self, query: str, limit : int | None = 30) -> list[T]:
        results: list[T] = await self.asearch(query)
        return results[:limit] if limit is not None else results

    async def asearch(self, query: str) -> list[T]:
        prompt = get_prompt("nl_query_filter", custom_path=self.prompt_path)
        full_prompt = prompt.render_text(
            schema=json.dumps(self.search_schema, indent=2), query=query
        )
        self._full_prompt = full_prompt

        response = await self.llm.ainvoke(
            full_prompt,
            response_format=self.llm_response_format,
            schema=(
                self.response_schema
                if self.llm_response_format == ResponseFormat.JSON_SCHEMA
                else None
            ),
        )
        raw_json = response.strip()

        if self.llm_response_format == ResponseFormat.PLAIN_TEXT:
            if "```json" in raw_json:
                raw_json = raw_json.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_json:
                raw_json = raw_json.split("```")[1].split("```")[0].strip()

        queryset = self.base_queryset.filter(**self.base_filters)

        conditions = self.adapter.parse_response(
            raw_json,
            is_schema_based=self.llm_response_format == ResponseFormat.JSON_SCHEMA,
        )

        if not conditions:
            return await queryset.aexecute()  # type: ignore[attr-defined]

        allowed_lookups = {lookup.value for lookup in Lookup}
        all_filters = {}

        for cond in conditions:
            if cond.lookup not in allowed_lookups:
                continue

            filter_key = f"{cond.field}__{cond.lookup}"
            all_filters[filter_key] = cond.value

        queryset = queryset.filter(**all_filters)

        return await queryset.aexecute()  # type: ignore[attr-defined]

    def search(self, query: str) -> list[T]:
        prompt = get_prompt("nl_query_filter", custom_path=self.prompt_path)
        full_prompt = prompt.render_text(
            schema=json.dumps(self.search_schema, indent=2), query=query
        )
        self._full_prompt = full_prompt

        response = self.llm.invoke(
            full_prompt,
            response_format=self.llm_response_format,
            schema=(
                self.response_schema
                if self.llm_response_format == ResponseFormat.JSON_SCHEMA
                else None
            ),
        )
        raw_json = response.strip()

        if self.llm_response_format == ResponseFormat.PLAIN_TEXT:
            if "```json" in raw_json:
                raw_json = raw_json.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_json:
                raw_json = raw_json.split("```")[1].split("```")[0].strip()

        queryset = self.base_queryset.filter(**self.base_filters)

        conditions = self.adapter.parse_response(
            raw_json,
            is_schema_based=self.llm_response_format == ResponseFormat.JSON_SCHEMA,
        )

        if not conditions:
            return queryset.execute()  # type: ignore[attr-defined]

        allowed_lookups = {lookup.value for lookup in Lookup}
        all_filters = {}

        for cond in conditions:
            if cond.lookup not in allowed_lookups:
                continue

            filter_key = f"{cond.field}__{cond.lookup}"
            all_filters[filter_key] = cond.value

        queryset = queryset.filter(**all_filters)

        return queryset.execute()  # type: ignore[attr-defined]

    def _select_response_format(
        self,
        requested: Optional[ResponseFormat],
    ) -> ResponseFormat:
        if requested:
            return requested

        supported = self.llm.supported_formats
        if ResponseFormat.JSON_SCHEMA in supported:
            return ResponseFormat.JSON_SCHEMA
        if ResponseFormat.JSON_OBJECT in supported:
            return ResponseFormat.JSON_OBJECT
        return ResponseFormat.PLAIN_TEXT

    def _build_search_schema(self) -> list[dict[str, Any]]:
        schema = []
        model_fields = self.model_class.model_fields
        fields_to_process = (
            self.fields
            if self.fields is not None
            else [*model_fields.keys(), *self.base_queryset._annotations.keys()]
        )

        for field_name in fields_to_process:
            if field_name in model_fields:
                field_obj = model_fields[field_name]
                description = self.fields_info.get(
                    field_name, field_obj.title or field_name
                )
                field_type = self._get_field_type(field_obj.annotation)
                if field_type is None:
                    continue
            elif field_name in self.base_queryset._annotations:
                description = f"{field_name}: computed field based on internal fields"
                field_type = "string"
            else:
                continue

            schema.append(
                {"name": field_name, "type": field_type, "description": description}
            )

        return schema

    def is_skip_type(self, typ: Any, depth: int = 0) -> bool:
        if depth > self.MAX_SCHEMA_INSPECTION_DEPTH:
            return True

        origin = get_origin(typ)

        if origin.__name__ == "Annotated" if origin else False:
            return self.is_skip_type(get_args(typ)[0], depth + 1)

        if origin is dict:
            return True

        if origin in (list, tuple, set):
            return True

        if origin and "Union" in str(origin):
            return any(
                self.is_skip_type(arg, depth + 1)
                for arg in get_args(typ)
                if arg is not type(None)
            )

        try:
            if (
                isinstance(typ, type)
                and issubclass(typ, (BaseModel, Model))
                and not issubclass(typ, Enum)
            ):
                return True
        except TypeError:
            pass

        return False

    def _extract_enum_literal(self, typ: Any, depth: int = 0) -> list[str] | None:
        if depth > self.MAX_SCHEMA_INSPECTION_DEPTH:
            return None

        origin = get_origin(typ)

        if origin.__name__ == "Annotated" if origin else False:
            return self._extract_enum_literal(get_args(typ)[0], depth + 1)

        try:
            if isinstance(typ, type) and issubclass(typ, Enum):
                return [e.value for e in typ]
        except TypeError:
            pass

        if origin is Literal:
            return list(get_args(typ))

        if origin and "Union" in str(origin):
            all_values = []
            has_primitive = False
            for arg in get_args(typ):
                if arg is type(None):
                    continue
                if arg in (str, int, float, bool):
                    has_primitive = True
                    break
                values = self._extract_enum_literal(arg, depth + 1)
                if values:
                    all_values.extend(values)

            if has_primitive or not all_values:
                return None
            return list(dict.fromkeys(all_values))

        return None

    def _get_field_type(self, annotation) -> str | None:
        origin = get_origin(annotation)

        if origin is dict:
            return None

        # TODO: Enable list/set/tuple fields when AMSDAL adds JSONB array support
        skip_list_fields = True
        if skip_list_fields and origin in (
            list,
            tuple,
            set,
        ):
            return None

        if origin in (list, tuple, set):
            args = get_args(annotation)
            if not args:
                return "list of string"

            inner = args[0]
            if self.is_skip_type(inner):
                return None

            values = self._extract_enum_literal(inner)
            if values:
                if len(values) > self.MAX_VALUES_DISPLAY_LIMIT:
                    values = [*values[: self.MAX_VALUES_DISPLAY_LIMIT], "..."]
                return f"list of options: {', '.join(f'{type(v).__name__}({v!r})' for v in values)}"

            inner_type = self._get_primitive_type(inner)
            if inner_type is None:
                return None
            return f"list of {inner_type}"

        if self.is_skip_type(annotation):
            return None

        values = self._extract_enum_literal(annotation)
        if values:
            if len(values) > self.MAX_VALUES_DISPLAY_LIMIT:
                values = [*values[: self.MAX_VALUES_DISPLAY_LIMIT], "..."]
            return f"options: {', '.join(f'{type(v).__name__}({v!r})' for v in values)}"

        return self._get_primitive_type(annotation)

    def _get_primitive_type(self, typ: Any, depth: int = 0) -> str | None:
        if depth > self.MAX_SCHEMA_INSPECTION_DEPTH:
            return "string"

        origin = get_origin(typ)

        if origin.__name__ == "Annotated" if origin else False:
            return self._get_primitive_type(get_args(typ)[0], depth + 1)

        if origin and "Union" in str(origin):
            for arg in get_args(typ):
                if arg is type(None):
                    continue
                if arg is int or arg is float:
                    return "number"
                if arg is bool:
                    return "boolean"
                if arg is str:
                    return "string"
                return self._get_primitive_type(arg, depth + 1) or "string"

        if typ is int or typ is float:
            return "number"
        if typ is bool:
            return "boolean"
        if typ is str:
            return "string"

        type_name = typ.__name__.lower()
        if type_name in ("int", "float"):
            return "number"
        if type_name == "bool":
            return "boolean"
        if type_name in ("str", "string"):
            return "string"
        if "datetime" in type_name:
            return "datetime (YYYY-MM-DD HH:MM:SS)"
        if "date" in type_name and "time" not in type_name:
            return "date (YYYY-MM-DD)"

        return None

    def _build_system_prompt(self) -> str:
        schema_json = json.dumps(self.search_schema, indent=2, ensure_ascii=False)
        prompt = get_prompt('nl_query_filter', custom_path=self.prompt_path)
        return prompt.render_text(schema=schema_json, query='{query}')


class NLQueryRetriever(Retriever, Generic[T]):
    """
    Retriever wrapper for NLQueryExecutor.
    """

    def __init__(
        self,
        llm: MLModel,
        queryset: AmsdalQuerySet[T],
        base_filters: Optional[dict[str, Any]] = None,
        fields: Optional[list[str]] = None,
        fields_info: Optional[dict[str, str]] = None,
        prompt_path: Optional[str | Path] = None,
        llm_response_format: Optional[ResponseFormat] = None,
        adapter: Optional[DefaultRetrieverAdapter] = None,
    ) -> None:
        self.executor = NLQueryExecutor(
            llm=llm,
            queryset=queryset,
            base_filters=base_filters,
            fields=fields,
            fields_info=fields_info,
            prompt_path=prompt_path,
            llm_response_format=llm_response_format,
            adapter=adapter,
        )

    async def invoke(self, query: str, limit: int | None = 30) -> list[Document]:
        results: list[T] = await self.executor.execute(query, limit)
        documents = []
        for item in results:
            cleaned_data = await serialize_and_clean_record(item)
            documents.append(
                Document(
                    page_content=json.dumps(cleaned_data, ensure_ascii=False),
                    metadata=item.model_dump(),
                )
            )
        return documents
