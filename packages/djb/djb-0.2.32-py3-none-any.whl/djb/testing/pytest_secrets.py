"""
Pytest plugin for early test secrets setup.

This plugin uses pytest_load_initial_conftests with tryfirst=True to run
BEFORE conftest.py files are imported. This ensures Django is configured
before any conftest files import Django models.

Usage:
    Register via pytest.ini or pyproject.toml:

        [pytest]
        addopts = -p djb.testing.pytest_secrets
        DJANGO_SETTINGS_MODULE = myproject.settings

    Or set DJANGO_SETTINGS_MODULE via environment variable.

The plugin creates isolated test secrets in a temporary directory with:
- An unprotected age key (no GPG needed for tests)
- SOPS configuration
- Encrypted test secrets

Environment variables set for Django settings:
- TEST_SECRETS_DIR: Path to the secrets directory
- TEST_AGE_KEY_PATH: Path to the age key file

"""

from __future__ import annotations

import getpass
import os
import shutil
import tempfile
from pathlib import Path
from typing import NamedTuple

import pytest

from djb.secrets import create_sops_config, encrypt_file, generate_age_key

_test_secrets_root: Path | None = None


class TestSecretsPaths(NamedTuple):
    """Paths created by setup_test_secrets."""

    root: Path
    secrets_dir: Path
    age_key_path: Path


def setup_test_secrets() -> TestSecretsPaths:
    """Create isolated test secrets infrastructure in a temp directory.

    Creates a temporary directory with:
    - An unprotected age key (no GPG needed)
    - SOPS configuration
    - Encrypted test secrets with stub database credentials

    The database name in the stub secrets doesn't matter because
    pytest-django creates a test database with a `test_` prefix anyway.

    Returns:
        TestSecretsPaths with root, secrets_dir, and age_key_path.

    Side effects:
        Sets environment variables:
        - TEST_SECRETS_DIR: Path to the secrets directory
        - TEST_AGE_KEY_PATH: Path to the age key file
    """
    # Create temp directory that persists for the test session
    test_secrets_root = Path(tempfile.mkdtemp(prefix="djb_test_secrets_"))

    # Create directories
    age_dir = test_secrets_root / ".age"
    secrets_dir = test_secrets_root / "secrets"
    age_dir.mkdir()
    secrets_dir.mkdir()

    # Generate unprotected age key (no GPG needed for tests)
    key_path = age_dir / "keys.txt"
    public_key, _private_key = generate_age_key(key_path)

    # Create SOPS config
    create_sops_config(secrets_dir, recipients=[public_key])

    # Create test secrets and encrypt in-place
    # Use system user for database access (peer authentication).
    # pytest-django will create a test database automatically.
    current_user = getpass.getuser()
    test_secrets_content = f"""\
# Test secrets - auto-generated for pytest by djb.testing.pytest_secrets
django_secret_key: test-secret-key-for-pytest-only
db_credentials:
  database: djb_test
  username: {current_user}
  password: ""
  host: localhost
  port: 5432
"""
    secrets_file = secrets_dir / "dev.yaml"
    secrets_file.write_text(test_secrets_content)

    # Encrypt in-place with SOPS
    sops_config = secrets_dir / ".sops.yaml"
    encrypt_file(secrets_file, sops_config=sops_config)

    # Set environment variables for Django settings
    os.environ["TEST_SECRETS_DIR"] = str(secrets_dir)
    os.environ["TEST_AGE_KEY_PATH"] = str(key_path)

    return TestSecretsPaths(
        root=test_secrets_root,
        secrets_dir=secrets_dir,
        age_key_path=key_path,
    )


def cleanup_test_secrets(root: Path) -> None:
    """Clean up test secrets directory.

    Args:
        root: The root path returned by setup_test_secrets().
    """
    if root and root.exists():
        shutil.rmtree(root, ignore_errors=True)


# =============================================================================
# Pytest Plugin Hooks
# =============================================================================


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(early_config, parser, args):  # noqa: ARG001
    """Set up test secrets before Django configuration.

    This hook runs before conftest.py files are imported, ensuring:
    1. Test secrets are created and encrypted
    2. Environment variables are set for Django settings
    3. DJANGO_SETTINGS_MODULE is available before pytest-django's hook runs

    pytest-django's hook (without tryfirst) will then call django.setup().
    """
    global _test_secrets_root  # noqa: PLW0603

    paths = setup_test_secrets()
    _test_secrets_root = paths.root

    # Read DJANGO_SETTINGS_MODULE from pytest.ini if not already set
    # This allows projects to configure it in pytest.ini alongside this plugin
    ini_settings_module = early_config.getini("DJANGO_SETTINGS_MODULE")
    if ini_settings_module and "DJANGO_SETTINGS_MODULE" not in os.environ:
        os.environ["DJANGO_SETTINGS_MODULE"] = ini_settings_module


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    """Clean up test secrets after all tests complete."""
    if _test_secrets_root:
        cleanup_test_secrets(_test_secrets_root)
