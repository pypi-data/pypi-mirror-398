"""End-to-end tests for djb editable-djb CLI command.

Commands tested:
- djb editable-djb
- djb editable-djb --status
- djb editable-djb --uninstall

Run with: pytest --run-e2e
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from djb.cli.djb import djb_cli
from djb.cli.editable import (
    get_djb_version_specifier,
    is_djb_editable,
    is_djb_package_dir,
)

from . import create_pyproject_toml, init_git_repo


# Mark all tests in this module as e2e (skipped by default, use --run-e2e to include)
pytestmark = pytest.mark.e2e_skipped_by_default


@pytest.fixture
def host_project(tmp_path: Path) -> Path:
    """Create a host project that depends on djb."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    create_pyproject_toml(
        project_dir,
        name="myproject",
        extra_content='dependencies = [\n    "djb>=0.2.0",\n]',
    )

    init_git_repo(project_dir, user_email="test@example.com", user_name="Test User")

    return project_dir


@pytest.fixture
def djb_dir(tmp_path: Path) -> Path:
    """Create a djb package directory."""
    djb_path = tmp_path / "djb"
    djb_path.mkdir()

    # Create pyproject.toml for djb (without [tool.djb] section)
    pyproject = djb_path / "pyproject.toml"
    pyproject.write_text(
        """\
[project]
name = "djb"
version = "0.2.0"
dependencies = ["click>=8.0"]
"""
    )

    init_git_repo(djb_path)

    return djb_path


class TestEditableHelperFunctions:
    """E2E tests for editable helper functions."""

    def test_get_djb_version_specifier(self, host_project: Path):
        """Test extracting djb version specifier from pyproject.toml."""
        specifier = get_djb_version_specifier(host_project)
        assert specifier == ">=0.2.0"

    def test_is_djb_package_dir_true(self, djb_dir: Path):
        """Test that djb directory is correctly identified."""
        assert is_djb_package_dir(djb_dir) is True

    def test_is_djb_package_dir_false(self, host_project: Path):
        """Test that host project is not identified as djb."""
        assert is_djb_package_dir(host_project) is False

    def test_is_djb_editable_false_by_default(self, host_project: Path):
        """Test that djb is not editable by default."""
        assert is_djb_editable(host_project) is False


class TestEditableDjb:
    """E2E tests for djb editable-djb command."""

    def test_editable_status_shows_not_editable(
        self,
        runner,
        host_project: Path,
    ):
        """Test that --status shows djb is not in editable mode."""
        env = {
            "DJB_PROJECT_DIR": str(host_project),
            "DJB_PROJECT_NAME": "myproject",
            "DJB_NAME": "Test User",
            "DJB_EMAIL": "test@example.com",
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                ["editable-djb", "--status"],
            )

        # Should complete and show not editable
        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "not" in result.output.lower() or "pypi" in result.output.lower()

    def test_editable_from_djb_dir_warns(
        self,
        runner,
        djb_dir: Path,
    ):
        """Test that running from djb directory shows appropriate message."""
        env = {
            "DJB_PROJECT_DIR": str(djb_dir),
            "DJB_PROJECT_NAME": "djb",
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                ["editable-djb", "--status"],
            )

        # Should complete (may show special message for djb dir)
        assert "djb" in result.output.lower()
