import uuid
from typing import Any

import pytest

from amsdal_ml.ml_models.utils import ResponseFormat
from amsdal_ml.ml_retrievers.query_retriever import NLQueryExecutor
from tests.agents_tests.test_fakes import FakeModel


def get_base_id() -> int:
    return uuid.uuid4().int % (10**9)


BASE_ID = get_base_id()


# Model configurations fixture - only model data, no test scenarios
@pytest.fixture
def model_configs() -> dict[str, dict[str, Any]]:
    from models.author import Author  # type: ignore[import-not-found]
    from models.book import Book  # type: ignore[import-not-found]
    from models.product import Product  # type: ignore[import-not-found]
    from models.user import User  # type: ignore[import-not-found]
    from models.vehicle import Vehicle  # type: ignore[import-not-found]

    return {
        'author': {
            'model': Author,
            'items': [
                Author(id=BASE_ID + 1, name='Author One', email='one@example.com'),
                Author(id=BASE_ID + 2, name='Author Two', email='two@example.com'),
                Author(id=BASE_ID + 3, name='Author Three', email='three@example.com'),
            ],
            'fields': ['name', 'email'],
            'fields_info': {
                'name': 'The name of the author',
                'email': 'The email address of the author',
            },
        },
        'book': {
            'model': Book,
            'items': [
                Book(id=BASE_ID + 4, title='Book Alpha', author_id=BASE_ID + 1, published_year=2020),
                Book(id=BASE_ID + 5, title='Book Beta', author_id=BASE_ID + 2, published_year=2021),
                Book(id=BASE_ID + 6, title='Book Gamma', author_id=BASE_ID + 1, published_year=2022),
            ],
            'fields': ['title', 'published_year'],
            'fields_info': {
                'title': 'The title of the book',
                'published_year': 'The year the book was published',
            },
        },
        'user': {
            'model': User,
            'items': [
                User(id=BASE_ID + 7, name='User Active', email='active@example.com', age=25, is_active=True),
                User(id=BASE_ID + 8, name='User Inactive', email='inactive@example.com', age=30, is_active=False),
                User(id=BASE_ID + 9, name='User Young', email='young@example.com', age=20, is_active=True),
            ],
            'fields': ['name', 'age', 'is_active'],
            'fields_info': {
                'name': 'The name of the user',
                'age': 'The age of the user',
                'is_active': 'Whether the user is active',
            },
        },
        'product': {
            'model': Product,
            'items': [
                Product(id=BASE_ID + 10, name='Product Cheap', price=10.0, category='Electronics', in_stock=True),
                Product(id=BASE_ID + 11, name='Product Expensive', price=100.0, category='Electronics', in_stock=False),
                Product(id=BASE_ID + 12, name='Product Book', price=20.0, category='Books', in_stock=True),
            ],
            'fields': ['name', 'price', 'in_stock'],
            'fields_info': {
                'name': 'The name of the product',
                'price': 'The price of the product',
                'in_stock': 'Whether the product is in stock',
            },
        },
        'vehicle': {
            'model': Vehicle,
            'items': [
                Vehicle(
                    id=BASE_ID + 13,
                    make='Toyota',
                    model='Camry',
                    year=2022,
                    engine_type='gasoline',
                    fuel_efficiency=30.0,
                    features=['airbags', 'ABS'],
                    specs={'engine_size': '2.5', 'transmission': 'automatic'},
                    is_available=True,
                    price=25000.0,
                    warranty_years=5,
                    maintenance_schedule={'5000': {'oil_change': 'yes'}, '10000': {'tire_rotation': 'yes'}},
                    safety_ratings={'nhtsa': 5, 'iihs': 4},
                    options=['navigation', 'backup_camera'],
                ),
                Vehicle(
                    id=BASE_ID + 14,
                    make='Tesla',
                    model='Model 3',
                    year=2023,
                    engine_type='electric',
                    fuel_efficiency=None,
                    features=['autopilot', 'supercharger'],
                    specs={'battery_range': '358', 'charging_time': '5 hours'},
                    is_available=False,
                    price=45000.0,
                    warranty_years=8,
                    maintenance_schedule=None,
                    safety_ratings={'nhtsa': 5, 'iihs': 5},
                    options=['sunroof', 'leather_seats'],
                ),
            ],
            'fields': ['make', 'model', 'engine_type', 'is_available'],
            'fields_info': {
                'make': 'The manufacturer of the vehicle',
                'model': 'The model name of the vehicle',
                'engine_type': 'The type of engine (gasoline, diesel, electric, hybrid)',
                'is_available': 'Whether the vehicle is available for purchase',
            },
        },
    }


