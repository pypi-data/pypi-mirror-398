"""Response cleaning utilities for Linear toolkit."""

from typing import Any


def remove_none_values(data: dict[str, Any]) -> dict[str, Any]:
    """Remove None values from a dictionary (shallow)."""
    return {k: v for k, v in data.items() if v is not None}


def remove_none_values_recursive(data: Any) -> Any:
    """Recursively remove None values and empty collections from data structures.

    This function cleans tool outputs by removing None values, empty lists,
    and empty dictionaries to reduce response payload size.
    """
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            cleaned_value = remove_none_values_recursive(v)
            if cleaned_value is not None and cleaned_value != [] and cleaned_value != {}:
                cleaned[k] = cleaned_value
        return cleaned

    if isinstance(data, list):
        cleaned_list = []
        for item in data:
            cleaned_item = remove_none_values_recursive(item)
            if cleaned_item is not None:
                cleaned_list.append(cleaned_item)
        return cleaned_list

    return data
