"""
Config file operations - Loading and saving YAML config files.

This module provides utilities for reading and writing the .djb/ config files:
- .djb/local.yaml: User-specific settings (gitignored)
- .djb/project.yaml: Project settings (committed)
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Literal

import yaml

# Type alias for config file types - easily extensible (e.g., add "core" later)
ConfigFileType = Literal["local", "project"]

# Config type constants
LOCAL: ConfigFileType = "local"
PROJECT: ConfigFileType = "project"

# Config file names (internal)
_CONFIG_FILES = {
    LOCAL: "local.yaml",
    PROJECT: "project.yaml",
}


def get_config_dir(project_root: Path) -> Path:
    """Get the djb configuration directory (.djb/ in project root).

    Args:
        project_root: Project root path.

    Returns:
        Path to .djb/ directory in the project.
    """
    return project_root / ".djb"


def get_config_path(config_type: ConfigFileType, project_root: Path) -> Path:
    """Get path to a config file by type.

    Args:
        config_type: Config type (LOCAL or PROJECT).
        project_root: Project root path.

    Returns:
        Path to the config file.
    """
    if config_type not in _CONFIG_FILES:
        raise ValueError(f"Unknown config type: {config_type}")
    return get_config_dir(project_root) / _CONFIG_FILES[config_type]


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    """Load a YAML file and ensure it contains a mapping."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid config format in {path}: expected a mapping at top level")
    return data


def load_config(
    config_type: ConfigFileType,
    project_root: Path,
    *,
    known_keys: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Load a configuration file by type.

    Args:
        config_type: Config type (LOCAL or PROJECT).
        project_root: Project root path.
        known_keys: If provided, warn about unrecognized config keys (helps catch typos).

    Returns:
        Configuration dict, or empty dict if the file doesn't exist.
    """
    path = get_config_path(config_type, project_root)
    if not path.exists():
        return {}

    data = _load_yaml_mapping(path)

    # Warn about unknown keys to help catch typos
    if known_keys is not None and data:
        unknown_keys = set(data.keys()) - known_keys
        if unknown_keys:
            file_name = _CONFIG_FILES[config_type]
            warnings.warn(
                f"Unknown config keys in .djb/{file_name}: {sorted(unknown_keys)}. "
                f"Known keys: {sorted(known_keys)}",
                stacklevel=2,
            )

    return data


def save_config(config_type: ConfigFileType, data: dict[str, Any], project_root: Path) -> None:
    """Save a configuration file by type.

    Args:
        config_type: Config type (LOCAL or PROJECT).
        data: Configuration dict to save.
        project_root: Project root path.
    """
    path = get_config_path(config_type, project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
