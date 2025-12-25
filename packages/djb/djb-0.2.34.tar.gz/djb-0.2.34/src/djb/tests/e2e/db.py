"""End-to-end tests for djb db CLI commands.

These tests exercise the database management CLI against real local PostgreSQL.

Commands tested:
- djb db init
- djb db status

Requirements:
- PostgreSQL must be installed and running locally

Run with: pytest --run-e2e
"""

from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from djb.config import reset_config
from djb.cli.db import (
    DbSettings,
    DbStatus,
    can_connect_as_user,
    check_postgres_installed,
    check_postgres_running,
    create_database,
    create_user_and_grant,
    database_exists,
    get_db_status,
    grant_schema_permissions,
    user_exists,
)
from djb.cli.djb import djb_cli


# Mark all tests in this module as e2e (skipped by default, use --run-e2e to include)
pytestmark = pytest.mark.e2e_skipped_by_default


@pytest.fixture(autouse=True)
def _require_postgres(require_postgres):
    """Skip tests if PostgreSQL is not available."""
    pass


@pytest.fixture
def test_db_settings(tmp_path: Path) -> DbSettings:
    """Generate unique database settings for this test.

    Uses a UUID-based name to ensure isolation between tests.
    """
    unique_id = uuid.uuid4().hex[:8]
    return DbSettings(
        name=f"djb_e2e_test_{unique_id}",
        user=f"djb_e2e_user_{unique_id}",
        password="test_password_123",
        host="localhost",
        port=5432,
    )


@pytest.fixture
def cleanup_db(test_db_settings: DbSettings):
    """Cleanup fixture that drops the test database and user after tests.

    Yields the settings, then cleans up regardless of test outcome.
    """
    yield test_db_settings

    # Clean up: drop database and user
    settings = test_db_settings

    # Drop database first (must disconnect all sessions)
    if database_exists(settings.name, settings.host, settings.port):
        # Force disconnect all sessions
        subprocess.run(
            [
                "psql",
                "-h",
                settings.host,
                "-p",
                str(settings.port),
                "postgres",
                "-c",
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                f"WHERE datname = '{settings.name}';",
            ],
            capture_output=True,
        )
        subprocess.run(
            [
                "psql",
                "-h",
                settings.host,
                "-p",
                str(settings.port),
                "postgres",
                "-c",
                f"DROP DATABASE IF EXISTS {settings.name};",
            ],
            capture_output=True,
        )

    # Drop user
    if user_exists(settings.user, settings.host, settings.port):
        subprocess.run(
            [
                "psql",
                "-h",
                settings.host,
                "-p",
                str(settings.port),
                "postgres",
                "-c",
                f"DROP USER IF EXISTS {settings.user};",
            ],
            capture_output=True,
        )


class TestDbFunctions:
    """E2E tests for database utility functions."""

    def test_check_postgres_installed(self):
        """Test that PostgreSQL is detected as installed."""
        assert check_postgres_installed() is True

    def test_check_postgres_running(self):
        """Test that PostgreSQL is detected as running."""
        assert check_postgres_running("localhost", 5432) is True

    def test_database_exists_false_for_nonexistent(self, test_db_settings: DbSettings):
        """Test that database_exists returns False for non-existent database."""
        # Use a random name that definitely doesn't exist
        assert database_exists(f"nonexistent_{uuid.uuid4().hex}", "localhost", 5432) is False

    def test_create_database_and_user(self, cleanup_db: DbSettings):
        """Test creating a database and user from scratch."""
        settings = cleanup_db

        # Initially neither should exist
        assert database_exists(settings.name, settings.host, settings.port) is False
        assert user_exists(settings.user, settings.host, settings.port) is False

        # Create database
        result = create_database(settings)
        assert result is True
        assert database_exists(settings.name, settings.host, settings.port) is True

        # Create user and grant privileges
        result = create_user_and_grant(settings)
        assert result is True
        assert user_exists(settings.user, settings.host, settings.port) is True

        # Grant schema permissions
        result = grant_schema_permissions(settings)
        assert result is True

        # Verify connection works
        assert can_connect_as_user(settings) is True

    def test_get_db_status_no_database(self, test_db_settings: DbSettings):
        """Test that status is NO_DATABASE when database doesn't exist."""
        # Use settings for a non-existent database
        status = get_db_status(test_db_settings)
        assert status == DbStatus.NO_DATABASE

    def test_get_db_status_ok(self, cleanup_db: DbSettings):
        """Test that status is OK when database is fully configured."""
        settings = cleanup_db

        # Create everything
        create_database(settings)
        create_user_and_grant(settings)
        grant_schema_permissions(settings)

        # Status should be OK
        status = get_db_status(settings)
        assert status == DbStatus.OK


