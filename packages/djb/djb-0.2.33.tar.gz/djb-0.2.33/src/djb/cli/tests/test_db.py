"""Tests for djb db module."""

from __future__ import annotations

import os
import subprocess
from unittest.mock import Mock, patch

import pytest

from djb import configure
from djb.cli.db import (
    DbSettings,
    DbStatus,
    _get_db_settings_from_secrets,
    _get_default_db_settings,
    _run_psql,
    can_connect_as_user,
    check_postgres_installed,
    check_postgres_running,
    create_database,
    create_user_and_grant,
    database_exists,
    get_db_settings,
    get_db_status,
    grant_schema_permissions,
    init_database,
    start_postgres_service,
    user_exists,
    wait_for_postgres,
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


class TestWaitForPostgres:
    """Tests for wait_for_postgres function - polling pattern with timeout."""

    def test_returns_true_on_immediate_success(self):
        """Test returns True when PostgreSQL is immediately available."""
        with (
            patch("djb.cli.db.check_postgres_running", return_value=True),
            patch("djb.cli.db.sleep") as mock_sleep,
        ):
            result = wait_for_postgres()

        assert result is True
        mock_sleep.assert_not_called()

    def test_retries_until_success(self):
        """Test retries with polling until PostgreSQL becomes available."""
        with (
            patch("djb.cli.db.check_postgres_running") as mock_check,
            patch("djb.cli.db.sleep") as mock_sleep,
            patch("djb.cli.db.time") as mock_time,
        ):
            # First two checks fail, third succeeds
            mock_check.side_effect = [False, False, True]
            # Time progresses: start at 0, then 0.5, then 1 (still under timeout)
            mock_time.side_effect = [0, 0.5, 1, 1.5]

            result = wait_for_postgres(timeout=10.0)

        assert result is True
        assert mock_check.call_count == 3
        # Should have slept twice (after first and second failures)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(0.5)

    def test_returns_false_on_timeout(self):
        """Test returns False when timeout is reached."""
        with (
            patch("djb.cli.db.check_postgres_running", return_value=False),
            patch("djb.cli.db.sleep"),
            patch("djb.cli.db.time") as mock_time,
        ):
            # Time progresses past timeout
            mock_time.side_effect = [0, 11]  # start, past timeout of 10

            result = wait_for_postgres(timeout=10.0)

        assert result is False

    def test_uses_custom_timeout(self):
        """Test uses custom timeout value."""
        with (
            patch("djb.cli.db.check_postgres_running", return_value=False),
            patch("djb.cli.db.sleep"),
            patch("djb.cli.db.time") as mock_time,
        ):
            # With custom timeout of 5, time=6 should exceed it
            mock_time.side_effect = [0, 6]

            result = wait_for_postgres(timeout=5.0)

        assert result is False

    def test_custom_host_and_port(self):
        """Test passes custom host and port to check_postgres_running."""
        with (
            patch("djb.cli.db.check_postgres_running", return_value=True) as mock_check,
            patch("djb.cli.db.sleep"),
        ):
            result = wait_for_postgres(host="db.example.com", port=5433)

        assert result is True
        mock_check.assert_called_with("db.example.com", 5433)


class TestStartPostgresService:
    """Tests for start_postgres_service function - Homebrew service commands."""

    def test_returns_true_when_postgresql17_starts(self):
        """Test returns True when postgresql@17 service starts successfully."""
        with (
            patch("djb.cli.db.check_cmd", return_value=True),
            patch("djb.cli.db.subprocess.run") as mock_run,
        ):
            mock_run.return_value = Mock(returncode=0)
            result = start_postgres_service()

        assert result is True
        mock_run.assert_called_once_with(
            ["brew", "services", "start", "postgresql@17"],
            capture_output=True,
            text=True,
        )

    def test_falls_back_to_postgresql_without_version(self):
        """Test falls back to 'postgresql' when 'postgresql@17' fails."""
        with (
            patch("djb.cli.db.check_cmd", return_value=True),
            patch("djb.cli.db.subprocess.run") as mock_run,
        ):
            # First call (postgresql@17) fails, second (postgresql) succeeds
            mock_run.side_effect = [
                Mock(returncode=1),
                Mock(returncode=0),
            ]
            result = start_postgres_service()

        assert result is True
        assert mock_run.call_count == 2
        # Check that it tried postgresql after postgresql@17 failed
        calls = mock_run.call_args_list
        assert calls[0][0][0] == ["brew", "services", "start", "postgresql@17"]
        assert calls[1][0][0] == ["brew", "services", "start", "postgresql"]

    def test_returns_false_when_both_fail(self):
        """Test returns False when both postgresql@17 and postgresql fail."""
        with (
            patch("djb.cli.db.check_cmd", return_value=True),
            patch("djb.cli.db.subprocess.run") as mock_run,
        ):
            # Both calls fail
            mock_run.return_value = Mock(returncode=1)
            result = start_postgres_service()

        assert result is False
        assert mock_run.call_count == 2

    def test_returns_false_when_brew_not_available(self):
        """Test returns False when Homebrew is not available."""
        with patch("djb.cli.db.check_cmd", return_value=False):
            result = start_postgres_service()

        assert result is False


class TestGetDbSettingsFromSecrets:
    """Tests for _get_db_settings_from_secrets function - exception handling."""

    def test_returns_none_when_secrets_dir_missing(self, tmp_path):
        """Test returns None when secrets directory doesn't exist."""
        configure(project_dir=tmp_path)

        result = _get_db_settings_from_secrets()

        assert result is None

    def test_returns_settings_from_secrets(self, tmp_path):
        """Test returns DbSettings when secrets are available."""
        configure(project_dir=tmp_path)

        # Create secrets directory
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        mock_secrets = {
            "db_credentials": {
                "database": "mydb",
                "username": "myuser",
                "password": "mypass",
                "host": "db.example.com",
                "port": 5433,
            }
        }

        with patch("djb.cli.db.load_secrets", return_value=mock_secrets):
            result = _get_db_settings_from_secrets()

        assert result is not None
        assert result.name == "mydb"
        assert result.user == "myuser"
        assert result.password == "mypass"
        assert result.host == "db.example.com"
        assert result.port == 5433

    def test_returns_none_on_sops_decrypt_error(self, tmp_path):
        """Test returns None when SOPS decryption fails (key not in .sops.yaml)."""
        configure(project_dir=tmp_path)

        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        with patch("djb.cli.db.load_secrets", side_effect=SopsError("Failed to decrypt")):
            result = _get_db_settings_from_secrets()

        assert result is None

    def test_returns_none_on_sops_key_error(self, tmp_path):
        """Test returns None when SOPS reports key error."""
        configure(project_dir=tmp_path)

        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        with patch(
            "djb.cli.db.load_secrets",
            side_effect=SopsError("could not find key for recipient"),
        ):
            result = _get_db_settings_from_secrets()

        assert result is None

    def test_returns_none_on_sops_recipient_error(self, tmp_path):
        """Test returns None when SOPS reports recipient error."""
        configure(project_dir=tmp_path)

        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        with patch(
            "djb.cli.db.load_secrets",
            side_effect=SopsError("no matching recipient found"),
        ):
            result = _get_db_settings_from_secrets()

        assert result is None

    def test_returns_none_on_file_not_found(self, tmp_path):
        """Test returns None when secrets file is not found."""
        configure(project_dir=tmp_path)

        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        with patch("djb.cli.db.load_secrets", side_effect=FileNotFoundError("dev.yaml not found")):
            result = _get_db_settings_from_secrets()

        assert result is None

    def test_returns_none_when_db_credentials_not_dict(self, tmp_path):
        """Test returns None when db_credentials is not a dictionary."""
        configure(project_dir=tmp_path)

        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        mock_secrets = {"db_credentials": "not a dict"}

        with patch("djb.cli.db.load_secrets", return_value=mock_secrets):
            result = _get_db_settings_from_secrets()

        assert result is None

    def test_returns_none_when_db_credentials_missing(self, tmp_path):
        """Test returns None when db_credentials key is missing."""
        configure(project_dir=tmp_path)

        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        mock_secrets = {"other_key": "value"}

        with patch("djb.cli.db.load_secrets", return_value=mock_secrets):
            result = _get_db_settings_from_secrets()

        assert result is None

    def test_uses_defaults_for_missing_optional_fields(self, tmp_path):
        """Test uses defaults for host and port when not provided."""
        configure(project_dir=tmp_path)

        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        # Only provide required fields
        mock_secrets = {
            "db_credentials": {
                "database": "mydb",
                "username": "myuser",
                "password": "mypass",
            }
        }

        with patch("djb.cli.db.load_secrets", return_value=mock_secrets):
            result = _get_db_settings_from_secrets()

        assert result is not None
        assert result.host == "localhost"
        assert result.port == 5432


class TestGetDefaultDbSettings:
    """Tests for _get_default_db_settings function - configuration with fallback."""

    def test_uses_project_name_from_config(self, tmp_path):
        """Test uses project name from djb config."""
        os.environ["DJB_PROJECT_NAME"] = "my-project"
        configure(project_dir=tmp_path)

        result = _get_default_db_settings()

        assert result.name == "my_project"  # hyphens converted to underscores
        assert result.user == "my_project"
        assert result.password == "foobarqux"
        assert result.host == "localhost"
        assert result.port == 5432

        os.environ.pop("DJB_PROJECT_NAME", None)

    def test_uses_directory_name_as_fallback(self, tmp_path):
        """Test uses directory name when project_name not configured."""
        os.environ.pop("DJB_PROJECT_NAME", None)
        configure(project_dir=tmp_path)

        # Create pyproject.toml without project name
        (tmp_path / "pyproject.toml").write_text("[tool.other]\nkey = 'value'\n")

        result = _get_default_db_settings()

        # Should use the tmp_path directory name (sanitized)
        assert result.name == tmp_path.name.replace("-", "_")
        assert result.user == tmp_path.name.replace("-", "_")

    def test_sanitizes_hyphens_to_underscores(self, tmp_path):
        """Test converts hyphens to underscores for database/user names."""
        os.environ["DJB_PROJECT_NAME"] = "my-cool-app"
        configure(project_dir=tmp_path)

        result = _get_default_db_settings()

        assert result.name == "my_cool_app"
        assert result.user == "my_cool_app"

        os.environ.pop("DJB_PROJECT_NAME", None)


class TestGrantSchemaPermissions:
    """Tests for grant_schema_permissions function - idempotent database operation."""

    def test_returns_true_on_success(self):
        """Test returns True when grant succeeds."""
        settings = DbSettings("testdb", "testuser", "testpass", "localhost", 5432)

        with patch("djb.cli.db.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = grant_schema_permissions(settings)

        assert result is True
        mock_run.assert_called_once()
        # Verify correct psql command
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "psql"
        assert "-h" in call_args and "localhost" in call_args
        assert "-p" in call_args and "5432" in call_args
        assert "testdb" in call_args
        assert "GRANT ALL ON SCHEMA public TO testuser" in call_args[-1]

    def test_returns_true_on_failure_non_fatal(self):
        """Test returns True even when grant fails (non-fatal operation)."""
        settings = DbSettings("testdb", "testuser", "testpass", "localhost", 5432)

        with patch("djb.cli.db.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stderr="permission denied")
            result = grant_schema_permissions(settings)

        # Non-fatal, should still return True
        assert result is True

    def test_uses_correct_host_and_port(self):
        """Test uses correct host and port in psql command."""
        settings = DbSettings("mydb", "myuser", "pass", "db.example.com", 5433)

        with patch("djb.cli.db.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            grant_schema_permissions(settings)

        call_args = mock_run.call_args[0][0]
        assert "-h" in call_args
        host_idx = call_args.index("-h")
        assert call_args[host_idx + 1] == "db.example.com"
        port_idx = call_args.index("-p")
        assert call_args[port_idx + 1] == "5433"

    def test_grants_to_correct_user(self):
        """Test grants permissions to the correct user."""
        settings = DbSettings("testdb", "custom_user", "pass", "localhost", 5432)

        with patch("djb.cli.db.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            grant_schema_permissions(settings)

        call_args = mock_run.call_args[0][0]
        grant_cmd = call_args[-1]
        assert "GRANT ALL ON SCHEMA public TO custom_user" in grant_cmd


class TestRunPsql:
    """Tests for _run_psql function - internal psql query runner."""

    def test_runs_psql_with_default_params(self):
        """Test runs psql with default host, port, and database."""
        with patch("djb.cli.db.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="result", stderr="")
            result = _run_psql("SELECT 1;")

        assert result.returncode == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "psql"
        assert "-h" in call_args and "localhost" in call_args
        assert "-p" in call_args and "5432" in call_args
        assert "postgres" in call_args  # default database
        assert "-tAc" in call_args
        assert "SELECT 1;" in call_args

    def test_runs_psql_with_custom_params(self):
        """Test runs psql with custom database, host, and port."""
        with patch("djb.cli.db.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            _run_psql("SELECT 1;", database="mydb", host="db.example.com", port=5433)

        call_args = mock_run.call_args[0][0]
        host_idx = call_args.index("-h")
        assert call_args[host_idx + 1] == "db.example.com"
        port_idx = call_args.index("-p")
        assert call_args[port_idx + 1] == "5433"
        assert "mydb" in call_args

    def test_captures_output_as_text(self):
        """Test captures stdout and stderr as text."""
        with patch("djb.cli.db.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="output", stderr="error")
            _run_psql("SELECT 1;")

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["capture_output"] is True
        assert call_kwargs["text"] is True


class TestCanConnectAsUserEdgeCases:
    """Additional edge case tests for can_connect_as_user function."""

    def test_returns_false_on_subprocess_error(self):
        """Test returns False when subprocess raises SubprocessError."""
        settings = DbSettings("testdb", "testuser", "testpass", "localhost", 5432)

        with patch("djb.cli.db.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.SubprocessError("psql execution failed")
            result = can_connect_as_user(settings)

        assert result is False


class TestInitDatabaseEdgeCases:
    """Additional edge case tests for init_database function."""

    def test_returns_false_when_postgres_not_running_no_start(self):
        """Test returns False when PostgreSQL not running and start_service=False."""
        with (
            patch("djb.cli.db.get_db_settings") as mock_settings,
            patch("djb.cli.db.check_postgres_installed", return_value=True),
            patch("djb.cli.db.check_postgres_running", return_value=False),
        ):
            mock_settings.return_value = DbSettings("db", "user", "pass", "localhost", 5432)
            result = init_database(start_service=False, quiet=True)

        assert result is False

    def test_returns_false_when_create_user_fails(self):
        """Test returns False when create_user_and_grant fails."""
        with (
            patch("djb.cli.db.get_db_settings") as mock_settings,
            patch("djb.cli.db.check_postgres_installed", return_value=True),
            patch("djb.cli.db.check_postgres_running", return_value=True),
            patch("djb.cli.db.get_db_status", return_value=DbStatus.NO_DATABASE),
            patch("djb.cli.db.create_database", return_value=True),
            patch("djb.cli.db.create_user_and_grant", return_value=False),
        ):
            mock_settings.return_value = DbSettings("db", "user", "pass", "localhost", 5432)
            result = init_database(quiet=True)

        assert result is False

    def test_returns_false_when_final_connection_fails(self):
        """Test returns False when final can_connect_as_user check fails."""
        with (
            patch("djb.cli.db.get_db_settings") as mock_settings,
            patch("djb.cli.db.check_postgres_installed", return_value=True),
            patch("djb.cli.db.check_postgres_running", return_value=True),
            patch("djb.cli.db.get_db_status", return_value=DbStatus.NO_DATABASE),
            patch("djb.cli.db.create_database", return_value=True),
            patch("djb.cli.db.create_user_and_grant", return_value=True),
            patch("djb.cli.db.grant_schema_permissions", return_value=True),
            patch("djb.cli.db.can_connect_as_user", return_value=False),
        ):
            mock_settings.return_value = DbSettings("db", "user", "pass", "localhost", 5432)
            result = init_database(quiet=True)

        assert result is False

    def test_handles_status_no_user_skips_create_database(self):
        """Test when status is NO_USER, it skips database creation but creates user."""
        with (
            patch("djb.cli.db.get_db_settings") as mock_settings,
            patch("djb.cli.db.check_postgres_installed", return_value=True),
            patch("djb.cli.db.check_postgres_running", return_value=True),
            patch("djb.cli.db.get_db_status", return_value=DbStatus.NO_USER),
            patch("djb.cli.db.create_database") as mock_create_db,
            patch("djb.cli.db.create_user_and_grant", return_value=True) as mock_create_user,
            patch("djb.cli.db.grant_schema_permissions", return_value=True),
            patch("djb.cli.db.can_connect_as_user", return_value=True),
        ):
            mock_settings.return_value = DbSettings("db", "user", "pass", "localhost", 5432)
            result = init_database(quiet=True)

        assert result is True
        # NO_USER status means database exists, so should NOT call create_database
        mock_create_db.assert_not_called()
        # But should still call create_user_and_grant
        mock_create_user.assert_called_once()

    def test_returns_false_when_wait_for_postgres_fails(self):
        """Test returns False when waiting for PostgreSQL times out."""
        with (
            patch("djb.cli.db.get_db_settings") as mock_settings,
            patch("djb.cli.db.check_postgres_installed", return_value=True),
            patch("djb.cli.db.check_postgres_running", return_value=False),
            patch("djb.cli.db.start_postgres_service", return_value=True),
            patch("djb.cli.db.wait_for_postgres", return_value=False),
        ):
            mock_settings.return_value = DbSettings("db", "user", "pass", "localhost", 5432)
            result = init_database(start_service=True, quiet=True)

        assert result is False
