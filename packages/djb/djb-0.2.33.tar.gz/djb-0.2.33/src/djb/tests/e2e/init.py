"""End-to-end tests for djb init CLI command.

These tests exercise the init command while mocking external installers
(Homebrew, uv, bun) to avoid side effects.

Commands tested:
- djb init

Run with: pytest --run-e2e
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from djb.cli.djb import djb_cli
from djb.cli.init import (
    _add_djb_to_installed_apps,
    _find_settings_file,
    _update_gitignore_for_project_config,
)
from djb.config import reset_config
from djb.config.acquisition import GitConfigSource

from . import (
    add_django_settings_from_startproject,
    add_initial_commit,
    create_pyproject_toml,
    init_git_repo,
)


# Mark all tests in this module as e2e (skipped by default, use --run-e2e to include)
pytestmark = pytest.mark.e2e_skipped_by_default


@pytest.fixture
def django_project(tmp_path: Path) -> Path:
    """Create a realistic Django project structure using django-admin startproject.

    Creates:
    - pyproject.toml
    - manage.py
    - myproject/ (complete Django settings via startproject)
    - .git initialized
    - .gitignore with .djb/
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    create_pyproject_toml(project_dir, name="myproject")
    add_django_settings_from_startproject(project_dir)

    # Create .gitignore (without .djb/local.yaml so we can test adding it)
    gitignore = project_dir / ".gitignore"
    gitignore.write_text("# Python\n*.pyc\n__pycache__/\n")

    init_git_repo(project_dir, user_email="test@example.com", user_name="Test User")
    add_initial_commit(project_dir)

    return project_dir


class TestInitHelperFunctions:
    """E2E tests for init helper functions."""

    def test_find_settings_file(self, django_project: Path):
        """Test finding Django settings.py."""
        settings_path = _find_settings_file(django_project)
        assert settings_path is not None
        assert settings_path.name == "settings.py"
        assert settings_path.parent.name == "myproject"

    def test_find_settings_file_not_found(self, tmp_path: Path):
        """Test when no settings.py exists."""
        project = tmp_path / "empty"
        project.mkdir()
        settings_path = _find_settings_file(project)
        assert settings_path is None

    def test_add_djb_to_installed_apps(self, django_project: Path):
        """Test adding djb to INSTALLED_APPS."""
        result = _add_djb_to_installed_apps(django_project)
        assert result is True

        # Verify djb is in the settings
        settings = django_project / "myproject" / "settings.py"
        content = settings.read_text()
        assert '"djb"' in content or "'djb'" in content

    def test_add_djb_to_installed_apps_already_present(self, django_project: Path):
        """Test that adding djb is idempotent."""
        # Add djb first time
        result1 = _add_djb_to_installed_apps(django_project)
        assert result1 is True

        # Second time should return False (already present)
        result2 = _add_djb_to_installed_apps(django_project)
        assert result2 is False

    def test_update_gitignore_for_project_config(self, django_project: Path):
        """Test adding .djb/local.yaml to .gitignore."""
        result = _update_gitignore_for_project_config(django_project)
        assert result is True

        gitignore = django_project / ".gitignore"
        content = gitignore.read_text()
        assert ".djb/local.yaml" in content
        assert content.count(".djb/local.yaml") == 1

    def test_git_config_source_reads_values(self, django_project: Path):
        """Test reading git config values from global config."""
        # GitConfigSource reads global config, so it returns the user's actual values
        # We just verify it can read some value (not specifically what we set in the test repo)
        email = GitConfigSource("user.email").get()
        name = GitConfigSource("user.name").get()

        # Should get non-empty values from global git config
        assert email is not None and len(email) > 0
        assert name is not None and len(name) > 0


