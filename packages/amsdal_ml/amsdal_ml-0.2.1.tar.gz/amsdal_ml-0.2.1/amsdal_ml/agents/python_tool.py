from __future__ import annotations

import inspect
from collections.abc import Callable
from collections.abc import Coroutine
from typing import Any

from pydantic import create_model
from pydantic.fields import FieldInfo


class PythonTool:
    def __init__(
        self,
        func: Callable[..., Coroutine[Any, Any, Any] | Any],
        name: str,
        description: str,
    ):
        if not inspect.iscoroutinefunction(func) and not inspect.isfunction(func):
            msg = 'Tool must be a function or coroutine function'
            raise TypeError(msg)

        self.func = func
        self.name = name
        self.description = description
        self.is_async = inspect.iscoroutinefunction(func)
        self.parameters = self._build_schema()

    def _build_schema(self) -> dict[str, Any]:
        sig = inspect.signature(self.func)
        fields: dict[str, Any] = {}
        for param in sig.parameters.values():
            if param.kind not in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            ):
                continue

            field_info = (
                param.default
                if isinstance(param.default, FieldInfo)
                else FieldInfo(
                    default=param.default if param.default is not inspect.Parameter.empty else ...,
                    description=None,
                )
            )
            fields[param.name] = (
                param.annotation if param.annotation is not inspect.Parameter.empty else Any,
                field_info,
            )

        model = create_model(f'{self.name}Input', **fields)
        schema = model.model_json_schema()

        return {
            'type': 'object',
            'properties': schema.get('properties', {}),
            'required': schema.get('required', []),
        }


class _PythonToolProxy:
    def __init__(self, tool: PythonTool, timeout: float | None = 20.0):
        self.tool = tool
        self.name = tool.name
        self.qualified = tool.name
        self.parameters = tool.parameters
        self.description = tool.description
        self._default_timeout = timeout

    def set_timeout(self, timeout: float | None) -> None:
        self._default_timeout = timeout

    async def run(
        self,
        args: dict[str, Any],
        context: Any = None,
        *,
        convert_result: bool = True,
    ) -> Any:
        _ = (context, convert_result)

        if self.tool.is_async:
            return await self.tool.func(**args)
        else:
            return self.tool.func(**args)
