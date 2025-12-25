"""
Shared test fixtures for djb core tests.

See __init__.py for the full list of available fixtures and utilities.

Auto-enabled fixtures (applied to all tests automatically):
    clean_djb_env - Ensures a clean environment by removing DJB_* env vars

Factory fixtures:
    make_config_file - Factory for creating config files in .djb directory
"""

from __future__ import annotations

import os
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Literal

import pytest
import yaml

from djb import reset_config

# Environment variables that may be set by CLI test fixtures
_DJB_ENV_VARS = [
    "DJB_PROJECT_DIR",
    "DJB_PROJECT_NAME",
    "DJB_NAME",
    "DJB_EMAIL",
    "DJB_MODE",
    "DJB_TARGET",
    "DJB_HOSTNAME",
]


@pytest.fixture(autouse=True)
def clean_djb_env() -> Generator[None, None, None]:
    """Ensure a clean environment for config tests.

    This fixture removes all DJB_* environment variables before each test
    and restores the original state afterward. This prevents autouse fixtures
    from other test directories (like cli/tests) from affecting these tests.

    Also resets the lazy config singleton to ensure tests get fresh config.
    """
    reset_config()
    old_env = {k: os.environ.get(k) for k in _DJB_ENV_VARS}
    for k in _DJB_ENV_VARS:
        os.environ.pop(k, None)
    try:
        yield
    finally:
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        reset_config()


@pytest.fixture
def make_config_file(tmp_path: Path) -> Callable[..., Path]:
    """Factory for creating config files in .djb directory.

    Returns a factory function that creates config files with the given content.

    Args:
        content: YAML content to write to the config file
        config_type: Either "local" or "project" (default: "local")

    Returns:
        Path to the created config file

    Usage:
        def test_something(make_config_file):
            config_path = make_config_file("name: John\\nemail: john@example.com")
            # Creates .djb/local.yaml with the given content

            # For project config:
            config_path = make_config_file("hostname: example.com", config_type="project")
            # Creates .djb/project.yaml

            # You can also pass a dict-like structure:
            config_path = make_config_file({"name": "John", "email": "john@example.com"})
    """
    config_dir = tmp_path / ".djb"

    def _create(
        content: str | dict,
        config_type: Literal["local", "project"] = "local",
    ) -> Path:
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / f"{config_type}.yaml"

        if isinstance(content, dict):
            # Convert dict to YAML-like format
            content = yaml.safe_dump(content, default_flow_style=False)

        config_file.write_text(content)
        return config_file

    return _create
