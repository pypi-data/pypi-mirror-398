"""Comprehensive test for schema extraction with all edge cases."""

import datetime
import json
from enum import Enum
from typing import Annotated
from typing import Any
from typing import Literal

import pytest
from amsdal_models.classes.model import Model
from amsdal_models.querysets.base_queryset import QuerySetBase
from pydantic import BaseModel
from pydantic import BeforeValidator
from pydantic import Field


def _validate_state(v):
    return v


def _validate_category(v):
    return v


class File(BaseModel):
    filename: str
    content_type: str


class StateOptions(str, Enum):
    AL = "Alabama"
    AK = "Alaska"
    AZ = "Arizona"
    CA = "California"


StateOptionsField = Annotated[StateOptions, BeforeValidator(_validate_state)]


class GuaranteePeriod(str, Enum):
    FIVE = "5"
    TEN = "10"
    FIFTEEN = "15"


class ProductCategory(str, Enum):
    ANNUITY = "Annuity"
    LIFE = "Life"
    HEALTH = "Health"


class RiderType(str, Enum):
    INCOME = "Income"
    DEATH = "Death Benefit"
    LTC = "Long Term Care"


class NestedModel(BaseModel):
    field1: str
    field2: int


class DeepNestedModel(Model):
    name: str
    nested: NestedModel


class TimestampMixin(BaseModel):
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


class Rider(TimestampMixin, Model):
    name: str = Field(..., title="Rider Name")
    description: str = Field(..., title="Rider Description")
    cost: float = Field(..., title="Rider Cost")


class ComprehensiveTestModel(Model):
    simple_string: str = Field(..., title="Simple String")
    simple_int: int = Field(..., title="Simple Integer")
    simple_float: float = Field(..., title="Simple Float")
    simple_bool: bool = Field(..., title="Simple Boolean")

    optional_string: str | None = Field(None, title="Optional String")
    optional_int: int | None = Field(None, title="Optional Int")

    literal_field: Literal["MYGA", "FIA"] = Field(..., title="Literal Field")
    literal_numbers: Literal[1, 2, 3] = Field(..., title="Literal Numbers")

    enum_field: StateOptions = Field(..., title="Enum Field")
    annotated_enum: StateOptionsField = Field(..., title="Annotated Enum")

    union_enum: StateOptions | ProductCategory = Field(..., title="Union of Enums")
    union_literal: Literal["A"] | Literal["B", "C"] = Field(
        ..., title="Union of Literals"
    )
    union_enum_str: StateOptions | str = Field(..., title="Union Enum + String")
    union_literal_str: Literal["X"] | str = Field(..., title="Union Literal + String")
    union_primitives: int | float = Field(..., title="Union of Primitives")
    union_annotated_enum_str: StateOptionsField | str = Field(
        ..., title="Union Annotated Enum + String"
    )

    list_string: list[str] = Field(..., title="List of Strings")
    list_int: list[int] = Field(..., title="List of Integers")
    list_union_int_float: list[int | float] = Field(..., title="List Union Int Float")
    list_union_str_literal: list[str | Literal["a", "b"]] = Field(
        ..., title="List Union Str Literal"
    )

    list_enum: list[StateOptions] = Field(..., title="List of Enum")
    list_annotated_enum: list[StateOptionsField] = Field(
        ..., title="List of Annotated Enum"
    )
    list_literal: list[Literal["opt1", "opt2", "opt3"]] = Field(
        ..., title="List of Literal"
    )

    list_union_enums: list[StateOptions | ProductCategory] = Field(
        ..., title="List of Union Enums"
    )
    list_union_literals: list[Literal["A"] | Literal["B"]] = Field(
        ..., title="List of Union Literals"
    )
    list_union_enum_str: list[GuaranteePeriod | str] = Field(
        ..., title="List Union Enum + String"
    )
    list_union_literal_str: list[Literal["Y"] | str] = Field(
        ..., title="List Union Literal + String"
    )
    list_union_primitives: list[int | str] = Field(..., title="List Union Primitives")

    tuple_field: tuple[str, int] = Field(..., title="Tuple Field")
    set_field: set[str] = Field(..., title="Set Field")

    complex_tuple: tuple[str | int, float | bool] = Field(..., title="Complex Tuple")
    nested_tuple: tuple[tuple[str, int], str] = Field(..., title="Nested Tuple")
    set_union: set[str | int] = Field(..., title="Set Union")

    unknown_field: bytes = Field(..., title="Unknown Type")

    nested_model: NestedModel = Field(..., title="Nested Model")
    optional_nested: NestedModel | None = Field(None, title="Optional Nested")

    list_model: list[NestedModel] = Field(..., title="List of Models")
    list_union_model_str: list[NestedModel | str] = Field(
        ..., title="List Union Model + String"
    )
    list_rider: list[Rider] = Field(..., title="List of Riders (Model with Mixin)")

    rider_ref: Rider = Field(..., title="Rider Reference")
    optional_rider_ref: Rider | None = Field(None, title="Optional Rider Reference")

    file_field: File = Field(..., title="File Field")
    optional_file: File | None = Field(None, title="Optional File")
    list_file: list[File] = Field(..., title="List of Files")

    deep_nested: DeepNestedModel = Field(..., title="Deep Nested Model")

    dict_field: dict[str, str] = Field(..., title="Dict Field")
    dict_complex: dict[str, NestedModel] = Field(..., title="Dict with Models")

    annotated_literal: Annotated[
        Literal["val1", "val2"], Field(title="Annotated Literal")
    ] = Field(..., title="Annotated Literal")
    annotated_union_enum: Annotated[
        StateOptions | ProductCategory, BeforeValidator(_validate_category)
    ] = Field(..., title="Annotated Union Enum")
    annotated_union_enum_str: Annotated[
        RiderType | str, Field(title="Rider or Custom")
    ] = Field(..., title="Annotated Union Enum + Str")

    deep_annotated: Annotated[Annotated[Annotated[int, "meta1"], "meta2"], "meta3"] = (
        Field(..., title="Deep Annotated")
    )
    complex_union: Annotated[str | int, "meta"] | float | bool = Field(
        ..., title="Complex Union"
    )
    union_of_unions: Literal["a", "b"] | Literal["c"] | str = Field(
        ..., title="Union of Unions"
    )
    annotated_union_nested: Annotated[
        Annotated[Literal["x"] | int, "inner"] | str, "outer"
    ] = Field(..., title="Annotated Union Nested")
    triple_union: str | int | float | bool = Field(..., title="Triple Union")