class TestDbInit:
    """E2E tests for djb db init command."""

    def test_init_creates_database(
        self,
        runner,
        isolated_project,
        cleanup_db: DbSettings,
        djb_config_env,
    ):
        """Test that db init creates the database and user."""
        settings = cleanup_db

        # Initially database should not exist
        assert database_exists(settings.name, settings.host, settings.port) is False

        # Mock get_db_settings to return our test settings
        env = {
            **djb_config_env,
            "DJB_PROJECT_DIR": str(isolated_project),
        }

        with patch.dict(os.environ, env):
            with patch("djb.cli.db.get_db_settings", return_value=settings):
                result = runner.invoke(
                    djb_cli,
                    ["db", "init", "--no-start"],
                )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Database should now exist
        assert database_exists(settings.name, settings.host, settings.port) is True
        assert user_exists(settings.user, settings.host, settings.port) is True
        assert can_connect_as_user(settings) is True

    def test_init_is_idempotent(
        self,
        runner,
        isolated_project,
        cleanup_db: DbSettings,
        djb_config_env,
    ):
        """Test that running db init twice is safe."""
        settings = cleanup_db

        env = {
            **djb_config_env,
            "DJB_PROJECT_DIR": str(isolated_project),
        }

        with patch.dict(os.environ, env):
            with patch("djb.cli.db.get_db_settings", return_value=settings):
                # First run
                result1 = runner.invoke(
                    djb_cli,
                    ["db", "init", "--no-start"],
                )
                assert result1.exit_code == 0, f"First run failed: {result1.output}"

                # Reset config state between invocations
                reset_config()

                # Second run - should succeed without errors
                result2 = runner.invoke(
                    djb_cli,
                    ["db", "init", "--no-start"],
                )
                assert result2.exit_code == 0, f"Second run failed: {result2.output}"

        # Should still work
        assert can_connect_as_user(settings) is True


class TestDbStatus:
    """E2E tests for djb db status command."""

    def test_status_shows_not_configured(
        self,
        runner,
        isolated_project,
        test_db_settings: DbSettings,
        djb_config_env,
    ):
        """Test that status shows database not configured when it doesn't exist."""
        settings = test_db_settings

        env = {
            **djb_config_env,
            "DJB_PROJECT_DIR": str(isolated_project),
        }

        with patch.dict(os.environ, env):
            with patch("djb.cli.db.get_db_settings", return_value=settings):
                result = runner.invoke(
                    djb_cli,
                    ["db", "status"],
                )

        # Should complete but show database doesn't exist
        assert result.exit_code == 0
        assert "does not exist" in result.output or "not" in result.output.lower()

    def test_status_shows_configured(
        self,
        runner,
        isolated_project,
        cleanup_db: DbSettings,
        djb_config_env,
    ):
        """Test that status shows database is configured when it exists."""
        settings = cleanup_db

        # Create the database first
        create_database(settings)
        create_user_and_grant(settings)
        grant_schema_permissions(settings)

        env = {
            **djb_config_env,
            "DJB_PROJECT_DIR": str(isolated_project),
        }

        with patch.dict(os.environ, env):
            with patch("djb.cli.db.get_db_settings", return_value=settings):
                result = runner.invoke(
                    djb_cli,
                    ["db", "status"],
                )

        assert result.exit_code == 0
        # Should show database name and indicate it's accessible
        assert settings.name in result.output
        assert "accessible" in result.output.lower() or "configured" in result.output.lower()
