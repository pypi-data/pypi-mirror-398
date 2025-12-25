from typing import Any

from amsdal_models.classes.model import Model
from amsdal_models.querysets.base_queryset import QuerySetBase
from pydantic import BaseModel
from pydantic import Field

from amsdal_ml.ml_models.openai_model import OpenAIModel
from amsdal_ml.ml_retrievers.query_retriever import NLQueryRetriever


class TestModel(BaseModel):
    simple_string: str = Field(..., title="Simple String")
    simple_int: int = Field(..., title="Simple Integer")

    union_with_list: str | list[int] = Field(..., title="Union with List")
    union_with_nested_list: dict[str, int] | list[str] = Field(
        ..., title="Union with Nested List"
    )
    union_list_dict: list[str] | dict[str, str] = Field(..., title="Union List Dict")

    dict_with_list_value: dict[str, list[int]] = Field(
        ..., title="Dict with List Value"
    )
    dict_with_union_list: dict[str, str | list[int]] = Field(
        ..., title="Dict with Union List"
    )

    list_of_unions_with_list: list[str | list[int]] = Field(
        ..., title="List of Unions with List"
    )
    list_of_dicts_with_list: list[dict[str, list[str]]] = Field(
        ..., title="List of Dicts with List"
    )

    tuple_with_list: tuple[str, list[int]] = Field(..., title="Tuple with List")
    set_with_list: set[list[str]] = Field(..., title="Set with List")

    complex_union: dict[str, list[int]] | list[dict[str, str]] = Field(
        ..., title="Complex Union"
    )

    nested_dict_with_list: dict[str, dict[str, list[int]]] = Field(
        ..., title="Nested Dict with List"
    )
    union_of_lists: list[str] | list[int] = Field(..., title="Union of Lists")
    list_in_tuple: tuple[list[str], str] = Field(..., title="List in Tuple")
    set_of_unions: set[str | list[int]] = Field(..., title="Set of Unions")
    complex_nested: dict[str, list[int] | str] | list[dict[str, str]] = Field(
        ..., title="Complex Nested"
    )

    optional_union_with_list: str | list[int] | None = Field(
        None, title="Optional Union with List"
    )
    list_of_lists: list[list[str]] = Field(..., title="List of Lists")
    dict_list_union: dict[str, list[int] | str] = Field(..., title="Dict List Union")

    triple_nested: dict[str, list[dict[str, list[int]]]] = Field(
        ..., title="Triple Nested"
    )
    union_complex: str | list[int] | dict[str, list[str]] = Field(
        ..., title="Union Complex"
    )


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


def test_nested_list_skipping():
    llm = OpenAIModel()
    llm.setup()
    queryset = MockQuerySet(TestModel)

    retriever = NLQueryRetriever(llm=llm, queryset=queryset)
    schema = retriever.executor.search_schema

    schema_dict = {item["name"]: item["type"] for item in schema}

    test_cases = [
        ("simple_string", "string", True),
        ("simple_int", "number", True),
        ("union_with_list", None, False),
        ("union_with_nested_list", None, False),
        ("union_list_dict", None, False),
        ("dict_with_list_value", None, False),
        ("dict_with_union_list", None, False),
        ("list_of_unions_with_list", None, False),
        ("list_of_dicts_with_list", None, False),
        ("tuple_with_list", None, False),
        ("set_with_list", None, False),
        ("complex_union", None, False),
        ("nested_dict_with_list", None, False),
        ("union_of_lists", None, False),
        ("list_in_tuple", None, False),
        ("set_of_unions", None, False),
        ("complex_nested", None, False),
        ("optional_union_with_list", None, False),
        ("list_of_lists", None, False),
        ("dict_list_union", None, False),
        ("triple_nested", None, False),
        ("union_complex", None, False),
    ]

    for field_name, expected_type, should_be_present in test_cases:
        if should_be_present:
            assert (
                field_name in schema_dict
            ), f"{field_name} should be present"  # noqa: S101
            assert (
                schema_dict[field_name] == expected_type
            ), f"{field_name} should have type {expected_type}"  # noqa: S101
        else:
            assert (
                field_name not in schema_dict
            ), f"{field_name} should be absent"  # noqa: S101


if __name__ == "__main__":
    test_nested_list_skipping()
