import asyncio
import json
import os
from datetime import date
from enum import Enum
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from amsdal_models.classes.model import Model
from pydantic import Field

from amsdal_ml.ml_models.models import LLModelInput
from amsdal_ml.ml_models.models import MLModel
from amsdal_ml.ml_models.utils import ResponseFormat
from amsdal_ml.ml_retrievers.query_retriever import NLQueryRetriever

os.environ["AMSDAL_CONTRIBS"] = "[]"

EXPECTED_COUNT_TWO = 2
EXPECTED_COUNT_THREE = 3
LAPTOP_PRICE = 999.99
TABLET_PRICE = 799.00
PHONE_PRICE = 599.50
QUANTITY_FIVE = 5
PRICE_SEVEN_HUNDRED = 700.0
PRICE_EIGHT_HUNDRED = 800.0


class MockLLM(MLModel):
    def __init__(self, response: str, response_format: str | None = None):
        self._response = response
        self._response_format = response_format
        self.async_mode = False

    @property
    def supported_formats(self) -> set[ResponseFormat]:
        return {ResponseFormat.JSON_OBJECT, ResponseFormat.PLAIN_TEXT}

    @property
    def input_role(self) -> str:
        return "user"

    @property
    def output_role(self) -> str:
        return "assistant"

    @property
    def tool_role(self) -> str:
        return "tool"

    @property
    def system_role(self) -> str:
        return "system"

    @property
    def content_field(self) -> str:
        return "content"

    @property
    def role_field(self) -> str:
        return "role"

    @property
    def tool_call_id_field(self) -> str:
        return "tool_call_id"

    @property
    def tool_name_field(self) -> str:
        return "name"

    @property
    def response_format(self) -> str | None:
        return self._response_format

    def setup(self) -> None:
        pass

    def teardown(self) -> None:
        pass

    def invoke(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        attachments: list[Any] | None = None,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> str:
        return self._response

    async def ainvoke(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        attachments: list[Any] | None = None,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> str:
        await asyncio.sleep(0)
        return self._response

    def stream(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        attachments: list[Any] | None = None,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ):
        yield self._response

    async def astream(
        self,
        input: LLModelInput,  # noqa: A002
        *,
        attachments: list[Any] | None = None,
        response_format: ResponseFormat | None = None,
        schema: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ):
        await asyncio.sleep(0)
        yield self._response


class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class Product(Model):
    name: str = Field(..., title="Product Name")
    price: float = Field(..., title="Product Price")
    status: StatusEnum = Field(..., title="Product Status")
    quantity: int = Field(..., title="Quantity in Stock")
    release_date: date = Field(..., title="Release Date")
    is_available: bool = Field(..., title="Is Available")


def create_mock_product(
    name: str,
    price: float,
    status: StatusEnum,
    quantity: int,
    release_date: date,
    *,
    is_available: bool,
) -> Product:
    return Product(
        name=name,
        price=price,
        status=status,
        quantity=quantity,
        release_date=release_date,
        is_available=is_available,
    )


def create_mock_queryset(return_value: list[Product]) -> MagicMock:
    filtered_mock = MagicMock()
    filtered_mock.filter = MagicMock(return_value=filtered_mock)
    filtered_mock.aexecute = AsyncMock(return_value=return_value)

    mock_queryset = MagicMock()
    mock_queryset.entity = Product
    mock_queryset._annotations = {}
    mock_queryset.filter = MagicMock(return_value=filtered_mock)
    mock_queryset.aexecute = AsyncMock(return_value=return_value)

    return mock_queryset


@pytest.mark.asyncio
async def test_valid_json_list():
    response = json.dumps([{"field": "price", "lookup": "gte", "value": 600.0}])
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )
    tablet = create_mock_product(
        "Tablet", 799.00, StatusEnum.PENDING, 5, date(2024, 3, 20), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop, tablet])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products with price >= 600")

    assert len(result) == EXPECTED_COUNT_TWO
    prices = {p.price for p in result}
    assert LAPTOP_PRICE in prices
    assert TABLET_PRICE in prices


@pytest.mark.asyncio
async def test_json_with_filters_wrapper():
    response = json.dumps(
        {"filters": [{"field": "status", "lookup": "exact", "value": "active"}]}
    )
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("active products")

    assert len(result) == 1
    assert result[0].name == "Laptop"
    assert result[0].status == StatusEnum.ACTIVE


@pytest.mark.asyncio
async def test_json_in_markdown_backticks():
    response = f"""```json
{json.dumps([{"field": "is_available", "lookup": "exact", "value": True}])}
```"""
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )
    tablet = create_mock_product(
        "Tablet", 799.00, StatusEnum.PENDING, 5, date(2024, 3, 20), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop, tablet])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("available products")

    assert len(result) == EXPECTED_COUNT_TWO
    names = {p.name for p in result}
    assert "Laptop" in names
    assert "Tablet" in names


