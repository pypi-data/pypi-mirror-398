"""Utilities for data cleaning, serialization, and table rendering."""

import inspect
from collections.abc import Callable
from datetime import date
from datetime import datetime
from typing import Any

from amsdal_models.classes.model import Model
from typing_extensions import TypedDict

CleanedRecord = dict[str, Any]

MAX_CELL_LENGTH = 40
MAX_OBJECT_ID_LENGTH = 10
MAX_DICT_STR_LENGTH = 100


class Column(TypedDict):
    """TypedDict for defining table columns."""
    field: str | Callable[[Any], str]
    title: str


async def async_serialize_model(model: Model) -> dict[str, Any]:
    """
    Asynchronously serializes a Model instance into a dictionary.

    Handles async fields and nested models by extracting their display_name.

    Args:
        model: The Model instance to serialize.

    Returns:
        A dictionary representation of the model.
    """
    data = {}
    for field_name in model.__fields__:
        value = getattr(model, field_name)
        if inspect.isawaitable(value):
            value = await value
        if isinstance(value, Model):
            display_name = value.display_name
            if inspect.isawaitable(display_name):
                display_name = await display_name
            data[field_name] = display_name
        else:
            data[field_name] = value
    return data


def clean_data(val: Any) -> Any:
    """
    Cleans data for serialization/display.

    Handles dates by formatting them, truncates strings and dicts to prevent overflow,
    handles object IDs in dicts, and escapes markdown characters.

    Args:
        val: The value to clean.

    Returns:
        The cleaned value.
    """
    if val is None:
        return ""
    if isinstance(val, (datetime, date)):
        if isinstance(val, datetime):
            return val.strftime('%Y-%m-%dT%H:%M:%S')
        return val.isoformat()
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    if isinstance(val, dict):
        ref = val.get('ref')
        if isinstance(ref, dict):
            obj_id = ref.get('object_id', 'Object')
            return (
                obj_id[:MAX_OBJECT_ID_LENGTH] + '...'
                if len(obj_id) > MAX_OBJECT_ID_LENGTH
                else obj_id
            )
        s_val = str(val)
        return (
            s_val[:MAX_DICT_STR_LENGTH] + '...'
            if len(s_val) > MAX_DICT_STR_LENGTH
            else s_val
        )

    s = str(val)
    s = s.replace('\n', ' ').replace('\r', '').replace('|', r'\|')
    return s[: MAX_CELL_LENGTH - 3] + "..." if len(s) > MAX_CELL_LENGTH else s


async def serialize_and_clean_record(
    record: Model | dict[str, Any],
) -> CleanedRecord:
    """
    Serializes a Model or dict and cleans its values for display/usage.

    Handles both Model instances (by serializing them asynchronously) and plain dicts,
    then applies cleaning to all values.

    Args:
        record: The Model instance or dictionary to serialize and clean.

    Returns:
        A dictionary with cleaned field values.
    """
    if isinstance(record, Model):
        data = await async_serialize_model(record)
    elif isinstance(record, dict):
        data = record
    else:
        msg = f"Unsupported record type: {type(record)}"
        raise ValueError(msg)

    return {k: clean_data(v) for k, v in data.items()}


def render_markdown_table(
    records: list[CleanedRecord],
    columns: list[Column] | None = None,
    fields: list[str] | None = None,
) -> str:
    """
    Renders a list of cleaned records as a Markdown table.

    If columns are not provided, infers them from the first record's keys or uses the fields list.
    Handles callable fields for custom value extraction.

    Args:
        records: List of cleaned records to render.
        columns: Optional list of column definitions with field and title.
        fields: Optional list of field names to include if columns not provided.

    Returns:
        A string containing the Markdown table.
    """
    if not records:
        return "No records found."

    if columns is None:
        if fields:
            columns = [
                {"field": f, "title": f.replace('_', ' ').title()} for f in fields
            ]
        else:
            headers = list(records[0].keys())
            columns = [
                {"field": h, "title": h.replace('_', ' ').title()} for h in headers
            ]

    if not columns:
        return "No columns to display."

    rows: list[dict[str, Any]] = []
    for record in records:
        row: dict[str, Any] = {}
        for col in columns:
            field = col["field"]
            if callable(field):
                value = field(record)
            else:
                value = record.get(field, '')
            row[col["title"]] = value
        rows.append(row)

    headers = list(rows[0].keys())

    col_widths: dict[str, int] = {h: len(h) for h in headers}

    for row in rows:
        for h in headers:
            val = str(row.get(h, ''))
            col_widths[h] = max(col_widths[h], len(val))

    table_lines: list[str] = []
    table_lines.append(
        "| " + " | ".join(h.ljust(col_widths[h]) for h in headers) + " |"
    )
    table_lines.append(
        "| " + " | ".join("-" * col_widths[h] for h in headers) + " |"
    )
    for row in rows:
        table_lines.append(
            "| " + " | ".join(str(row[h]).ljust(col_widths[h]) for h in headers) + " |"
        )

    return '\n'.join(table_lines)
