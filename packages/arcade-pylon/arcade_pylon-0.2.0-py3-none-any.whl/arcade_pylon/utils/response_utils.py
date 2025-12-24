"""Response transformation utilities."""

from typing import Any


def remove_none_values_recursive(data: Any) -> Any:
    """Recursively remove None values and empty nested dicts (preserves empty lists)."""
    if isinstance(data, dict):
        return {
            k: remove_none_values_recursive(v) for k, v in data.items() if v is not None and v != {}
        }
    if isinstance(data, list):
        return [remove_none_values_recursive(item) for item in data if item is not None]
    return data