@pytest.mark.asyncio
async def test_invalid_json_returns_all():
    response = "This is not valid JSON at all"
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )
    phone = create_mock_product(
        "Phone", 599.50, StatusEnum.INACTIVE, 0, date(2023, 6, 1), is_available=False
    )
    tablet = create_mock_product(
        "Tablet", 799.00, StatusEnum.PENDING, 5, date(2024, 3, 20), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop, phone, tablet])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("all products")

    assert len(result) == EXPECTED_COUNT_THREE


@pytest.mark.asyncio
async def test_empty_response():
    response = ""
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )
    phone = create_mock_product(
        "Phone", 599.50, StatusEnum.INACTIVE, 0, date(2023, 6, 1), is_available=False
    )
    tablet = create_mock_product(
        "Tablet", 799.00, StatusEnum.PENDING, 5, date(2024, 3, 20), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop, phone, tablet])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products")

    assert len(result) == EXPECTED_COUNT_THREE


@pytest.mark.asyncio
async def test_multiple_filters():
    response = json.dumps(
        [
            {"field": "price", "lookup": "gte", "value": 500.0},
            {"field": "is_available", "lookup": "exact", "value": True},
        ]
    )
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )
    tablet = create_mock_product(
        "Tablet", 799.00, StatusEnum.PENDING, 5, date(2024, 3, 20), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop, tablet])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("available products over 500")

    assert len(result) == EXPECTED_COUNT_TWO
    names = {p.name for p in result}
    assert "Laptop" in names
    assert "Tablet" in names


@pytest.mark.asyncio
async def test_nested_backticks_extraction():
    response = f"""Here's the filter:
```json
{json.dumps([{"field": "quantity", "lookup": "exact", "value": 5}])}
```
Hope that helps!"""
    llm = MockLLM(response=response)

    tablet = create_mock_product(
        "Tablet", 799.00, StatusEnum.PENDING, 5, date(2024, 3, 20), is_available=True
    )

    mock_queryset = create_mock_queryset([tablet])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products with 5 items")

    assert len(result) == 1
    assert result[0].name == "Tablet"
    assert result[0].quantity == QUANTITY_FIVE


@pytest.mark.asyncio
async def test_status_enum_filter():
    response = json.dumps([{"field": "status", "lookup": "exact", "value": "inactive"}])
    llm = MockLLM(response=response)

    phone = create_mock_product(
        "Phone", 599.50, StatusEnum.INACTIVE, 0, date(2023, 6, 1), is_available=False
    )

    mock_queryset = create_mock_queryset([phone])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("inactive products")

    assert len(result) == 1
    assert result[0].name == "Phone"
    assert result[0].status == StatusEnum.INACTIVE


@pytest.mark.asyncio
async def test_lookup_eq():
    response = json.dumps([{"field": "price", "lookup": "eq", "value": 999.99}])
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products with price exactly 999.99")

    assert len(result) == 1
    assert result[0].price == LAPTOP_PRICE


@pytest.mark.asyncio
async def test_lookup_neq():
    response = json.dumps([{"field": "status", "lookup": "neq", "value": "active"}])
    llm = MockLLM(response=response)

    phone = create_mock_product(
        "Phone", 599.50, StatusEnum.INACTIVE, 0, date(2023, 6, 1), is_available=False
    )
    tablet = create_mock_product(
        "Tablet", 799.00, StatusEnum.PENDING, 5, date(2024, 3, 20), is_available=True
    )

    mock_queryset = create_mock_queryset([phone, tablet])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products not active")

    assert len(result) == EXPECTED_COUNT_TWO
    statuses = {p.status for p in result}
    assert StatusEnum.ACTIVE not in statuses


@pytest.mark.asyncio
async def test_lookup_gt():
    response = json.dumps([{"field": "price", "lookup": "gt", "value": 700.0}])
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products with price greater than 700")

    assert len(result) == 1
    assert result[0].price > PRICE_SEVEN_HUNDRED


@pytest.mark.asyncio
async def test_lookup_gte():
    response = json.dumps([{"field": "price", "lookup": "gte", "value": 799.00}])
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )
    tablet = create_mock_product(
        "Tablet", 799.00, StatusEnum.PENDING, 5, date(2024, 3, 20), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop, tablet])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products with price 799 or higher")

    assert len(result) == EXPECTED_COUNT_TWO
    prices = {p.price for p in result}
    assert TABLET_PRICE in prices
    assert LAPTOP_PRICE in prices