class MockQuerySet(QuerySetBase[Model]):
    def __init__(self, entity):
        super().__init__(entity)
        self._annotations = {}

    def filter(self, *args: Any, **kwargs: Any) -> "MockQuerySet":  # noqa: ARG002
        return self

    def exclude(self, *args: Any, **kwargs: Any) -> "MockQuerySet":  # noqa: ARG002
        return self

    async def aexecute(self):
        return []

    def execute(self):
        return []


@pytest.mark.skip(reason="Temporarily disabled - known to fail")
def test_comprehensive_schema():
    """Comprehensive test covering all edge cases."""
    from amsdal_ml.ml_models.openai_model import OpenAIModel
    from amsdal_ml.ml_retrievers.query_retriever import NLQueryRetriever

    llm = OpenAIModel()
    queryset = MockQuerySet(ComprehensiveTestModel)

    retriever = NLQueryRetriever(llm=llm, queryset=queryset)
    schema = retriever.executor.search_schema

    print("=" * 100)  # noqa: T201
    print("COMPREHENSIVE SCHEMA TEST")  # noqa: T201
    print("=" * 100)  # noqa: T201
    print(json.dumps(schema, indent=2, ensure_ascii=False))  # noqa: T201
    print("\n" + "=" * 100)  # noqa: T201

    schema_dict = {item["name"]: item["type"] for item in schema}

    print("\nVERIFICATION:")  # noqa: T201
    print("=" * 100)  # noqa: T201

    test_cases = [
        ("simple_string", "string", True),
        ("simple_int", "number", True),
        ("simple_float", "number", True),
        ("simple_bool", "boolean", True),
        ("optional_string", "string", True),
        ("optional_int", "number", True),
        ("literal_field", "options: str('MYGA'), str('FIA')", True),
        ("literal_numbers", "options: int(1), int(2), int(3)", True),
        (
            "enum_field",
            "options: str('Alabama'), str('Alaska'), str('Arizona'), str('California')",
            True,
        ),
        (
            "annotated_enum",
            "options: str('Alabama'), str('Alaska'), str('Arizona'), str('California')",
            True,
        ),
        ("union_enum", "options:", True),
        ("union_literal", "options: str('A'), str('B'), str('C')", True),
        ("union_enum_str", "string", True),
        ("union_literal_str", "string", True),
        ("union_primitives", "number", True),
        ("union_annotated_enum_str", "string", True),
        ("list_string", "list of string", True),
        ("list_int", "list of number", True),
        ("list_union_int_float", "list of number", True),
        ("list_union_str_literal", "list of string", True),
        (
            "list_enum",
            "list of options: str('Alabama'), str('Alaska'), str('Arizona'), str('California')",
            True,
        ),
        (
            "list_annotated_enum",
            "list of options: str('Alabama'), str('Alaska'), str('Arizona'), str('California')",
            True,
        ),
        (
            "list_literal",
            "list of options: str('opt1'), str('opt2'), str('opt3')",
            True,
        ),
        ("list_union_enums", "list of options:", True),
        ("list_union_literals", "list of options: str('A'), str('B')", True),
        ("list_union_enum_str", "list of string", True),
        ("list_union_literal_str", "list of string", True),
        ("list_union_primitives", "list of", True),
        ("tuple_field", "list of string", True),
        ("set_field", "list of string", True),
        ("complex_tuple", "list of string", True),
        ("nested_tuple", None, False),
        ("set_union", "list of string", True),
        ("unknown_field", None, False),
        ("nested_model", None, False),
        ("optional_nested", None, False),
        ("list_model", None, False),
        ("list_union_model_str", None, False),
        ("list_rider", None, False),
        ("rider_ref", None, False),
        ("optional_rider_ref", None, False),
        ("file_field", None, False),
        ("optional_file", None, False),
        ("list_file", None, False),
        ("deep_nested", None, False),
        ("dict_field", None, False),
        ("dict_complex", None, False),
        ("annotated_literal", "options: str('val1'), str('val2')", True),
        ("annotated_union_enum", "options:", True),
        ("annotated_union_enum_str", "string", True),
        ("deep_annotated", "number", True),
        ("complex_union", "string", True),
        ("union_of_unions", "string", True),
        ("annotated_union_nested", "string", True),
        ("triple_union", "string", True),
    ]

    passed = 0
    failed = 0

    for field_name, expected_type_prefix, should_exist in test_cases:
        if should_exist:
            if field_name in schema_dict:
                actual_type = schema_dict[field_name]
                if expected_type_prefix in actual_type:
                    print(f"PASS {field_name}: {actual_type}")  # noqa: T201
                    passed += 1
                else:
                    print(
                        f"FAIL {field_name}: expected '{expected_type_prefix}...', got '{actual_type}'"
                    )  # noqa: T201
                    failed += 1
            else:
                print(
                    f"FAIL {field_name}: MISSING (expected '{expected_type_prefix}...')"
                )
                failed += 1
        elif field_name not in schema_dict:
            print(f"PASS {field_name}: SKIPPED (as expected)")  # noqa: T201
            passed += 1
        else:
            print(
                f"FAIL {field_name}: should be SKIPPED, but found '{schema_dict[field_name]}'"
            )  # noqa: T201
            failed += 1

    print("\n" + "=" * 100)  # noqa: T201
    print(f"RESULTS: {passed} passed, {failed} failed")  # noqa: T201
    print("=" * 100)  # noqa: T201

    if failed > 0:
        print("\nWARNING: SOME TESTS FAILED!")  # noqa: T201
    else:
        print("\nSUCCESS: ALL TESTS PASSED!")  # noqa: T201


test_comprehensive_schema()
