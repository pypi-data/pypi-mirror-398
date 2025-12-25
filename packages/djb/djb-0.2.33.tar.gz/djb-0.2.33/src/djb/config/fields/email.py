"""
EmailField - Field for email addresses with validation.

Uses git config user.email as an external source for value acquisition
and as a resolution fallback.
"""

from __future__ import annotations

import re
from typing import Any

from djb.config.acquisition import GitConfigSource
from djb.config.field import ConfigFieldABC, ConfigValidationError
from djb.config.resolution import ConfigSource, ResolutionContext

# Basic email pattern - allows most valid emails
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailField(ConfigFieldABC):
    """Field for email addresses with format validation.

    Uses git config user.email as an external source and resolution fallback.
    """

    def __init__(self, **kwargs):
        """Initialize with git config fallback source."""
        super().__init__(
            prompt_text="Enter your email",
            validation_hint="expected: user@domain.com",
            external_sources=[GitConfigSource("user.email")],
            **kwargs,
        )
        self._git_source = GitConfigSource("user.email")

    def resolve(self, ctx: ResolutionContext) -> tuple[Any, ConfigSource | None]:
        """Resolve email from config layers, then git config as fallback."""
        # First try config layers (cli > env > local > project)
        if self.config_file_key:
            raw, source = ctx.configs.get(self.config_file_key, self.env_key)
            if raw is not None:
                return (self.normalize(raw), source)

        # Try git config as fallback
        git_value = self._git_source.get()
        if git_value:
            return (git_value, ConfigSource.GIT)

        # Default
        default_value = self.get_default()
        if default_value is not None:
            return (default_value, ConfigSource.DEFAULT)
        return (None, None)

    def validate(self, value: Any) -> None:
        """Validate email format."""
        if not self._require_string(value):
            return
        if not EMAIL_PATTERN.match(value):
            raise ConfigValidationError(f"Invalid email format: {value!r}")