@pytest.mark.asyncio
async def test_lookup_lt():
    response = json.dumps([{"field": "price", "lookup": "lt", "value": 700.0}])
    llm = MockLLM(response=response)

    phone = create_mock_product(
        "Phone", 599.50, StatusEnum.INACTIVE, 0, date(2023, 6, 1), is_available=False
    )

    mock_queryset = create_mock_queryset([phone])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products cheaper than 700")

    assert len(result) == 1
    assert result[0].price < PRICE_SEVEN_HUNDRED


@pytest.mark.asyncio
async def test_lookup_lte():
    response = json.dumps([{"field": "price", "lookup": "lte", "value": 599.50}])
    llm = MockLLM(response=response)

    phone = create_mock_product(
        "Phone", 599.50, StatusEnum.INACTIVE, 0, date(2023, 6, 1), is_available=False
    )

    mock_queryset = create_mock_queryset([phone])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products with price 599.50 or less")

    assert len(result) == 1
    assert result[0].price <= PHONE_PRICE


@pytest.mark.asyncio
async def test_lookup_contains():
    response = json.dumps([{"field": "name", "lookup": "contains", "value": "Lap"}])
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products containing Lap")

    assert len(result) == 1
    assert "Lap" in result[0].name


@pytest.mark.asyncio
async def test_lookup_icontains():
    response = json.dumps([{"field": "name", "lookup": "icontains", "value": "lap"}])
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products containing lap (case insensitive)")

    assert len(result) == 1
    assert "Lap" in result[0].name


@pytest.mark.asyncio
async def test_lookup_startswith():
    response = json.dumps([{"field": "name", "lookup": "startswith", "value": "Lap"}])
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products starting with Lap")

    assert len(result) == 1
    assert result[0].name.startswith("Lap")


@pytest.mark.asyncio
async def test_lookup_istartswith():
    response = json.dumps([{"field": "name", "lookup": "istartswith", "value": "lap"}])
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products starting with lap (case insensitive)")

    assert len(result) == 1
    assert result[0].name.lower().startswith("lap")


@pytest.mark.asyncio
async def test_lookup_endswith():
    response = json.dumps([{"field": "name", "lookup": "endswith", "value": "top"}])
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products ending with top")

    assert len(result) == 1
    assert result[0].name.endswith("top")


@pytest.mark.asyncio
async def test_lookup_iendswith():
    response = json.dumps([{"field": "name", "lookup": "iendswith", "value": "TOP"}])
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products ending with TOP (case insensitive)")

    assert len(result) == 1
    assert result[0].name.lower().endswith("top")


@pytest.mark.asyncio
async def test_lookup_isnull():
    response = json.dumps([{"field": "quantity", "lookup": "isnull", "value": True}])
    llm = MockLLM(response=response)

    phone = create_mock_product(
        "Phone", 599.50, StatusEnum.INACTIVE, 0, date(2023, 6, 1), is_available=False
    )

    mock_queryset = create_mock_queryset([phone])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products with null quantity")

    assert len(result) == 1
    assert result[0].quantity == 0


@pytest.mark.asyncio
async def test_lookup_regex():
    response = json.dumps([{"field": "name", "lookup": "regex", "value": "^L.*p$"}])
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products matching regex ^L.*p$")

    assert len(result) == 1
    assert result[0].name == "Laptop"


@pytest.mark.asyncio
async def test_lookup_iregex():
    response = json.dumps([{"field": "name", "lookup": "iregex", "value": "^l.*p$"}])
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop])
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(queryset=mock_queryset, llm=llm)
    result: list[Product] = await retriever.executor.asearch("products matching case-insensitive regex ^l.*p$")

    assert len(result) == 1
    assert result[0].name == "Laptop"


@pytest.mark.asyncio
async def test_custom_adapter():
    """Test custom adapter functionality."""
    from amsdal_ml.ml_retrievers.adapters import DefaultRetrieverAdapter

    class TestCustomAdapter(DefaultRetrieverAdapter):
        def get_response_schema(self, base_schema: dict[str, Any]) -> dict[str, Any]:
            base_schema["custom_test_field"] = "test_value"
            return base_schema

    response = json.dumps([{"field": "price", "lookup": "gte", "value": 800.0}])
    llm = MockLLM(response=response)

    laptop = create_mock_product(
        "Laptop", 999.99, StatusEnum.ACTIVE, 10, date(2024, 1, 15), is_available=True
    )

    mock_queryset = create_mock_queryset([laptop])
    custom_adapter = TestCustomAdapter()
    retriever: NLQueryRetriever[Product] = NLQueryRetriever(
        queryset=mock_queryset, llm=llm, adapter=custom_adapter
    )
    result: list[Product] = await retriever.executor.asearch("expensive products")

    assert "custom_test_field" in retriever.executor.response_schema
    assert retriever.executor.response_schema["custom_test_field"] == "test_value"

    assert len(result) == 1
    assert result[0].price >= PRICE_EIGHT_HUNDRED
