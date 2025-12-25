"""Tests for djb db module."""

from __future__ import annotations

import os
from unittest.mock import Mock, patch

import pytest

from djb import configure
from djb.cli.db import (
    DbSettings,
    DbStatus,
    can_connect_as_user,
    check_postgres_installed,
    check_postgres_running,
    create_database,
    create_user_and_grant,
    database_exists,
    get_db_settings,
    get_db_status,
    init_database,
    user_exists,
)
from djb.cli.djb import djb_cli
from djb.secrets import SopsError


class TestDbSettings:
    """Tests for DbSettings dataclass."""

    def test_dataclass_fields(self):
        """Test DbSettings has expected fields."""
        settings = DbSettings(
            name="testdb",
            user="testuser",
            password="testpass",
            host="localhost",
            port=5432,
        )
        assert settings.name == "testdb"
        assert settings.user == "testuser"
        assert settings.password == "testpass"
        assert settings.host == "localhost"
        assert settings.port == 5432


class TestGetDbSettings:
    """Tests for get_db_settings function."""

    def test_falls_back_to_defaults(self, tmp_path):
        """Test falls back to project-name-based defaults when secrets unavailable."""
        os.environ.pop("DJB_PROJECT_NAME", None)  # Clear to test pyproject fallback
        configure(project_dir=tmp_path)

        # Create a pyproject.toml with project name
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "my-cool-project"\n')

        with patch("djb.cli.db._get_db_settings_from_secrets", return_value=None):
            settings = get_db_settings()

        assert settings.name == "my_cool_project"  # hyphens converted to underscores
        assert settings.user == "my_cool_project"
        assert settings.password == "foobarqux"
        assert settings.host == "localhost"
        assert settings.port == 5432

    def test_uses_secrets_when_available(self, tmp_path):
        """Test uses secrets when db_credentials found in dev secrets."""
        configure(project_dir=tmp_path)

        secrets_settings = DbSettings(
            name="secrets_db",
            user="secrets_user",
            password="secrets_pass",
            host="db.example.com",
            port=5433,
        )

        with patch("djb.cli.db._get_db_settings_from_secrets", return_value=secrets_settings):
            settings = get_db_settings()

        assert settings.name == "secrets_db"
        assert settings.user == "secrets_user"
        assert settings.password == "secrets_pass"
        assert settings.host == "db.example.com"
        assert settings.port == 5433

    def test_falls_back_when_secrets_incomplete(self, tmp_path):
        """Test falls back to defaults when secrets have empty name/user."""
        os.environ.pop("DJB_PROJECT_NAME", None)  # Clear to test pyproject fallback
        configure(project_dir=tmp_path)

        # Create a pyproject.toml with project name
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "my-project"\n')

        incomplete_settings = DbSettings(
            name="",  # Empty name
            user="",  # Empty user
            password="some_pass",
            host="localhost",
            port=5432,
        )

        with patch("djb.cli.db._get_db_settings_from_secrets", return_value=incomplete_settings):
            settings = get_db_settings()

        # Should fall back to defaults
        assert settings.name == "my_project"
        assert settings.user == "my_project"

    def test_falls_back_on_sops_decryption_error(self, tmp_path):
        """Test falls back to defaults when SOPS decryption fails (user not in .sops.yaml)."""
        os.environ.pop("DJB_PROJECT_NAME", None)  # Clear to test pyproject fallback
        configure(project_dir=tmp_path)

        # Create a pyproject.toml with project name
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "new-user-project"\n')

        # Create secrets directory so it doesn't short-circuit
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        with patch("djb.secrets.load_secrets", side_effect=SopsError("Failed to decrypt")):
            settings = get_db_settings()

        # Should fall back to defaults
        assert settings.name == "new_user_project"
        assert settings.user == "new_user_project"
        assert settings.password == "foobarqux"


