"""Shared fixtures for djb CLI E2E tests.

See __init__.py for the full list of available fixtures and utilities.

These fixtures provide isolated test environments for end-to-end testing
of djb CLI commands against real external tools (PostgreSQL, age, SOPS, GPG)
while mocking cloud services (Heroku, PyPI).

Environment Isolation:
- GPG: Uses --homedir or GNUPGHOME to avoid touching ~/.gnupg
- Age: Keys generated in tmp_path, never ~/.age
- SOPS: Uses --config flag and SOPS_AGE_KEY_FILE env var
- PostgreSQL: Creates unique test databases, cleaned up after tests
- Git: Initializes repos in tmp_path with test-specific identity

Requirements:
- GPG must be installed (brew install gnupg)
- age must be installed (brew install age)
- SOPS must be installed (brew install sops)
- PostgreSQL must be running locally

Run with: pytest --run-e2e
"""

from __future__ import annotations

import os
import subprocess
import uuid
from collections.abc import Callable, Generator
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from djb import setup_logging
from djb.config import reset_config
from djb.secrets import (
    SecretsManager,
    check_gpg_installed,
    create_sops_config,
    generate_age_key,
)
from djb.testing.fixtures import alice_key, bob_key, make_age_key

# Re-export shared fixtures so they're available to tests in this package
__all__ = ["make_age_key", "alice_key", "bob_key"]


# =============================================================================
# Prerequisite Checking Fixtures
# =============================================================================