class TestInit:
    """E2E tests for djb init command."""

    def test_init_skips_all(
        self,
        runner,
        django_project: Path,
    ):
        """Test init with all skip flags."""
        env = {
            "DJB_PROJECT_DIR": str(django_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                [
                    "init",
                    "--skip-brew",
                    "--skip-python",
                    "--skip-frontend",
                    "--skip-db",
                    "--skip-secrets",
                    "--skip-hooks",
                ],
            )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        # Should show success message
        assert "initialization complete" in result.output.lower()

    def test_init_adds_djb_to_installed_apps(
        self,
        runner,
        django_project: Path,
    ):
        """Test that init adds djb to INSTALLED_APPS."""
        env = {
            "DJB_PROJECT_DIR": str(django_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                [
                    "init",
                    "--skip-brew",
                    "--skip-python",
                    "--skip-frontend",
                    "--skip-db",
                    "--skip-secrets",
                    "--skip-hooks",
                ],
            )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify djb was added to INSTALLED_APPS
        settings = django_project / "myproject" / "settings.py"
        content = settings.read_text()
        assert '"djb"' in content

    def test_init_updates_gitignore(
        self,
        runner,
        django_project: Path,
    ):
        """Test that init updates .gitignore."""
        env = {
            "DJB_PROJECT_DIR": str(django_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                [
                    "init",
                    "--skip-brew",
                    "--skip-python",
                    "--skip-frontend",
                    "--skip-db",
                    "--skip-secrets",
                    "--skip-hooks",
                ],
            )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify .gitignore was updated
        gitignore = django_project / ".gitignore"
        content = gitignore.read_text()
        assert ".djb/local.yaml" in content

    def test_init_fails_without_pyproject(
        self,
        runner,
        tmp_path: Path,
    ):
        """Test that init fails when pyproject.toml is missing."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        env = {
            "DJB_PROJECT_DIR": str(empty_dir),
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                [
                    "init",
                    "--skip-brew",
                    "--skip-python",
                    "--skip-frontend",
                    "--skip-db",
                    "--skip-secrets",
                    "--skip-hooks",
                ],
            )

        # Should fail with helpful error
        assert result.exit_code != 0
        assert "pyproject.toml" in result.output.lower()

    def test_init_with_mocked_brew(
        self,
        runner,
        django_project: Path,
    ):
        """Test init with mocked Homebrew commands."""
        env = {
            "DJB_PROJECT_DIR": str(django_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        # Mock check_cmd to pretend brew packages are installed
        def mock_check_cmd(cmd, *args, **kwargs):
            cmd_str = " ".join(cmd)
            if "brew" in cmd_str:
                return True  # All brew packages "installed"
            if "which" in cmd_str:
                return True  # All tools "available"
            return True

        with patch.dict(os.environ, env):
            with patch("djb.cli.init.check_cmd", side_effect=mock_check_cmd):
                result = runner.invoke(
                    djb_cli,
                    [
                        "init",
                        "--skip-python",
                        "--skip-frontend",
                        "--skip-db",
                        "--skip-secrets",
                        "--skip-hooks",
                    ],
                )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        # Should show that packages are already installed
        assert "already installed" in result.output.lower()

    def test_init_is_idempotent(
        self,
        runner,
        django_project: Path,
    ):
        """Test that running init twice is safe."""
        env = {
            "DJB_PROJECT_DIR": str(django_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            # First run
            result1 = runner.invoke(
                djb_cli,
                [
                    "init",
                    "--skip-brew",
                    "--skip-python",
                    "--skip-frontend",
                    "--skip-db",
                    "--skip-secrets",
                    "--skip-hooks",
                ],
            )
            assert result1.exit_code == 0, f"First run failed: {result1.output}"

            # Reset config state between runs
            reset_config()

            # Second run
            result2 = runner.invoke(
                djb_cli,
                [
                    "init",
                    "--skip-brew",
                    "--skip-python",
                    "--skip-frontend",
                    "--skip-db",
                    "--skip-secrets",
                    "--skip-hooks",
                ],
            )
            assert result2.exit_code == 0, f"Second run failed: {result2.output}"

        # Verify djb is still in INSTALLED_APPS (only once)
        settings = django_project / "myproject" / "settings.py"
        content = settings.read_text()
        # Should have "djb" only once
        assert content.count('"djb"') == 1 or content.count("'djb'") == 1

    def test_init_creates_config_files_in_fresh_project(
        self,
        runner,
        django_project: Path,
    ):
        """Test that init creates .djb/local.yaml and .djb/project.yaml in fresh project.

        When running djb init in a project that has never had djb initialized,
        it should create both config files with appropriate values.

        Note: We only set DJB_PROJECT_DIR to point to the test project.
        Name/email will be acquired from git config (set up in the fixture),
        which is a "derived" source, so they get saved to local.yaml.
        """
        # Ensure no .djb directory exists yet
        djb_dir = django_project / ".djb"
        assert not djb_dir.exists(), "Test requires fresh project without .djb directory"

        # Only set project dir - let name/email come from git config (derived source)
        env = {
            "DJB_PROJECT_DIR": str(django_project),
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                [
                    "init",
                    "--skip-brew",
                    "--skip-python",
                    "--skip-frontend",
                    "--skip-db",
                    "--skip-secrets",
                    "--skip-hooks",
                ],
            )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify .djb directory was created
        assert djb_dir.exists(), ".djb directory should be created"

        # Verify local.yaml was created with user settings (from git config)
        local_yaml = djb_dir / "local.yaml"
        assert local_yaml.exists(), ".djb/local.yaml should be created"
        local_content = local_yaml.read_text()
        assert "name:" in local_content or "email:" in local_content

        # Verify project.yaml was created with project settings
        project_yaml = djb_dir / "project.yaml"
        assert project_yaml.exists(), ".djb/project.yaml should be created"
        project_content = project_yaml.read_text()
        assert "project_name:" in project_content or "hostname:" in project_content