# Test cases - clean parametrize data
def get_test_cases() -> list[tuple[str, str, str, list[int]]]:
    """
    Generate test cases for parametrize.
    Returns: list of (model_name, query, llm_response, expected_ids)
    """

    return [
        # Author test cases
        (
            'author',
            'find authors with one in name',
            '{"filters": [{"field": "name", "lookup": "icontains", "value": "One"}]}',
            [BASE_ID + 1],
        ),
        (
            'author',
            'find all authors',
            '{"filters": []}',
            [BASE_ID + 1, BASE_ID + 2, BASE_ID + 3],
        ),
        (
            'author',
            'invalid response',
            '{"invalid": "json"}',
            [BASE_ID + 1, BASE_ID + 2, BASE_ID + 3],
        ),
        # Book test cases
        (
            'book',
            'find books published after 2020',
            '{"filters": [{"field": "published_year", "lookup": "gt", "value": 2020}]}',
            [BASE_ID + 5, BASE_ID + 6],
        ),
        (
            'book',
            'find all books',
            '{"filters": []}',
            [BASE_ID + 4, BASE_ID + 5, BASE_ID + 6],
        ),
        (
            'book',
            'malformed json',
            '{"filters": [{"field": "published_year", "lookup": "gt", "value": 2020"}',
            [BASE_ID + 4, BASE_ID + 5, BASE_ID + 6],
        ),
        # User test cases
        (
            'user',
            'find active users',
            '{"filters": [{"field": "is_active", "lookup": "eq", "value": true}]}',
            [BASE_ID + 7, BASE_ID + 9],
        ),
        (
            'user',
            'find users older than 22',
            '{"filters": [{"field": "age", "lookup": "gt", "value": 22}]}',
            [BASE_ID + 7, BASE_ID + 8],
        ),
        (
            'user',
            'find all users',
            '{"filters": []}',
            [BASE_ID + 7, BASE_ID + 8, BASE_ID + 9],
        ),
        # Product test cases
        (
            'product',
            'find products in stock',
            '{"filters": [{"field": "in_stock", "lookup": "eq", "value": true}]}',
            [BASE_ID + 10, BASE_ID + 12],
        ),
        (
            'product',
            'find cheap products',
            '{"filters": [{"field": "price", "lookup": "lt", "value": 50.0}]}',
            [BASE_ID + 10, BASE_ID + 12],
        ),
        (
            'product',
            'find all products',
            '{"filters": []}',
            [BASE_ID + 10, BASE_ID + 11, BASE_ID + 12],
        ),
        # Vehicle test cases
        (
            'vehicle',
            'find gasoline vehicles',
            '{"filters": [{"field": "engine_type", "lookup": "eq", "value": "gasoline"}]}',
            [BASE_ID + 13],
        ),
        (
            'vehicle',
            'find available vehicles',
            '{"filters": [{"field": "is_available", "lookup": "eq", "value": true}]}',
            [BASE_ID + 13],
        ),
        (
            'vehicle',
            'find vehicles from 2023',
            '{"filters": [{"field": "year", "lookup": "eq", "value": 2023}]}',
            [BASE_ID + 14],
        ),
        (
            'vehicle',
            'find all vehicles',
            '{"filters": []}',
            [BASE_ID + 13, BASE_ID + 14],
        ),
    ]


TEST_CASES = get_test_cases()


@pytest.mark.parametrize(
    'model_name,query,llm_response,expected_ids',
    TEST_CASES,
    ids=[f'{model}-{query}' for model, query, _, _ in TEST_CASES],
)
@pytest.mark.parametrize(
    'response_format',
    [
        ResponseFormat.JSON_OBJECT,
        ResponseFormat.JSON_SCHEMA,
        ResponseFormat.PLAIN_TEXT,
    ],
    ids=['json_object', 'json_schema', 'plain_text'],
)
@pytest.mark.asyncio
async def test_nl_query_models(
    async_test_amsdal_manager,  # noqa: ARG001
    model_configs: dict[str, dict[str, Any]],
    model_name: str,
    query: str,
    llm_response: str,
    expected_ids: list[int],
    response_format: ResponseFormat,
) -> None:
    model_config = model_configs[model_name]
    model_class = model_config['model']
    items = model_config['items']
    fields = model_config['fields']
    fields_info = model_config['fields_info']

    # Save all items
    for item in items:
        await item.asave(force_insert=True)

    # Adjust LLM response based on format
    if response_format == ResponseFormat.PLAIN_TEXT:
        adjusted_response = f'```json\n{llm_response}\n```'
    else:
        adjusted_response = llm_response

    # Setup fake LLM with mock response
    llm = FakeModel(async_mode=True, responses={query: adjusted_response})
    llm.setup()

    # Create executor
    executor = NLQueryExecutor(
        llm=llm,
        queryset=model_class.objects.all(),
        fields=fields,
        fields_info=fields_info,
        llm_response_format=response_format,
    )

    # Execute NL search
    nl_results: list[Any] = await executor.asearch(query)

    # Get actual IDs from results
    nl_ids = tuple(sorted([item.id for item in nl_results]))
    expected_ids_sorted = tuple(sorted(expected_ids))

    # Assert IDs match
    assert nl_ids == expected_ids_sorted, f'Expected IDs {expected_ids_sorted}, got {nl_ids}'