def check_age_installed() -> bool:
    """Check if age is installed."""
    try:
        result = subprocess.run(["age", "--version"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_sops_installed() -> bool:
    """Check if SOPS is installed."""
    try:
        result = subprocess.run(["sops", "--version"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_postgres_available() -> bool:
    """Check if PostgreSQL is available locally."""
    try:
        result = subprocess.run(["psql", "--version"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.fixture
def require_gpg():
    """Skip test if GPG is not installed."""
    if not check_gpg_installed():
        pytest.skip("GPG not installed (brew install gnupg)")


@pytest.fixture
def require_age():
    """Skip test if age is not installed."""
    if not check_age_installed():
        pytest.skip("age not installed (brew install age)")


@pytest.fixture
def require_sops():
    """Skip test if SOPS is not installed."""
    if not check_sops_installed():
        pytest.skip("SOPS not installed (brew install sops)")


@pytest.fixture
def require_postgres():
    """Skip test if PostgreSQL is not available."""
    if not check_postgres_available():
        pytest.skip("PostgreSQL not available")


# =============================================================================
# CLI Runner Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def configure_logging():
    """Configure logging for all CLI tests.

    This fixture runs automatically before each test to ensure
    the djb CLI logging system is initialized.
    """
    setup_logging()


@pytest.fixture(autouse=True)
def clean_config_state():
    """Reset config state before and after each test.

    This ensures tests have a clean config state and don't leak
    state to other tests. The config will be reloaded fresh when
    accessed within each test.
    """
    reset_config()
    yield
    reset_config()


@pytest.fixture
def runner() -> CliRunner:
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def e2e_runner() -> CliRunner:
    """CLI runner configured for E2E tests with isolated filesystem."""
    return CliRunner()


# =============================================================================
# Environment Isolation Fixtures
# =============================================================================


@pytest.fixture
def isolated_env(tmp_path: Path) -> dict[str, str]:
    """Provide environment dict that isolates all tools from user's real config.

    This environment can be passed to subprocess.run() to ensure tools
    don't pollute the user's actual configuration.
    """
    gnupg_home = tmp_path / ".gnupg"
    gnupg_home.mkdir(mode=0o700)

    age_dir = tmp_path / ".age"
    age_dir.mkdir(mode=0o700)

    env = os.environ.copy()
    env["GNUPGHOME"] = str(gnupg_home)
    env["SOPS_AGE_KEY_FILE"] = str(age_dir / "keys.txt")
    # Don't override HOME unless absolutely necessary - it can break many tools
    return env


@pytest.fixture
def gpg_home(tmp_path: Path) -> Path:
    """Create an isolated GPG home directory."""
    gpg_dir = tmp_path / ".gnupg"
    gpg_dir.mkdir(mode=0o700)
    return gpg_dir


@pytest.fixture
def age_key_dir(tmp_path: Path) -> Path:
    """Create an isolated .age directory for keys."""
    age_dir = tmp_path / ".age"
    age_dir.mkdir(mode=0o700)
    return age_dir


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def test_passphrase() -> str:
    """Passphrase for test GPG encryption."""
    return "test-passphrase-12345"


@pytest.fixture
def test_secret_value() -> str:
    """A test secret value for encryption tests."""
    return "super-secret-test-value-abc123"


# =============================================================================
# Project Structure Fixtures
# =============================================================================


@pytest.fixture
def isolated_project(tmp_path: Path) -> Path:
    """Create an isolated project directory with basic structure.

    Creates:
    - pyproject.toml with minimal config
    - Initialized git repo with test identity
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create minimal pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test-project"\nversion = "0.1.0"\n'
        '\n[tool.djb]\nproject_name = "test-project"\n'
    )

    # Initialize git with test identity
    subprocess.run(
        ["git", "init", str(project_dir)],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(project_dir), "config", "user.email", "e2e-test@example.com"],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(project_dir), "config", "user.name", "E2E Test"],
        capture_output=True,
        check=True,
    )

    return project_dir


@pytest.fixture
def isolated_project_with_secrets(isolated_project: Path, age_key_dir: Path) -> tuple[Path, Path]:
    """Create an isolated project with secrets directory, age key, and encrypted secrets files.

    Creates:
    - secrets/ directory with .sops.yaml config
    - Encrypted dev.yaml, staging.yaml, production.yaml files
    - Age key at age_key_dir/keys.txt

    Returns (project_dir, key_path) tuple.
    """
    # Create secrets directory
    secrets_dir = isolated_project / "secrets"
    secrets_dir.mkdir()

    # Generate age key
    key_path = age_key_dir / "keys.txt"
    public_key, _ = generate_age_key(key_path)

    # Create .sops.yaml
    create_sops_config(secrets_dir, {public_key: "test@example.com"})

    # Create encrypted secrets files for each environment
    manager = SecretsManager(secrets_dir=secrets_dir, key_path=key_path)
    all_public_keys = [public_key]

    for env in ["dev", "staging", "production"]:
        # Create a simple secrets template
        template = {
            "django_secret_key": f"test-secret-key-for-{env}",
            "database_url": f"postgres://localhost/{env}_db",
        }
        manager.save_secrets(env, template, all_public_keys)

    return isolated_project, key_path


@pytest.fixture
def secrets_dir(tmp_path: Path) -> Path:
    """Create a secrets directory for testing."""
    dir_path = tmp_path / "secrets"
    dir_path.mkdir()
    return dir_path


# =============================================================================
# SOPS Configuration Fixtures
# =============================================================================


@pytest.fixture
def setup_sops_config(secrets_dir: Path) -> Callable[[dict[str, str]], Path]:
    """Factory fixture to create .sops.yaml configuration.

    Example:
        def test_sops(setup_sops_config, alice_key):
            _, alice_public = alice_key
            setup_sops_config({alice_public: "alice@example.com"})
    """

    def _setup(recipients: dict[str, str]) -> Path:
        return create_sops_config(secrets_dir, recipients)

    return _setup


# =============================================================================
# PostgreSQL Fixtures
# =============================================================================


@pytest.fixture
def pg_test_database(require_postgres) -> Generator[str, None, None]:
    """Create an isolated PostgreSQL database for testing.

    Creates a uniquely named database, yields the name, then drops it.
    """
    db_name = f"djb_e2e_test_{uuid.uuid4().hex[:8]}"

    # Create the database
    result = subprocess.run(
        ["createdb", db_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"Could not create test database: {result.stderr}")

    try:
        yield db_name
    finally:
        # Drop the database
        subprocess.run(
            ["dropdb", "--if-exists", db_name],
            capture_output=True,
            text=True,
        )


# =============================================================================
# DJB Config Environment Fixtures
# =============================================================================


@pytest.fixture
def djb_config_env(tmp_path: Path) -> Generator[dict[str, str], None, None]:
    """Set up DJB environment variables for testing.

    This fixture sets DJB_* environment variables to ensure the CLI's
    required config validation passes. Restores original values after test.
    """
    env_vars = {
        "DJB_PROJECT_DIR": str(tmp_path),
        "DJB_PROJECT_NAME": "e2e-test-project",
        "DJB_NAME": "E2E Test User",
        "DJB_EMAIL": "e2e-test@example.com",
    }
    old_env = {k: os.environ.get(k) for k in env_vars}
    os.environ.update(env_vars)
    try:
        yield env_vars
    finally:
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# =============================================================================
# Heroku Mocking Fixtures
# =============================================================================


@pytest.fixture
def mock_heroku_cli():
    """Mock Heroku CLI commands.

    Mocks subprocess.run to intercept heroku commands and return
    appropriate mock responses. Unknown heroku commands return an error
    to catch typos and missing mock cases.
    """
    # Save original before patching
    original_run = subprocess.run

    def heroku_side_effect(cmd, *args, **kwargs):
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd

        if "heroku" not in cmd_str:
            # Not a heroku command, use real subprocess
            return original_run(cmd, *args, **kwargs)

        # Mock known heroku commands
        if "auth:whoami" in cmd_str:
            return Mock(returncode=0, stdout="e2e-test@example.com\n", stderr="")
        if "apps:info" in cmd_str:
            return Mock(returncode=0, stdout="=== e2e-test-app\n", stderr="")
        if "config:set" in cmd_str:
            return Mock(returncode=0, stdout="", stderr="")
        if "config:get" in cmd_str:
            return Mock(returncode=0, stdout="mock-value\n", stderr="")
        if "buildpacks" in cmd_str:
            return Mock(returncode=0, stdout="heroku/python\n", stderr="")
        if "addons" in cmd_str:
            return Mock(returncode=0, stdout="", stderr="")
        if "run" in cmd_str:
            return Mock(returncode=0, stdout="", stderr="")
        if "git:remote" in cmd_str:
            return Mock(returncode=0, stdout="", stderr="")

        # Unknown heroku command - return error to catch typos/missing mocks
        return Mock(
            returncode=1,
            stdout="",
            stderr=f"mock_heroku_cli: Unknown command '{cmd_str}'. Add a mock case.",
        )

    with patch("subprocess.run", side_effect=heroku_side_effect) as mock:
        yield mock


# =============================================================================
# PyPI Mocking Fixtures
# =============================================================================


@pytest.fixture
def mock_pypi_publish():
    """Mock PyPI publishing workflow.

    Mocks the publish-related functions to avoid actual PyPI uploads.
    """
    with patch("djb.cli.publish.run_cmd") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        yield mock_run


# =============================================================================
# Git Fixtures
# =============================================================================


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Initialize a real git repository for testing.

    Creates a git repo with test identity and initial commit.
    """
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    subprocess.run(["git", "init", str(repo_dir)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(repo_dir), "config", "user.email", "e2e-test@example.com"],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "config", "user.name", "E2E Test"],
        capture_output=True,
        check=True,
    )

    # Create initial commit
    readme = repo_dir / "README.md"
    readme.write_text("# Test Repository\n")
    subprocess.run(["git", "-C", str(repo_dir), "add", "."], capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_dir), "commit", "-m", "Initial commit"],
        capture_output=True,
    )

    return repo_dir


@pytest.fixture
def git_repo_with_commits(git_repo: Path) -> Path:
    """Git repo with multiple commits for revert testing."""
    # Add more commits
    for i in range(3):
        file_path = git_repo / f"file{i}.txt"
        file_path.write_text(f"Content {i}\n")
        subprocess.run(["git", "-C", str(git_repo), "add", "."], capture_output=True)
        subprocess.run(
            ["git", "-C", str(git_repo), "commit", "-m", f"Add file{i}"],
            capture_output=True,
        )

    return git_repo
