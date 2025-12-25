"""Tests for project detection utilities."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from djb.config.fields.project_dir import (
    _is_djb_project,
    find_project_root,
    find_pyproject_root,
)
from djb.config.resolution import ConfigSource
from djb.core.exceptions import ProjectNotFound


class TestFindPyprojectRoot:
    """Tests for find_pyproject_root function."""

    def test_finds_pyproject_in_current_dir(self, tmp_path):
        """Test finding pyproject.toml in current directory."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\n')

        result = find_pyproject_root(tmp_path)
        assert result == tmp_path

    def test_finds_pyproject_in_parent(self, tmp_path):
        """Test finding pyproject.toml from a subdirectory."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\n')

        subdir = tmp_path / "src" / "app"
        subdir.mkdir(parents=True)

        result = find_pyproject_root(subdir)
        assert result == tmp_path

    def test_raises_when_not_found(self, tmp_path):
        """Test FileNotFoundError when no pyproject.toml exists."""
        subdir = tmp_path / "not_a_project"
        subdir.mkdir()

        with pytest.raises(FileNotFoundError):
            find_pyproject_root(subdir)

    def test_predicate_filters_results(self, tmp_path):
        """Test predicate filters which pyproject.toml is returned."""
        # Create outer project without djb
        outer = tmp_path / "pyproject.toml"
        outer.write_text('[project]\nname = "outer"\ndependencies = ["django"]\n')

        # Create inner djb project
        inner_dir = tmp_path / "inner"
        inner_dir.mkdir()
        inner = inner_dir / "pyproject.toml"
        inner.write_text('[project]\nname = "inner"\ndependencies = ["djb"]\n')

        # Without predicate, finds outer (closer to root)
        result = find_pyproject_root(inner_dir)
        assert result == inner_dir

        # With predicate, starting from inner finds inner (which has djb)
        result = find_pyproject_root(inner_dir, predicate=_is_djb_project)
        assert result == inner_dir

    def test_predicate_skips_non_matching(self, tmp_path):
        """Test predicate skips pyproject.toml that don't match."""
        # Create outer djb project
        outer = tmp_path / "pyproject.toml"
        outer.write_text('[project]\nname = "outer"\ndependencies = ["djb"]\n')

        # Create inner non-djb project
        inner_dir = tmp_path / "inner"
        inner_dir.mkdir()
        inner = inner_dir / "pyproject.toml"
        inner.write_text('[project]\nname = "inner"\ndependencies = ["django"]\n')

        # With predicate, skips inner (no djb) and finds outer
        result = find_pyproject_root(inner_dir, predicate=_is_djb_project)
        assert result == tmp_path

    def test_predicate_raises_when_no_match(self, tmp_path):
        """Test raises FileNotFoundError when predicate never matches."""
        # Create pyproject.toml without djb
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\ndependencies = ["django"]\n')

        with pytest.raises(FileNotFoundError):
            find_pyproject_root(tmp_path, predicate=_is_djb_project)


