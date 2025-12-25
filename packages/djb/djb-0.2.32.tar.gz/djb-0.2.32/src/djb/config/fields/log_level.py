"""
LogLevelField - Field for log level configuration with validation.

Accepts: error, warning, info, note, debug (case-insensitive).
Silently saves default value during acquisition (no prompting).
"""

from __future__ import annotations

from typing import Any

from djb.config.acquisition import AcquisitionContext, AcquisitionResult
from djb.config.field import ConfigFieldABC, ConfigValidationError

# Valid log levels (lowercase)
VALID_LOG_LEVELS = frozenset({"error", "warning", "info", "note", "debug"})

# Default log level
DEFAULT_LOG_LEVEL = "info"


class LogLevelField(ConfigFieldABC):
    """Field for log level with validation and normalization.

    Accepts: "error", "warning", "info", "note", "debug" (case-insensitive).
    Stores as lowercase string in config files.
    """

    def acquire(self, ctx: AcquisitionContext) -> AcquisitionResult | None:
        """Acquire log_level with silent auto-save (no prompting)."""
        value = ctx.current_value if ctx.current_value else DEFAULT_LOG_LEVEL
        return AcquisitionResult(
            value=value,
            should_save=True,
            source_name=None,
            was_prompted=False,
        )

    def normalize(self, value: Any) -> str:
        """Normalize log level to lowercase string."""
        if isinstance(value, str):
            return value.lower()
        return str(value).lower()

    def validate(self, value: Any) -> None:
        """Validate log level is one of the allowed values."""
        if not self._require_string(value):
            return
        if value.lower() not in VALID_LOG_LEVELS:
            valid = ", ".join(sorted(VALID_LOG_LEVELS))
            raise ConfigValidationError(f"Invalid log_level: {value!r}. Must be one of: {valid}")
