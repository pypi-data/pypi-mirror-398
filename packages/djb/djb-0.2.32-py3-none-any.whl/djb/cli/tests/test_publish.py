"""Tests for djb publish module."""

from __future__ import annotations

import os
from unittest.mock import Mock, patch

import click
import pytest

from djb.cli.djb import djb_cli
from djb.cli.editable import find_djb_dir
from djb.cli.publish import (
    bump_version,
    get_version,
    set_version,
    update_parent_dependency,
)
from djb.core.exceptions import ProjectNotFound
from djb.config import find_project_root

from . import DJB_PYPROJECT_CONTENT, make_editable_pyproject


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run to avoid actual command execution."""
    with patch("djb.cli.publish.subprocess.run") as mock:
        mock.return_value = Mock(returncode=0, stdout="", stderr="")
        yield mock


class TestFindDjbDirRaiseOnMissing:
    """Tests for find_djb_dir with raise_on_missing=True."""

    def test_finds_djb_in_cwd(self, tmp_path):
        """Test finding djb when in djb directory."""
        (tmp_path / "pyproject.toml").write_text(DJB_PYPROJECT_CONTENT)

        with patch("djb.cli.editable.Path.cwd", return_value=tmp_path):
            result = find_djb_dir(raise_on_missing=True)
            assert result == tmp_path

    def test_finds_djb_in_subdirectory(self, tmp_path, djb_project):
        """Test finding djb/ subdirectory."""
        with patch("djb.cli.editable.Path.cwd", return_value=tmp_path):
            result = find_djb_dir(raise_on_missing=True)
            assert result == djb_project

    def test_raises_when_not_found(self, tmp_path):
        """Test raises ClickException when djb not found."""
        with patch("djb.cli.editable.Path.cwd", return_value=tmp_path):
            with pytest.raises(click.ClickException):
                find_djb_dir(raise_on_missing=True)


class TestGetVersion:
    """Tests for get_version function."""

    def test_gets_version(self, tmp_path):
        """Test getting version from pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "djb"\nversion = "0.2.5"')

        result = get_version(tmp_path)
        assert result == "0.2.5"

    def test_raises_when_version_not_found(self, tmp_path):
        """Test raises when version not in pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "djb"')

        with pytest.raises(click.ClickException):
            get_version(tmp_path)


class TestSetVersion:
    """Tests for set_version function."""

    def test_sets_version(self, tmp_path):
        """Test setting version in pyproject.toml and _version.py."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "djb"\nversion = "0.2.5"')

        # Create the src/djb directory structure
        version_dir = tmp_path / "src" / "djb"
        version_dir.mkdir(parents=True)
        version_file = version_dir / "_version.py"
        version_file.write_text('__version__ = "0.2.5"')

        set_version(tmp_path, "djb", "0.3.0")

        # Check pyproject.toml
        content = pyproject.read_text()
        assert 'version = "0.3.0"' in content
        assert 'version = "0.2.5"' not in content

        # Check _version.py
        version_content = version_file.read_text()
        assert '__version__ = "0.3.0"' in version_content
        assert '__version__ = "0.2.5"' not in version_content


class TestBumpVersion:
    """Tests for bump_version function."""

    def test_bump_patch(self):
        """Test bumping patch version."""
        assert bump_version("0.2.5", "patch") == "0.2.6"

    def test_bump_minor(self):
        """Test bumping minor version resets patch."""
        assert bump_version("0.2.5", "minor") == "0.3.0"

    def test_bump_major(self):
        """Test bumping major version resets minor and patch."""
        assert bump_version("0.2.5", "major") == "1.0.0"

    def test_invalid_version_format(self):
        """Test raises for invalid version format."""
        with pytest.raises(click.ClickException):
            bump_version("invalid", "patch")

    def test_unknown_part(self):
        """Test raises for unknown version part."""
        with pytest.raises(click.ClickException):
            bump_version("0.2.5", "unknown")