class TestPostgresChecks:
    """Tests for PostgreSQL availability checks."""

    def test_check_postgres_installed_when_present(self):
        """Test check_postgres_installed returns True when psql is available."""
        with patch("djb.cli.db.shutil.which", return_value="/usr/bin/psql"):
            assert check_postgres_installed() is True

    def test_check_postgres_installed_when_missing(self):
        """Test check_postgres_installed returns False when psql is missing."""
        with patch("djb.cli.db.shutil.which", return_value=None):
            assert check_postgres_installed() is False

    def test_check_postgres_running_success(self):
        """Test check_postgres_running returns True when server is up."""
        with (
            patch("djb.cli.db.shutil.which", return_value="/usr/bin/pg_isready"),
            patch("djb.cli.db.subprocess.run") as mock_run,
        ):
            mock_run.return_value = Mock(returncode=0)
            assert check_postgres_running() is True

    def test_check_postgres_running_failure(self):
        """Test check_postgres_running returns False when server is down."""
        with (
            patch("djb.cli.db.shutil.which", return_value="/usr/bin/pg_isready"),
            patch("djb.cli.db.subprocess.run") as mock_run,
        ):
            mock_run.return_value = Mock(returncode=1)
            assert check_postgres_running() is False

    def test_check_postgres_running_no_pg_isready(self):
        """Test check_postgres_running returns False when pg_isready is missing."""
        with patch("djb.cli.db.shutil.which", return_value=None):
            assert check_postgres_running() is False


