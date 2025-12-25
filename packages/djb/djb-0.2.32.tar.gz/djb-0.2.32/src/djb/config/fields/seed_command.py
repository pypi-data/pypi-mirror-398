"""
SeedCommandField - Field for seed commands with 'module.path:attribute' validation.
"""

from __future__ import annotations

import re
from typing import Any

from djb.config.field import ConfigFieldABC, ConfigValidationError

# Pattern for 'module.path:attribute' format
# Module path: one or more dotted identifiers (e.g., myapp.seeds)
# Attribute: valid Python identifier (e.g., run_seeds)
SEED_COMMAND_PATTERN = re.compile(
    r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*:[a-zA-Z_][a-zA-Z0-9_]*$"
)


class SeedCommandField(ConfigFieldABC):
    """Field for seed_command with 'module.path:attribute' validation."""

    def validate(self, value: Any) -> None:
        """Validate seed_command as 'module.path:attribute' format."""
        if not self._require_string(value):
            return
        if not SEED_COMMAND_PATTERN.match(value):
            raise ConfigValidationError(
                f"seed_command must be 'module.path:attribute' format. Got: {value!r}"
            )