class TestFindParentProject:
    """Tests for finding parent project using find_project_root."""

    def test_finds_parent_with_djb_dependency(self, tmp_path, djb_project):
        """Test finding parent project with djb dependency."""
        parent_pyproject = tmp_path / "pyproject.toml"
        parent_pyproject.write_text(
            '[project]\nname = "myproject"\ndependencies = ["djb>=0.2.5"]\n'
        )

        path, _source = find_project_root(start_path=djb_project.parent)
        assert path == tmp_path

    def test_raises_when_no_parent(self, djb_project):
        """Test raises ProjectNotFound when no parent project."""
        # Clear DJB_PROJECT_DIR to test actual search behavior
        with patch.dict(os.environ, {"DJB_PROJECT_DIR": ""}, clear=False):
            with pytest.raises(ProjectNotFound):
                find_project_root(start_path=djb_project.parent)

    def test_raises_when_parent_without_djb(self, tmp_path, djb_project):
        """Test raises ProjectNotFound when parent doesn't depend on djb."""
        parent_pyproject = tmp_path / "pyproject.toml"
        parent_pyproject.write_text(
            '[project]\nname = "myproject"\ndependencies = ["other-package>=1.0"]\n'
        )

        # Clear DJB_PROJECT_DIR to test actual search behavior
        with patch.dict(os.environ, {"DJB_PROJECT_DIR": ""}, clear=False):
            with pytest.raises(ProjectNotFound):
                find_project_root(start_path=djb_project.parent)


class TestUpdateParentDependency:
    """Tests for update_parent_dependency function."""

    def test_updates_version(self, tmp_path):
        """Test updates djb version in dependencies."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"
dependencies = [
    "djb>=0.2.4",
]
"""
        )

        result = update_parent_dependency(tmp_path, "djb", "0.2.5")

        assert result is True
        content = pyproject.read_text()
        assert '"djb>=0.2.5"' in content
        assert '"djb>=0.2.4"' not in content

    def test_returns_false_when_no_change(self, tmp_path):
        """Test returns False when version already correct."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"
dependencies = [
    "djb>=0.2.5",
]
"""
        )

        result = update_parent_dependency(tmp_path, "djb", "0.2.5")
        assert result is False


class TestPublishCommand:
    """Tests for publish CLI command."""

    @pytest.fixture
    def djb_project_v024(self, tmp_path):
        """Create djb project with version 0.2.4 for publish tests."""
        djb_dir = tmp_path / "djb"
        djb_dir.mkdir()
        (djb_dir / "pyproject.toml").write_text('[project]\nname = "djb"\nversion = "0.2.4"\n')
        return djb_dir

    def test_help(self, runner):
        """Test that publish --help works."""
        result = runner.invoke(djb_cli, ["publish", "--help"])
        assert result.exit_code == 0
        assert "Bump version and publish a Python package to PyPI" in result.output
        assert "--major" in result.output
        assert "--minor" in result.output
        assert "--patch" in result.output
        assert "--dry-run" in result.output

    def test_dry_run_basic(self, runner, tmp_path, djb_project_v024):
        """Test dry-run shows planned actions."""
        with patch("djb.cli.publish.Path.cwd", return_value=tmp_path):
            result = runner.invoke(djb_cli, ["publish", "--dry-run"])

        assert result.exit_code == 0
        assert "[dry-run]" in result.output
        assert "0.2.5" in result.output
        assert "v0.2.5" in result.output

    def test_dry_run_with_editable_parent(self, runner, tmp_path, djb_project_v024):
        """Test dry-run shows editable handling steps."""
        parent_pyproject = tmp_path / "pyproject.toml"
        parent_pyproject.write_text(
            '[project]\nname = "myproject"\ndependencies = ["djb>=0.2.4"]\n\n'
            + make_editable_pyproject("djb").split("\n\n", 1)[
                1
            ]  # Get just the [tool.uv.sources] part
        )

        with patch("djb.cli.publish.Path.cwd", return_value=tmp_path):
            result = runner.invoke(djb_cli, ["publish", "--dry-run"])

        assert result.exit_code == 0
        assert "editable" in result.output.lower()
        assert "Stash editable djb configuration" in result.output
        assert "Re-enable editable djb with current version" in result.output

    def test_dry_run_minor_bump(self, runner, tmp_path, djb_project_v024):
        """Test dry-run with --minor flag."""
        with patch("djb.cli.publish.Path.cwd", return_value=tmp_path):
            result = runner.invoke(djb_cli, ["publish", "--minor", "--dry-run"])

        assert result.exit_code == 0
        assert "0.3.0" in result.output

    def test_dry_run_major_bump(self, runner, tmp_path, djb_project_v024):
        """Test dry-run with --major flag."""
        with patch("djb.cli.publish.Path.cwd", return_value=tmp_path):
            result = runner.invoke(djb_cli, ["publish", "--major", "--dry-run"])

        assert result.exit_code == 0
        assert "1.0.0" in result.output