class TestDatabaseOperations:
    """Tests for database existence and connection checks."""

    def test_database_exists_true(self):
        """Test database_exists returns True when database exists."""
        with patch("djb.cli.db._run_psql") as mock_psql:
            mock_psql.return_value = Mock(stdout="1\n", returncode=0)
            assert database_exists("mydb") is True

    def test_database_exists_false(self):
        """Test database_exists returns False when database doesn't exist."""
        with patch("djb.cli.db._run_psql") as mock_psql:
            mock_psql.return_value = Mock(stdout="", returncode=0)
            assert database_exists("mydb") is False

    def test_user_exists_true(self):
        """Test user_exists returns True when user exists."""
        with patch("djb.cli.db._run_psql") as mock_psql:
            mock_psql.return_value = Mock(stdout="1\n", returncode=0)
            assert user_exists("myuser") is True

    def test_user_exists_false(self):
        """Test user_exists returns False when user doesn't exist."""
        with patch("djb.cli.db._run_psql") as mock_psql:
            mock_psql.return_value = Mock(stdout="", returncode=0)
            assert user_exists("myuser") is False

    def test_can_connect_as_user_success(self):
        """Test can_connect_as_user returns True on successful connection."""
        settings = DbSettings(
            name="testdb",
            user="testuser",
            password="testpass",
            host="localhost",
            port=5432,
        )
        with patch("djb.cli.db.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            assert can_connect_as_user(settings) is True

    def test_can_connect_as_user_failure(self):
        """Test can_connect_as_user returns False on connection failure."""
        settings = DbSettings(
            name="testdb",
            user="testuser",
            password="testpass",
            host="localhost",
            port=5432,
        )
        with patch("djb.cli.db.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1)
            assert can_connect_as_user(settings) is False


class TestDbStatus:
    """Tests for get_db_status function."""

    def test_status_uninstalled(self):
        """Test returns UNINSTALLED when PostgreSQL not installed."""
        settings = DbSettings("db", "user", "pass", "localhost", 5432)
        with patch("djb.cli.db.check_postgres_installed", return_value=False):
            assert get_db_status(settings) == DbStatus.UNINSTALLED

    def test_status_unreachable(self):
        """Test returns UNREACHABLE when PostgreSQL not running."""
        settings = DbSettings("db", "user", "pass", "localhost", 5432)
        with (
            patch("djb.cli.db.check_postgres_installed", return_value=True),
            patch("djb.cli.db.check_postgres_running", return_value=False),
        ):
            assert get_db_status(settings) == DbStatus.UNREACHABLE

    def test_status_no_database(self):
        """Test returns NO_DATABASE when database doesn't exist."""
        settings = DbSettings("db", "user", "pass", "localhost", 5432)
        with (
            patch("djb.cli.db.check_postgres_installed", return_value=True),
            patch("djb.cli.db.check_postgres_running", return_value=True),
            patch("djb.cli.db.database_exists", return_value=False),
        ):
            assert get_db_status(settings) == DbStatus.NO_DATABASE

    def test_status_no_user(self):
        """Test returns NO_USER when user doesn't exist."""
        settings = DbSettings("db", "user", "pass", "localhost", 5432)
        with (
            patch("djb.cli.db.check_postgres_installed", return_value=True),
            patch("djb.cli.db.check_postgres_running", return_value=True),
            patch("djb.cli.db.database_exists", return_value=True),
            patch("djb.cli.db.user_exists", return_value=False),
        ):
            assert get_db_status(settings) == DbStatus.NO_USER

    def test_status_ok(self):
        """Test returns OK when everything is set up."""
        settings = DbSettings("db", "user", "pass", "localhost", 5432)
        with (
            patch("djb.cli.db.check_postgres_installed", return_value=True),
            patch("djb.cli.db.check_postgres_running", return_value=True),
            patch("djb.cli.db.database_exists", return_value=True),
            patch("djb.cli.db.user_exists", return_value=True),
            patch("djb.cli.db.can_connect_as_user", return_value=True),
        ):
            assert get_db_status(settings) == DbStatus.OK


class TestCreateDatabase:
    """Tests for create_database function."""

    def test_skips_when_exists(self):
        """Test skips creation when database already exists."""
        settings = DbSettings("testdb", "user", "pass", "localhost", 5432)
        with patch("djb.cli.db.database_exists", return_value=True):
            result = create_database(settings)
        assert result is True

    def test_creates_when_missing(self):
        """Test creates database when it doesn't exist."""
        settings = DbSettings("testdb", "user", "pass", "localhost", 5432)
        with (
            patch("djb.cli.db.database_exists", return_value=False),
            patch("djb.cli.db._run_psql") as mock_psql,
        ):
            mock_psql.return_value = Mock(returncode=0)
            result = create_database(settings)
        assert result is True
        mock_psql.assert_called_once()

    def test_returns_false_on_error(self):
        """Test returns False when creation fails."""
        settings = DbSettings("testdb", "user", "pass", "localhost", 5432)
        with (
            patch("djb.cli.db.database_exists", return_value=False),
            patch("djb.cli.db._run_psql") as mock_psql,
        ):
            mock_psql.return_value = Mock(returncode=1, stderr="error")
            result = create_database(settings)
        assert result is False


class TestCreateUserAndGrant:
    """Tests for create_user_and_grant function."""

    def test_creates_user_when_missing(self):
        """Test creates user when it doesn't exist."""
        settings = DbSettings("testdb", "testuser", "testpass", "localhost", 5432)
        with (
            patch("djb.cli.db.user_exists", return_value=False),
            patch("djb.cli.db._run_psql") as mock_psql,
        ):
            mock_psql.return_value = Mock(returncode=0)
            result = create_user_and_grant(settings)
        assert result is True

    def test_updates_existing_user(self):
        """Test updates password for existing user."""
        settings = DbSettings("testdb", "testuser", "testpass", "localhost", 5432)
        with (
            patch("djb.cli.db.user_exists", return_value=True),
            patch("djb.cli.db._run_psql") as mock_psql,
        ):
            mock_psql.return_value = Mock(returncode=0)
            result = create_user_and_grant(settings)
        assert result is True

    def test_returns_false_on_error(self):
        """Test returns False when operation fails."""
        settings = DbSettings("testdb", "testuser", "testpass", "localhost", 5432)
        with (
            patch("djb.cli.db.user_exists", return_value=False),
            patch("djb.cli.db._run_psql") as mock_psql,
        ):
            mock_psql.return_value = Mock(returncode=1, stderr="error")
            result = create_user_and_grant(settings)
        assert result is False


class TestInitDatabase:
    """Tests for init_database function."""

    def test_returns_true_when_already_configured(self):
        """Test returns True immediately when database is already OK."""
        with (
            patch("djb.cli.db.get_db_settings") as mock_settings,
            patch("djb.cli.db.check_postgres_installed", return_value=True),
            patch("djb.cli.db.check_postgres_running", return_value=True),
            patch("djb.cli.db.get_db_status", return_value=DbStatus.OK),
        ):
            mock_settings.return_value = DbSettings("db", "user", "pass", "localhost", 5432)
            result = init_database(quiet=True)
        assert result is True

    def test_returns_false_when_postgres_not_installed(self):
        """Test returns False when PostgreSQL not installed."""
        with (
            patch("djb.cli.db.get_db_settings") as mock_settings,
            patch("djb.cli.db.check_postgres_installed", return_value=False),
        ):
            mock_settings.return_value = DbSettings("db", "user", "pass", "localhost", 5432)
            result = init_database(quiet=True)
        assert result is False

    def test_creates_database_and_user(self):
        """Test creates database and user when they don't exist."""
        with (
            patch("djb.cli.db.get_db_settings") as mock_settings,
            patch("djb.cli.db.check_postgres_installed", return_value=True),
            patch("djb.cli.db.check_postgres_running", return_value=True),
            patch("djb.cli.db.get_db_status", return_value=DbStatus.NO_DATABASE),
            patch("djb.cli.db.create_database", return_value=True) as mock_create_db,
            patch("djb.cli.db.create_user_and_grant", return_value=True) as mock_create_user,
            patch("djb.cli.db.grant_schema_permissions", return_value=True),
            patch("djb.cli.db.can_connect_as_user", return_value=True),
        ):
            mock_settings.return_value = DbSettings("db", "user", "pass", "localhost", 5432)
            result = init_database(quiet=True)

        assert result is True
        mock_create_db.assert_called_once()
        mock_create_user.assert_called_once()


class TestDbCLI:
    """Tests for djb db CLI commands."""

    def test_help(self, runner):
        """Test djb db --help works."""
        result = runner.invoke(djb_cli, ["db", "--help"])
        assert result.exit_code == 0
        assert "Database management commands" in result.output

    def test_init_help(self, runner):
        """Test djb db init --help works."""
        result = runner.invoke(djb_cli, ["db", "init", "--help"])
        assert result.exit_code == 0
        assert "Initialize development database" in result.output
        assert "--no-start" in result.output

    def test_status_help(self, runner):
        """Test djb db status --help works."""
        result = runner.invoke(djb_cli, ["db", "status", "--help"])
        assert result.exit_code == 0
        assert "Show database connection status" in result.output

    def test_init_success(self, runner, tmp_path):
        """Test djb db init succeeds when everything works."""
        with (
            patch("djb.cli.db.get_db_settings") as mock_settings,
            patch("djb.cli.db.check_postgres_installed", return_value=True),
            patch("djb.cli.db.check_postgres_running", return_value=True),
            patch("djb.cli.db.get_db_status", return_value=DbStatus.OK),
        ):
            mock_settings.return_value = DbSettings("db", "user", "pass", "localhost", 5432)
            result = runner.invoke(djb_cli, ["db", "init"])

        assert result.exit_code == 0

    def test_init_failure_no_postgres(self, runner, tmp_path):
        """Test djb db init fails gracefully when PostgreSQL not installed."""
        with (
            patch("djb.cli.db.get_db_settings") as mock_settings,
            patch("djb.cli.db.check_postgres_installed", return_value=False),
        ):
            mock_settings.return_value = DbSettings("db", "user", "pass", "localhost", 5432)
            result = runner.invoke(djb_cli, ["db", "init"])

        assert result.exit_code == 1
        assert "failed" in result.output.lower() or "not installed" in result.output.lower()

    def test_status_command(self, runner, tmp_path):
        """Test djb db status shows configuration."""
        with (
            patch("djb.cli.db.get_db_settings") as mock_settings,
            patch("djb.cli.db.get_db_status", return_value=DbStatus.OK),
        ):
            mock_settings.return_value = DbSettings("testdb", "testuser", "pass", "localhost", 5432)
            result = runner.invoke(djb_cli, ["db", "status"])

        assert result.exit_code == 0
        assert "testdb" in result.output
        assert "testuser" in result.output
