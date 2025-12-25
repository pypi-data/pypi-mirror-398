from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from amsdal_ml.ml_models.models import MLModel


class ToolAdapter(ABC):
    @abstractmethod
    def get_tools_schema(self, tools: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Converts indexed tools to the model-specific function calling schema.

        Args:
            tools: A dictionary mapping tool names to tool proxy objects.
                   Tool objects are expected to have `description` and `parameters` attributes.

        Returns:
            list[dict[str, Any]]: A list of tool definitions compatible with the model's API.
        """
        raise NotImplementedError

    @abstractmethod
    def parse_response(self, response_data: dict[str, Any]) -> tuple[str | None, list[dict[str, Any]] | None]:
        """
        Parses the model's response to extract content and tool calls.

        Args:
            response_data: The JSON response from the model.

        Returns:
            tuple[str | None, list[dict[str, Any]] | None]: A tuple containing:
                - content_text: The text content of the response (or None).
                - tool_calls: A list of tool calls (or None).
        """
        raise NotImplementedError

    @abstractmethod
    def get_tool_call_info(self, tool_call: dict[str, Any]) -> tuple[str, str, str]:
        """
        Extracts function name, arguments string, and call ID from a tool call object.

        Args:
            tool_call: A single tool call object from the parsed response.

        Returns:
            tuple[str, str, str]: A tuple containing (function_name, arguments_str, call_id).
        """
        raise NotImplementedError


class OpenAIToolAdapter(ToolAdapter):
    def get_tools_schema(self, tools: dict[str, Any]) -> list[dict[str, Any]]:
        tools_schema = []
        for name, tool in tools.items():
            tools_schema.append({
                'type': 'function',
                'function': {
                    'name': name,
                    'description': tool.description,
                    'parameters': tool.parameters,
                },
            })
        return tools_schema

    def parse_response(self, response_data: dict[str, Any]) -> tuple[str | None, list[dict[str, Any]] | None]:
        content_text = response_data.get('content')
        tool_calls = response_data.get('tool_calls')
        return content_text, tool_calls

    def get_tool_call_info(self, tool_call: dict[str, Any]) -> tuple[str, str, str]:
        function_name = tool_call['function']['name']
        arguments_str = tool_call['function']['arguments']
        call_id = tool_call['id']
        return function_name, arguments_str, call_id



def get_tool_adapter(model: MLModel) -> ToolAdapter:
    """
    Factory function to get the appropriate ToolAdapter for a given model.

    Args:
        model: The MLModel instance.

    Returns:
        ToolAdapter: An instance of a ToolAdapter subclass.
    """
    model_name = model.__class__.__name__.lower()

    if "openai" in model_name:
        return OpenAIToolAdapter()

    return OpenAIToolAdapter()
