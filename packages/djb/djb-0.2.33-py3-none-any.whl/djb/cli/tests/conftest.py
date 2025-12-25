"""
Shared test fixtures for djb CLI tests.

See __init__.py for the full list of available fixtures and utilities.

Fixtures:
    pty_stdin - Creates a PTY and replaces stdin for interactive input testing (from djb.testing)
    runner - Click CliRunner for invoking CLI commands
    secrets_dir - Creates a secrets/ directory in tmp_path
    make_age_key - Factory for creating age key pairs (from djb.testing)
    alice_key - Pre-made age key pair for Alice (from djb.testing)
    bob_key - Pre-made age key pair for Bob (from djb.testing)
    djb_project - Creates a minimal djb project directory
    host_with_editable_djb - Creates a host project with djb in editable mode
    setup_sops_config - Factory for creating .sops.yaml configuration

Auto-enabled fixtures (applied to all tests automatically):
    configure_logging - Initializes djb CLI logging system
    test_config_env - Sets DJB_* environment variables for CLI tests
    disable_gpg_protection - Disables GPG protection to avoid pinentry prompts
"""

from __future__ import annotations

import os
from collections.abc import Callable, Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from djb import reset_config, setup_logging
from djb.secrets import create_sops_config
from djb.testing.fixtures import alice_key, bob_key, make_age_key, pty_stdin

# Re-export shared fixtures so they're available to tests in this package
__all__ = ["pty_stdin", "make_age_key", "alice_key", "bob_key"]


@pytest.fixture(autouse=True)
def configure_logging():
    """Configure logging for all CLI tests.

    This fixture runs automatically before each test to ensure
    the djb CLI logging system is initialized. Without this,
    tests using CliRunner won't capture logger output.
    """
    setup_logging()


@pytest.fixture(autouse=True)
def test_config_env(tmp_path: Path) -> Generator[None, None, None]:
    """Provide default config values via environment variables for CLI tests.

    This fixture sets DJB_* environment variables to ensure the CLI's
    required config validation passes. Tests can override these by setting
    their own environment variables before invoking commands.

    Also resets the lazy config cache to ensure tests get fresh config
    based on the test environment variables.
    """
    # Reset lazy config to clear any cached config from previous tests
    reset_config()

    env_vars = {
        "DJB_PROJECT_DIR": str(tmp_path),
        "DJB_PROJECT_NAME": "test-project",
        "DJB_NAME": "Test User",
        "DJB_EMAIL": "test@example.com",
    }
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-project"\n')
    old_env = {k: os.environ.get(k) for k in env_vars}
    os.environ.update(env_vars)
    try:
        yield
    finally:
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        # Reset config after test to avoid polluting other tests
        reset_config()


@pytest.fixture(autouse=True)
def disable_gpg_protection():
    """Disable GPG protection to avoid pinentry prompts in tests.

    GPG requires an interactive pinentry for decryption, which fails in
    automated test environments. By marking GPG as unavailable, we skip
    the GPG-protection code path entirely.
    """
    with (
        patch("djb.secrets.init.check_gpg_installed", return_value=False),
        patch("djb.secrets.protected.check_gpg_installed", return_value=False),
    ):
        yield


@pytest.fixture
def runner():
    """Click CLI test runner.

    Returns a CliRunner instance for invoking Click commands
    in tests. The CliRunner captures stdout/stderr and provides
    access to exit codes and output.

    Example:
        def test_my_command(runner):
            result = runner.invoke(djb_cli, ["my-command"])
            assert result.exit_code == 0
            assert "expected output" in result.output
    """
    return CliRunner()


# =============================================================================
# Secrets Test Fixtures
# =============================================================================


@pytest.fixture
def secrets_dir(tmp_path: Path) -> Path:
    """Create a secrets directory for testing.

    Returns the path to a freshly created secrets/ directory inside tmp_path.
    """
    dir_path = tmp_path / "secrets"
    dir_path.mkdir()
    return dir_path


# =============================================================================
# Project Structure Fixtures
# =============================================================================

# Common pyproject.toml content for testing
DJB_PYPROJECT_CONTENT = '[project]\nname = "djb"\nversion = "0.1.0"\n'

EDITABLE_PYPROJECT_TEMPLATE = """\
[project]
name = "myproject"

[tool.uv.workspace]
members = ["{path}"]

[tool.uv.sources]
djb = {{ workspace = true, editable = true }}
"""


def make_editable_pyproject(djb_path: str = "djb") -> str:
    """Generate editable pyproject.toml content with given djb path."""
    return EDITABLE_PYPROJECT_TEMPLATE.format(path=djb_path)


@pytest.fixture
def djb_project(tmp_path: Path) -> Path:
    """Create a minimal djb project directory.

    Creates tmp_path/djb/ with a valid pyproject.toml.
    Returns the djb directory path.
    """
    djb_dir = tmp_path / "djb"
    djb_dir.mkdir()
    (djb_dir / "pyproject.toml").write_text(DJB_PYPROJECT_CONTENT)
    return djb_dir


@pytest.fixture
def host_with_editable_djb(tmp_path: Path, djb_project: Path) -> Path:
    """Create a host project with djb in editable mode.

    Creates:
    - tmp_path/djb/ (via djb_project fixture)
    - tmp_path/pyproject.toml with [tool.uv.sources] pointing to djb

    Returns the host project path (tmp_path).
    """
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(make_editable_pyproject("djb"))
    return tmp_path


@pytest.fixture
def setup_sops_config(secrets_dir: Path) -> Callable[[dict[str, str]], Path]:
    """Factory fixture to create .sops.yaml configuration.

    Returns a factory function that creates a .sops.yaml file with the given
    recipients (mapping public_key -> email).

    Example:
        def test_sops(setup_sops_config, alice_key):
            _, alice_public = alice_key
            setup_sops_config({alice_public: "alice@example.com"})
    """

    def _setup(recipients: dict[str, str]) -> Path:
        return create_sops_config(secrets_dir, recipients)

    return _setup
