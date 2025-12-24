"""Response transformation utilities."""

from typing import Any


def remove_none_values_recursive(data: Any) -> Any:
    """Recursively remove None values and empty nested dicts (preserves empty lists)."""
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if value is not None:
                cleaned_value = remove_none_values_recursive(value)
                if cleaned_value != {}:
                    cleaned[key] = cleaned_value
        return cleaned
    if isinstance(data, list):
        return [remove_none_values_recursive(item) for item in data if item is not None]
    return data
