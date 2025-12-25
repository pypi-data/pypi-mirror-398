"""
Config field definitions - abstract base class and common field types.

This module provides:
- ConfigValidationError: Exception for validation failures
- ConfigFieldABC: Abstract base class for declarative config fields
- StringField: Simple string field
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

import attrs

from djb.core.logging import get_logger
from djb.config.acquisition import AcquisitionContext, AcquisitionResult, ExternalSource
from djb.config.constants import ATTRSLIB_METADATA_KEY
from djb.config.prompting import prompt
from djb.config.resolution import ConfigSource, ResolutionContext, _NOT_LOADED

if TYPE_CHECKING:
    from djb.config.file import ConfigFileType


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


logger = get_logger(__name__)


# =============================================================================
# ConfigFieldABC - Abstract base class for config fields
# =============================================================================


class ConfigFieldABC(ABC):
    """Abstract base for config fields.

    Subclass this to create reusable field types with custom resolution logic.
    The class is callable - when called, it returns an attrs.field().

    Override these methods as needed:
    - resolve(ctx): Custom resolution logic (default: configs > default)
    - configure(ctx): Custom configuration during init (default: sources > prompt)
    - normalize(value): Transform raw values (default: identity)
    - validate(value): Validate resolved values (default: no-op)
    - get_default(): Computed defaults (default: returns self.default)

    Attributes:
        field_name: Set by load() based on the attrs field name. Used for
            auto-deriving env_key and config_file_key.
        config_file: Which config file to save to by default ("local" or "project").
            Provenance takes precedence when saving.
        prompt_text: Prompt message for user input during init.
        validation_hint: Hint shown when validation fails.
        external_sources: List of external sources to try (e.g., git config).
    """

    # Set by load() based on the attrs field name
    field_name: str | None = None

    # Configuration attributes (set by subclasses or __init__)
    prompt_text: str | None = None
    validation_hint: str | None = None
    external_sources: list[ExternalSource]

    def __init__(
        self,
        *,
        env_key: str | None = None,
        config_file_key: str | None = None,
        config_file: ConfigFileType | None = None,
        default: Any = attrs.NOTHING,
        prompt_text: str | None = None,
        validation_hint: str | None = None,
        external_sources: list[ExternalSource] | None = None,
    ):
        """Initialize a config field.

        Args:
            env_key: Full env var name (e.g., "DJB_EMAIL"), or None to derive
                from field name.
            config_file_key: Config file key, or None to derive from field name.
            config_file: Which config file to save to ("local" or "project").
                Provenance takes precedence when saving. Omit for transient fields.
            default: Default value if not found in any source.
            prompt_text: Prompt message for user input during init.
            validation_hint: Hint shown when validation fails.
            external_sources: List of external sources to try (e.g., git config).
        """
        self._env_key = env_key
        self._config_file_key = config_file_key
        self.config_file = config_file
        self.default = default
        self.prompt_text = prompt_text
        self.validation_hint = validation_hint
        self.external_sources = external_sources or []

    @property
    def env_key(self) -> str | None:
        """Get env var name. Derives from field_name if not explicitly set."""
        if self._env_key is not None:
            return self._env_key
        if self.field_name is not None:
            return f"DJB_{self.field_name.upper()}"
        return None

    @property
    def config_file_key(self) -> str | None:
        """Get config file key. Derives from field_name if not explicitly set."""
        if self._config_file_key is not None:
            return self._config_file_key
        return self.field_name

    @staticmethod
    def _attrs_validator(_instance: Any, attrib: attrs.Attribute, value: Any) -> None:
        """attrs validator that delegates to ConfigField.validate().

        This is a static method because it extracts the ConfigField from
        attribute metadata rather than using self.

        Args:
            _instance: The attrs class instance being validated (unused).
            attrib: The attrs attribute being validated.
            value: The value being assigned to the attribute.
        """
        if value is _NOT_LOADED:
            return  # Skip sentinel values during lazy loading
        config_field = attrib.metadata.get(ATTRSLIB_METADATA_KEY)
        if config_field is not None:
            config_field.field_name = attrib.name
            config_field.validate(value)

    def __call__(self) -> Any:
        """Return an attrs.field() with this ConfigField in metadata.

        Uses factory=_unloaded so fields start as sentinel values.
        The actual values are resolved lazily when the config is first accessed.
        Includes a validator that delegates to ConfigField.validate().
        """
        return attrs.field(
            factory=lambda: _NOT_LOADED,
            metadata={ATTRSLIB_METADATA_KEY: self},
            validator=ConfigFieldABC._attrs_validator,
        )

    def resolve(self, ctx: ResolutionContext) -> tuple[Any, ConfigSource | None]:
        """Resolve this field's value from the context.

        Override in subclasses for custom resolution logic.
        Default: configs (cli > env > local > project) > default

        Args:
            ctx: Resolution context with project_root and config layers.

        Returns:
            Tuple of (resolved_value, source). Source is None only when
            no value is set (default is None).
        """
        # Config layers - probes cli > env > local > project
        if self.config_file_key:
            raw, source = ctx.configs.get(self.config_file_key, self.env_key)
            if raw is not None:
                return (self.normalize(raw), source)

        # Default - track as DEFAULT if there's an actual default value
        default_value = self.get_default()
        if default_value is not None:
            return (default_value, ConfigSource.DEFAULT)
        return (None, None)

    def normalize(self, value: Any) -> Any:
        """Normalize a raw value. Override for custom normalization."""
        return value

    def validate(self, value: Any) -> None:
        """Validate resolved value. Override to add validation.

        Raise ConfigValidationError if validation fails.
        """
        pass

    def get_default(self) -> Any:
        """Get the default value. Override for computed defaults."""
        if self.default is attrs.NOTHING:
            return None
        return self.default

    @property
    def display_name(self) -> str:
        """Human-readable name for display."""
        return (self.field_name or "field").replace("_", " ").title()

    def _is_valid(self, value: str) -> bool:
        """Check if a string value is valid. Returns True if valid."""
        try:
            self.validate(value)
            return True
        except (ConfigValidationError, ValueError, TypeError):
            return False

    def _require_string(self, value: Any, *, allow_none: bool = True) -> bool:
        """Validate that value is a string (or None if allowed).

        Args:
            value: The value to validate.
            allow_none: If True, None values skip validation. Default True.

        Returns:
            True if validation should continue (value is a string).
            False if value is None and allow_none is True (skip further validation).

        Raises:
            ConfigValidationError: If value is not a string (or None when allowed).
        """
        if value is None:
            if allow_none:
                return False  # Skip further validation
            raise ConfigValidationError(f"{self.field_name} is required")
        if not isinstance(value, str):
            raise ConfigValidationError(
                f"{self.field_name} must be a string. Got: {type(value).__name__}"
            )
        return True  # Continue with further validation

    def _prompted_result(self, value: Any) -> AcquisitionResult:
        """Create an AcquisitionResult after successful prompting.

        Logs the 'saved' message and creates the result with standard
        prompted-value settings (should_save=True, was_prompted=True).

        Args:
            value: The value from prompting.

        Returns:
            AcquisitionResult ready for return from acquire().
        """
        logger.done(f"{self.display_name} saved: {value}")
        return AcquisitionResult(
            value=value,
            should_save=True,
            source_name=None,
            was_prompted=True,
        )

    def acquire(self, ctx: AcquisitionContext) -> AcquisitionResult | None:
        """Acquire a value for this field interactively.

        Default implementation:
        1. Try external sources in order
        2. Fall back to prompting

        Note: Explicit fields (from config file) are skipped by the orchestrator
        before acquire() is called.

        Override in subclasses for custom behavior (e.g., confirmation flow).

        Args:
            ctx: Acquisition context with project_root, current value, etc.

        Returns:
            AcquisitionResult with value and metadata, or None to skip this field.
        """
        # 1. Try external sources
        for source in self.external_sources:
            value = source.get()
            if value and self._is_valid(value):
                return AcquisitionResult(
                    value=value,
                    should_save=True,
                    source_name=source.name,
                    was_prompted=False,
                )

        # 2. Prompt user (if prompt_text is set)
        if not self.prompt_text:
            # No prompting configured - return current value if any
            if ctx.current_value is not None:
                return AcquisitionResult(
                    value=ctx.current_value,
                    should_save=False,
                    source_name=None,
                    was_prompted=False,
                )
            return None

        result = prompt(
            self.prompt_text,
            default=str(ctx.current_value) if ctx.current_value else None,
            validator=self._is_valid,
            validation_hint=self.validation_hint,
        )

        if result.source == "cancelled":
            return None

        value = self.normalize(result.value) if result.value else result.value
        return self._prompted_result(value)


# =============================================================================
# Common field types
# =============================================================================


class StringField(ConfigFieldABC):
    """Simple string field with no special behavior.

    This is just ConfigFieldABC with no overrides - an alias for clarity.
    """

    pass
