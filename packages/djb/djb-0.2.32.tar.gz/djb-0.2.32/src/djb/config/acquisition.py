"""
Value acquisition for interactive field configuration.

Fields acquire values in two ways:
- Resolution (resolve()): Automatic - from config files, env vars, defaults
- Acquisition (acquire()): Interactive - from external sources, user prompts

This module provides:
- ExternalSource: Protocol for external value sources
- AcquisitionContext: Context passed to field.acquire()
- AcquisitionResult: Return value from field.acquire()
- GitConfigSource: Git config as an external source
- acquire_all_fields(): Generator that acquires values for all interactive fields
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import attrs

from djb.config.constants import ATTRSLIB_METADATA_KEY
from djb.config.file import LOCAL, PROJECT, load_config, save_config
from djb.config.resolution import ConfigSource

if TYPE_CHECKING:
    from djb.config.config import DjbConfigBase
    from djb.config.field import ConfigFieldABC


# =============================================================================
# Acquisition types and protocols
# =============================================================================


@runtime_checkable
class ExternalSource(Protocol):
    """Protocol for external value sources (e.g., git config)."""

    @property
    def name(self) -> str:
        """Display name for this source (e.g., "git config")."""
        ...

    def get(self) -> str | None:
        """Get value from this source, or None if not available."""
        ...


@dataclass
class AcquisitionContext:
    """Context passed to field.acquire() during init.

    Provides access to:
    - project_root: Where config files should be saved
    - current_value: The currently resolved value (may be None)
    - source: Where the current value came from (provenance)
    - other_values: Dict of already-configured field values (for dependencies)
    """

    project_root: Path
    current_value: Any
    source: ConfigSource | None
    other_values: dict[str, Any]

    def is_explicit(self) -> bool:
        """Check if current value was explicitly configured (config file, env var)."""
        return self.source is not None and self.source.is_explicit()

    def is_derived(self) -> bool:
        """Check if current value was derived (pyproject.toml, directory name, etc.)."""
        return self.source is not None and self.source.is_derived()


@dataclass
class AcquisitionResult:
    """Result of field configuration.

    Attributes:
        value: The configured value.
        should_save: Whether to persist the value to config file.
        source_name: Name of external source used (e.g., "git config"), or None.
        was_prompted: Whether user was prompted for this value.
    """

    value: Any
    should_save: bool = True
    source_name: str | None = None
    was_prompted: bool = False


@dataclass
class GitConfigSource:
    """Git config as an external source.

    Reads values from git config. Writing back to git config
    is handled by init.py, not this source.
    """

    key: str  # e.g., "user.email"

    @property
    def name(self) -> str:
        """Display name for this source."""
        return "git config"

    def get(self) -> str | None:
        """Get value from git config."""
        try:
            result = subprocess.run(
                ["git", "config", "--get", self.key],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip() or None
        except (FileNotFoundError, OSError):
            pass
        return None


# =============================================================================
# Field acquisition orchestrator
# =============================================================================


def _is_acquirable(config_field: ConfigFieldABC) -> bool:
    """Check if a field participates in interactive acquisition.

    A field is acquirable if it has an acquire() method and prompt_text.
    """
    return hasattr(config_field, "acquire") and config_field.prompt_text is not None


def _save_field_value(
    config_field: ConfigFieldABC,
    value: Any,
    project_root: Path,
) -> None:
    """Save a field value to the appropriate config file.

    Uses config_field.config_file metadata to determine storage location:
    - "local": Goes to local.yaml (gitignored, user-specific)
    - "project": Goes to project.yaml (committed, shared)
    """
    config_type = LOCAL if config_field.config_file == "local" else PROJECT
    file_key = config_field.config_file_key or config_field.field_name
    assert file_key is not None, "field_name must be set before saving"
    existing = load_config(config_type, project_root)
    existing[file_key] = value
    save_config(config_type, existing, project_root)


def acquire_all_fields(
    project_root: Path,
    config_instance: "DjbConfigBase",
) -> Iterator[tuple[str, AcquisitionResult]]:
    """Acquire values for all interactive fields.

    Iterates through fields in declaration order, acquiring values for each
    field that is acquirable (has acquire() method and prompt_text).

    Explicit fields (already configured via config file/env) are skipped.
    Saving is handled internally after each successful acquisition.

    Args:
        project_root: Project root directory for saving.
        config_instance: Config instance (DjbConfigBase or subclass).

    Yields:
        (field_name, AcquisitionResult) for each acquired field.
    """
    configured: dict[str, Any] = {}

    # Iterate fields in declaration order (works with LazyConfig via __attrs_attrs__ descriptor)
    for field in attrs.fields(type(config_instance)):
        field_name = field.name
        config_field = field.metadata.get(ATTRSLIB_METADATA_KEY)

        if config_field is None:
            continue

        # Set field_name for env_key/config_file_key derivation
        config_field.field_name = field_name

        # Skip non-acquirable fields
        if not _is_acquirable(config_field):
            continue

        # Get current value and source
        current_value = getattr(config_instance, field_name, None)
        source = config_instance.get_source(field_name)

        # Skip explicit fields - they don't need acquisition
        if source is not None and source.is_explicit():
            configured[field_name] = current_value
            continue

        # Build context for this field
        ctx = AcquisitionContext(
            project_root=project_root,
            current_value=current_value,
            source=source,
            other_values=configured.copy(),
        )

        # Call field's acquire method
        result = config_field.acquire(ctx)

        if result is None:
            # Acquisition was cancelled
            continue

        configured[field_name] = result.value

        # Save to config file if needed
        if result.should_save and result.value is not None:
            _save_field_value(config_field, result.value, project_root)

        yield field_name, result
