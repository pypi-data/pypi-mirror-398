"""
Config resolution machinery - layered config lookup with provenance tracking.

This module provides:
- ConfigSource: Enum tracking where a config value came from
- _NOT_LOADED: Sentinel for unloaded fields (lazy config support)
- ProvenanceChainMap: A ChainMap-like object that probes config layers with provenance tracking
- ResolutionContext: Context passed to field resolution
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from djb.config.file import ConfigFileType


class ConfigSource(Enum):
    """Where a config value came from.

    Used for provenance tracking to distinguish explicitly configured values
    from derived/fallback values. This helps init decide what to prompt for.

    Sources are ordered from most explicit to most derived:
    - CLI, ENV, LOCAL_CONFIG, PROJECT_CONFIG: Explicit user configuration
    - PYPROJECT, GIT, CWD_PATH, CWD_NAME, DEFAULT, DERIVED: Derived from other sources
    - PROMPTED: User entered during init (before saving to config)
    """

    # Explicit sources (user configured)
    CLI = "cli"  # --project-name flag
    ENV = "environment"  # DJB_PROJECT_NAME
    LOCAL_CONFIG = "local_config"  # .djb/local.yaml
    PROJECT_CONFIG = "project_config"  # .djb/project.yaml

    # Derived sources (computed/fallback)
    PYPROJECT = "pyproject"  # pyproject.toml (project name or project dir detection)
    GIT = "git"  # git config user.name/email
    CWD_PATH = "cwd_path"  # project_dir from current working directory fallback
    CWD_NAME = "cwd_name"  # project_name from directory name
    DEFAULT = "default"  # field using its default value
    DERIVED = "derived"  # Generic fallback/computed value

    # Special case for init workflow
    PROMPTED = "prompted"  # User entered during init

    def is_explicit(self) -> bool:
        """True if this source represents explicit user configuration."""
        return self in {
            ConfigSource.CLI,
            ConfigSource.ENV,
            ConfigSource.LOCAL_CONFIG,
            ConfigSource.PROJECT_CONFIG,
        }

    def is_derived(self) -> bool:
        """True if this source represents a derived/fallback value."""
        return self in {
            ConfigSource.PYPROJECT,
            ConfigSource.GIT,
            ConfigSource.CWD_PATH,
            ConfigSource.CWD_NAME,
            ConfigSource.DEFAULT,
            ConfigSource.DERIVED,
        }

    @property
    def config_file_type(self) -> ConfigFileType | None:
        """Return the ConfigFileType for config file sources, None otherwise."""
        if self == ConfigSource.LOCAL_CONFIG:
            return "local"
        elif self == ConfigSource.PROJECT_CONFIG:
            return "project"
        return None


_NOT_LOADED = object()
"""Sentinel value indicating a field hasn't been loaded yet.

Used by @attrs.frozen DjbConfig to implement lazy loading:
- Fields start with this sentinel as their default value
- On first access, __getattribute__ detects the sentinel and triggers load()
- After loading, fields contain their resolved values

This avoids eager config file/env var access at import time.
"""


class ProvenanceChainMap:
    """A ChainMap-like object that tracks which layer a value came from.

    Probes layers in order (cli > env > local > project) and remembers
    which layer provided each value.

    Each layer can have its own key scheme:
    - cli, local, project: use config_file_key (e.g., "email")
    - env: uses env_key (e.g., "DJB_EMAIL")

    Args:
        cli: CLI overrides dict
        env: Environment variables mapping (defaults to os.environ)
        local: Local config dict (.djb/local.yaml)
        project: Project config dict (.djb/project.yaml)
    """

    def __init__(
        self,
        *,
        cli: dict[str, Any] | None = None,
        env: Mapping[str, str] | None = None,
        local: dict[str, Any] | None = None,
        project: dict[str, Any] | None = None,
    ):
        self._layers: dict[str, Mapping[str, Any]] = {
            "cli": cli or {},
            "env": env if env is not None else os.environ,
            "local": local or {},
            "project": project or {},
        }
        self._resolution_order = ["cli", "env", "local", "project"]
        self._layer_to_source: dict[str, ConfigSource] = {
            "cli": ConfigSource.CLI,
            "env": ConfigSource.ENV,
            "local": ConfigSource.LOCAL_CONFIG,
            "project": ConfigSource.PROJECT_CONFIG,
        }

    def get(
        self, config_file_key: str, env_key: str | None = None
    ) -> tuple[Any, ConfigSource | None]:
        """Get a value, using the appropriate key for each layer.

        Args:
            config_file_key: Key to use for cli/local/project layers
            env_key: Key to use for env layer (if None, env layer is skipped)

        Returns:
            Tuple of (value, ConfigSource). If not found, returns (None, None).
        """
        for layer_name in self._resolution_order:
            layer = self._layers[layer_name]
            # Use env_key for env layer, config_file_key for others
            key = env_key if layer_name == "env" else config_file_key
            if key and key in layer:
                value = layer[key]
                # Treat empty strings as "not set" (especially for env vars)
                if value == "":
                    continue
                return (value, self._layer_to_source[layer_name])
        return (None, None)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in any layer (uses config_file_key only)."""
        return any(key in layer for layer in self._layers.values())


@dataclass(frozen=True)
class ResolutionContext:
    """Context passed to field resolution.

    Attributes:
        project_root: The resolved project root directory
        project_root_source: How project_root was determined (PYPROJECT, CWD, etc.)
        configs: All config layers (cli > env > local > project)
    """

    project_root: Path
    project_root_source: ConfigSource
    configs: ProvenanceChainMap = field(default_factory=lambda: ProvenanceChainMap())
