"""
EnumField - Field for enum types with automatic parsing.

Handles parsing strings to enum values, with fallback to default
when parsing fails.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from djb.config.field import ConfigFieldABC


class EnumField(ConfigFieldABC):
    """Field for enum types with automatic parsing."""

    def __init__(self, enum_class: type[Enum], **kwargs: Any):
        super().__init__(**kwargs)
        self.enum_class = enum_class

    def normalize(self, value: Any) -> Any:
        """Parse string to enum."""
        if isinstance(value, self.enum_class):
            return value
        # Use the enum's parse method if available (like Mode.parse)
        if hasattr(self.enum_class, "parse"):
            parsed = self.enum_class.parse(value)  # type: ignore[attr-defined]
            if parsed is not None:
                return parsed
        # Fall back to trying to create enum from value
        try:
            return self.enum_class(value)
        except (ValueError, KeyError):
            return self.get_default()
