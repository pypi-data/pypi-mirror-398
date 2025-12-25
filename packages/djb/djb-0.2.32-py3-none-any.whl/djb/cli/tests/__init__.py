"""
djb.cli.tests - Test utilities for djb CLI unit tests.

Fixtures (auto-discovered by pytest from conftest.py):
    pty_stdin - Creates a PTY and replaces stdin for interactive input testing
    runner - Click CliRunner for invoking CLI commands
    secrets_dir - Creates a secrets/ directory in tmp_path
    make_age_key - Factory for creating age key pairs
    alice_key - Pre-made age key pair for Alice
    bob_key - Pre-made age key pair for Bob
    djb_project - Creates a minimal djb project directory
    host_with_editable_djb - Creates a host project with djb in editable mode
    setup_sops_config - Factory for creating .sops.yaml configuration

Auto-enabled fixtures (applied to all tests automatically):
    configure_logging - Initializes djb CLI logging system
    test_config_env - Sets DJB_* environment variables for CLI tests
    disable_gpg_protection - Disables GPG protection to avoid pinentry prompts

Helper functions:
    make_editable_pyproject - Generate editable pyproject.toml content

Constants:
    DJB_PYPROJECT_CONTENT - Common pyproject.toml content for testing
    EDITABLE_PYPROJECT_TEMPLATE - Template for editable pyproject.toml
"""

from __future__ import annotations

from .conftest import (
    DJB_PYPROJECT_CONTENT,
    EDITABLE_PYPROJECT_TEMPLATE,
    make_editable_pyproject,
    pty_stdin,
)

__all__ = [
    "DJB_PYPROJECT_CONTENT",
    "EDITABLE_PYPROJECT_TEMPLATE",
    "make_editable_pyproject",
    "pty_stdin",
]
