"""Utility for flattening nested dictionaries."""

from __future__ import annotations

from djb.types import NestedDict


def flatten_dict(d: NestedDict, parent_key: str = "") -> dict[str, str]:
    """Flatten a nested dictionary into a flat dict with uppercase keys.

    Nested keys are joined with underscores. All values are converted to strings.

    Args:
        d: Dictionary to flatten
        parent_key: Prefix for all keys (used during recursion)

    Returns:
        Flat dictionary with uppercase keys

    Example:
        >>> flatten_dict({"db": {"host": "localhost", "port": 5432}})
        {"DB_HOST": "localhost", "DB_PORT": "5432"}
    """
    items: list[tuple[str, str]] = []
    for key, value in d.items():
        new_key = f"{parent_key}_{key}".upper() if parent_key else key.upper()
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key).items())
        else:
            items.append((new_key, str(value)))
    return dict(items)