class TestIsDjbProject:
    """Tests for _is_djb_project helper."""

    def test_detects_djb_dependency(self, tmp_path):
        """Test detection of djb in dependencies."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\ndependencies = ["django", "djb"]\n')

        assert _is_djb_project(tmp_path) is True

    def test_detects_djb_with_version(self, tmp_path):
        """Test detection of djb with version specifier."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\ndependencies = ["djb>=0.1.0"]\n')

        assert _is_djb_project(tmp_path) is True

    def test_rejects_no_pyproject(self, tmp_path):
        """Test rejection when pyproject.toml doesn't exist."""
        assert _is_djb_project(tmp_path) is False

    def test_rejects_no_djb_dependency(self, tmp_path):
        """Test rejection when djb is not in dependencies."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\ndependencies = ["django"]\n')

        assert _is_djb_project(tmp_path) is False

    def test_rejects_no_dependencies(self, tmp_path):
        """Test rejection when there are no dependencies."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\n')

        assert _is_djb_project(tmp_path) is False

    def test_rejects_no_project_section(self, tmp_path):
        """Test rejection when there's no project section."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.black]\n")

        assert _is_djb_project(tmp_path) is False

    def test_rejects_invalid_toml(self, tmp_path):
        """Test rejection of invalid TOML."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("this is not valid toml [[[")

        assert _is_djb_project(tmp_path) is False

    def test_rejects_djb_hyphen_package(self, tmp_path):
        """Test that djb-something does NOT match (different package)."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\ndependencies = ["djb-tools"]\n')

        # djb-tools is a different package, not djb
        assert _is_djb_project(tmp_path) is False

    def test_rejects_djb_in_optional_dependencies(self, tmp_path):
        """Test that djb in optional-dependencies does NOT match.

        djb should be a required runtime dependency, not optional.
        Only project.dependencies is checked, not optional-dependencies.
        """
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            "[project]\n"
            'name = "myproject"\n'
            'dependencies = ["django"]\n'
            "\n"
            "[project.optional-dependencies]\n"
            'dev = ["djb", "pytest"]\n'
        )

        # djb in optional-dependencies should NOT count as a djb project
        assert _is_djb_project(tmp_path) is False


class TestFindProjectRoot:
    """Tests for find_project_root function."""

    def test_finds_project_in_current_dir(self, tmp_path):
        """Test finding project when in root directory."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\ndependencies = ["djb"]\n')

        path, source = find_project_root(start_path=tmp_path)
        assert path == tmp_path
        assert source == ConfigSource.PYPROJECT

    def test_finds_project_in_parent(self, tmp_path):
        """Test finding project from a subdirectory."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\ndependencies = ["djb"]\n')

        subdir = tmp_path / "src" / "app"
        subdir.mkdir(parents=True)

        path, source = find_project_root(start_path=subdir)
        assert path == tmp_path
        assert source == ConfigSource.PYPROJECT

    def test_uses_env_variable(self, tmp_path):
        """Test DJB_PROJECT_DIR environment variable."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\ndependencies = ["djb"]\n')

        with patch.dict(os.environ, {"DJB_PROJECT_DIR": str(tmp_path)}):
            # Start from somewhere else - env var takes precedence
            path, source = find_project_root(start_path=Path("/"))
            assert path == tmp_path
            assert source == ConfigSource.ENV

    def test_env_variable_trusted_even_without_pyproject(self, tmp_path):
        """Test that DJB_PROJECT_DIR is trusted even without valid djb project.

        This supports bootstrapping, testing, and running outside a project.
        """
        # No pyproject.toml in tmp_path
        with patch.dict(os.environ, {"DJB_PROJECT_DIR": str(tmp_path)}):
            path, source = find_project_root(start_path=tmp_path)
            assert path == tmp_path
            assert source == ConfigSource.ENV

    def test_explicit_project_root_wins(self, tmp_path):
        """Test that explicit project_root bypasses search."""
        explicit_path = tmp_path / "explicit"
        explicit_path.mkdir()

        path, source = find_project_root(project_root=explicit_path)
        assert path == explicit_path
        assert source == ConfigSource.CLI

    def test_raises_project_not_found(self, tmp_path):
        """Test ProjectNotFound when no project exists."""
        # Create a directory with no pyproject.toml
        subdir = tmp_path / "not_a_project"
        subdir.mkdir()

        with pytest.raises(ProjectNotFound):
            find_project_root(start_path=subdir)

    def test_project_not_found_message(self, tmp_path):
        """Test ProjectNotFound has helpful message."""
        subdir = tmp_path / "not_a_project"
        subdir.mkdir()

        with pytest.raises(ProjectNotFound) as exc_info:
            find_project_root(start_path=subdir)

        assert "djb project" in str(exc_info.value)
        assert "pyproject.toml" in str(exc_info.value)


class TestFindProjectRootFallback:
    """Tests for find_project_root with fallback_to_cwd=True."""

    def test_returns_project_root_when_found(self, tmp_path, monkeypatch):
        """Test returns project root when in a djb project."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\ndependencies = ["djb"]\n')

        # Change to the project directory
        monkeypatch.chdir(tmp_path)

        path, source = find_project_root(fallback_to_cwd=True)
        assert path == tmp_path
        assert source == ConfigSource.PYPROJECT

    def test_returns_cwd_when_not_found(self, tmp_path, monkeypatch):
        """Test returns cwd when not in a djb project."""
        # tmp_path has no pyproject.toml
        monkeypatch.chdir(tmp_path)

        path, source = find_project_root(fallback_to_cwd=True)
        assert path == tmp_path
        assert source == ConfigSource.CWD_PATH

    def test_never_raises(self, tmp_path, monkeypatch):
        """Test function never raises ProjectNotFound."""
        monkeypatch.chdir(tmp_path)

        # Should not raise, should return cwd with CWD_PATH source
        path, source = find_project_root(fallback_to_cwd=True)
        assert path is not None
        assert source == ConfigSource.CWD_PATH
