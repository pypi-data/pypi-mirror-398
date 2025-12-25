from __future__ import annotations

import json
from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from amsdal_ml.ml_models.models import MLModel
    from amsdal_ml.ml_retrievers.query_retriever import FilterCondition


class RetrieverAdapter(ABC):

    @abstractmethod
    def get_response_schema(self, base_schema: dict[str, Any]) -> dict[str, Any]:
        """Adapts the base JSON schema for the specific model."""
        raise NotImplementedError

    @abstractmethod
    def parse_response(
        self,
        raw_json: str,
        *,
        is_schema_based: bool,
    ) -> list[FilterCondition]:
        """Parses the raw JSON string from the model into a list of FilterCondition."""
        raise NotImplementedError


class DefaultRetrieverAdapter(RetrieverAdapter):
    def get_response_schema(self, base_schema: dict[str, Any]) -> dict[str, Any]:
        return base_schema

    def parse_response(
        self,
        raw_json: str,
        *,
        is_schema_based: bool,
    ) -> list[FilterCondition]:
        from amsdal_ml.ml_retrievers.query_retriever import FilterCondition
        from amsdal_ml.ml_retrievers.query_retriever import FilterResponse

        try:
            filter_data = json.loads(raw_json)

            if is_schema_based:
                return FilterResponse.model_validate(filter_data).filters

            if isinstance(filter_data, dict) and "filters" in filter_data:
                return [FilterCondition(**cond) for cond in filter_data["filters"]]
            if isinstance(filter_data, list):
                return [FilterCondition(**cond) for cond in filter_data]

            return []
        except (json.JSONDecodeError, Exception):
            return []


class OpenAIRetrieverAdapter(DefaultRetrieverAdapter):
    def get_response_schema(self, base_schema: dict[str, Any]) -> dict[str, Any]:
        def add_additional_properties_recursively(schema_node: dict[str, Any] | list[Any]) -> None:
            if isinstance(schema_node, dict):
                if (
                    schema_node.get("type") == "object"
                    and "additionalProperties" not in schema_node
                ):
                    schema_node["additionalProperties"] = False

                for value in schema_node.values():
                    add_additional_properties_recursively(value)

            elif isinstance(schema_node, list):
                for item in schema_node:
                    add_additional_properties_recursively(item)

        add_additional_properties_recursively(base_schema)

        return {
            "name": "data",
            "strict": True,
            "schema": base_schema
        }


def get_retriever_adapter(model: MLModel) -> RetrieverAdapter:
    model_name = model.__class__.__name__.lower()

    if "openai" in model_name:
        return OpenAIRetrieverAdapter()

    return DefaultRetrieverAdapter()
