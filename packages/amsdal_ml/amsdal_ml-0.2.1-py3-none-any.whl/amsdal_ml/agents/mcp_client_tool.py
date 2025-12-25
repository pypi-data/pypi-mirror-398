from __future__ import annotations

from typing import Any

from amsdal_ml.mcp_client.base import ToolClient


class ClientToolProxy:
    def __init__(
        self,
        client: ToolClient,
        alias: str,
        name: str,
        schema: dict[str, Any],
        description: str,
    ):
        self.client = client
        self.alias = alias
        self.name = name
        self.qualified = f'{alias}.{name}'
        self.parameters = schema
        self.description = description
        self._default_timeout: float | None = 20.0

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

        if self.parameters:
            try:
                import jsonschema

                jsonschema.validate(instance=args, schema=self.parameters)
            except Exception as exc:
                msg = f'Tool input validation failed for {self.qualified}: {exc}'
                raise ValueError(msg) from exc

        return await self.client.call(self.name, args, timeout=self._default_timeout)
