"""Tests for djb publish module."""

from __future__ import annotations

import os
from unittest.mock import Mock, patch

import click
import pytest

from djb.cli.djb import djb_cli
from djb.cli.editable import find_djb_dir
from djb.cli.publish import (
    PUBLISH_WORKFLOW_TEMPLATE,
    _find_dependency_string,
    bump_version,
    ensure_publish_workflow,
    find_version_file,
    get_current_branch,
    get_package_info,
    get_version,
    is_dependency_of,
    set_version,
    update_parent_dependency,
    wait_for_uv_resolvable,
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


class TestGetPackageInfo:
    """Tests for get_package_info function - covers all error paths."""

    def test_returns_name_and_version(self, tmp_path):
        """Test returns tuple of (name, version) on success."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "djb"\nversion = "0.2.5"')

        name, version = get_package_info(tmp_path)

        assert name == "djb"
        assert version == "0.2.5"

    def test_handles_hyphenated_name(self, tmp_path):
        """Test handles package names with hyphens."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "django-model-changes"\nversion = "1.0.0"'
        )

        name, version = get_package_info(tmp_path)

        assert name == "django-model-changes"
        assert version == "1.0.0"

    def test_error_missing_pyproject(self, tmp_path):
        """Test raises ClickException when pyproject.toml is missing."""
        with pytest.raises(click.ClickException) as exc_info:
            get_package_info(tmp_path)

        assert "pyproject.toml" in str(exc_info.value.message)

    def test_error_missing_project_name(self, tmp_path):
        """Test raises ClickException when project.name is missing."""
        (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.2.5"')

        with pytest.raises(click.ClickException) as exc_info:
            get_package_info(tmp_path)

        assert "name" in str(exc_info.value.message).lower()

    def test_error_missing_project_version(self, tmp_path):
        """Test raises ClickException when project.version is missing."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "djb"')

        with pytest.raises(click.ClickException) as exc_info:
            get_package_info(tmp_path)

        assert "version" in str(exc_info.value.message).lower()

    def test_error_missing_project_section(self, tmp_path):
        """Test raises ClickException when [project] section is missing."""
        (tmp_path / "pyproject.toml").write_text('[tool.other]\nkey = "value"')

        with pytest.raises(click.ClickException) as exc_info:
            get_package_info(tmp_path)

        assert "name" in str(exc_info.value.message).lower()

    def test_error_invalid_toml(self, tmp_path):
        """Test raises ClickException for invalid TOML syntax."""
        (tmp_path / "pyproject.toml").write_text("invalid toml [ syntax")

        with pytest.raises(click.ClickException) as exc_info:
            get_package_info(tmp_path)

        assert "Invalid TOML" in str(exc_info.value.message)


class TestFindVersionFile:
    """Tests for find_version_file function - covers src and flat layouts."""

    def test_finds_src_layout(self, tmp_path):
        """Test finds _version.py in src layout."""
        # Create src layout structure
        version_dir = tmp_path / "src" / "djb"
        version_dir.mkdir(parents=True)
        version_file = version_dir / "_version.py"
        version_file.write_text('__version__ = "0.2.5"')

        result = find_version_file(tmp_path, "djb")

        assert result == version_file

    def test_finds_flat_layout(self, tmp_path):
        """Test finds _version.py in flat layout."""
        # Create flat layout structure
        version_dir = tmp_path / "djb"
        version_dir.mkdir()
        version_file = version_dir / "_version.py"
        version_file.write_text('__version__ = "0.2.5"')

        result = find_version_file(tmp_path, "djb")

        assert result == version_file

    def test_prefers_src_layout_over_flat(self, tmp_path):
        """Test prefers src layout when both exist."""
        # Create both layouts
        src_version_dir = tmp_path / "src" / "djb"
        src_version_dir.mkdir(parents=True)
        src_version_file = src_version_dir / "_version.py"
        src_version_file.write_text('__version__ = "src"')

        flat_version_dir = tmp_path / "djb"
        flat_version_dir.mkdir()
        flat_version_file = flat_version_dir / "_version.py"
        flat_version_file.write_text('__version__ = "flat"')

        result = find_version_file(tmp_path, "djb")

        assert result == src_version_file

    def test_returns_none_when_not_found(self, tmp_path):
        """Test returns None when _version.py doesn't exist."""
        result = find_version_file(tmp_path, "djb")

        assert result is None

    def test_handles_hyphenated_package_name(self, tmp_path):
        """Test converts hyphens to underscores for directory lookup."""
        # Create src layout with underscored directory
        version_dir = tmp_path / "src" / "django_model_changes"
        version_dir.mkdir(parents=True)
        version_file = version_dir / "_version.py"
        version_file.write_text('__version__ = "1.0.0"')

        result = find_version_file(tmp_path, "django-model-changes")

        assert result == version_file


class TestGetCurrentBranch:
    """Tests for get_current_branch function - covers git command and fallback."""

    def test_returns_branch_name(self, tmp_path):
        """Test returns branch name from git command."""
        with patch("djb.cli.publish.run_cmd") as mock_run:
            mock_run.return_value = Mock(stdout="feature-branch\n")

            result = get_current_branch(tmp_path)

        assert result == "feature-branch"
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        assert call_args[1]["cwd"] == tmp_path
        assert call_args[1]["halt_on_fail"] is False

    def test_falls_back_to_main_on_empty_output(self, tmp_path):
        """Test falls back to 'main' when git returns empty output."""
        with patch("djb.cli.publish.run_cmd") as mock_run:
            # Detached HEAD or empty output scenario
            mock_run.return_value = Mock(stdout="")

            result = get_current_branch(tmp_path)

        assert result == "main"

    def test_falls_back_to_main_on_whitespace_only(self, tmp_path):
        """Test falls back to 'main' when git returns only whitespace."""
        with patch("djb.cli.publish.run_cmd") as mock_run:
            mock_run.return_value = Mock(stdout="   \n")

            result = get_current_branch(tmp_path)

        assert result == "main"

    def test_strips_whitespace_from_branch_name(self, tmp_path):
        """Test strips leading/trailing whitespace from branch name."""
        with patch("djb.cli.publish.run_cmd") as mock_run:
            mock_run.return_value = Mock(stdout="  main  \n")

            result = get_current_branch(tmp_path)

        assert result == "main"


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

    @pytest.mark.parametrize(
        "old_dep,expected_new",
        [
            # Various version specifiers
            ("djb==0.2.4", "djb>=0.2.5"),
            ("djb~=0.2.4", "djb>=0.2.5"),
            ("djb<1.0", "djb>=0.2.5"),
            ("djb<=0.2.4", "djb>=0.2.5"),
            ("djb>0.2.3", "djb>=0.2.5"),
            ("djb!=0.2.3", "djb>=0.2.5"),
            # Compound version specifiers
            ("djb>=0.2.4,<1.0", "djb>=0.2.5"),
            # Extras syntax
            ("djb[dev]>=0.2.4", "djb[dev]>=0.2.5"),
            ("djb[dev,test]>=0.2.4", "djb[dev,test]>=0.2.5"),
            # Dependency without version constraint
            ("djb", "djb>=0.2.5"),
            # No specifier with extras
            ("djb[dev]", "djb[dev]>=0.2.5"),
        ],
    )
    def test_handles_various_specifiers(self, tmp_path, old_dep, expected_new):
        """Test handles all PEP 508 version specifiers, extras, and markers."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            f"""
[project]
name = "myproject"
dependencies = [
    "{old_dep}",
]
"""
        )

        result = update_parent_dependency(tmp_path, "djb", "0.2.5")

        assert result is True
        content = pyproject.read_text()
        assert f'"{expected_new}"' in content
        assert f'"{old_dep}"' not in content

    def test_handles_environment_markers(self, tmp_path):
        """Test handles dependencies with PEP 508 environment markers."""
        pyproject = tmp_path / "pyproject.toml"
        # Use single quotes for TOML string since marker contains double quotes
        pyproject.write_text(
            """
[project]
name = "myproject"
dependencies = [
    'djb>=0.2.4; python_version >= "3.10"',
]
"""
        )

        result = update_parent_dependency(tmp_path, "djb", "0.2.5")

        assert result is True
        content = pyproject.read_text()
        assert "'djb>=0.2.5; python_version >= " in content
        assert "'djb>=0.2.4; python_version >= " not in content

    def test_handles_extras_with_markers(self, tmp_path):
        """Test handles dependencies with extras and environment markers."""
        pyproject = tmp_path / "pyproject.toml"
        # Use single quotes for TOML string since marker contains double quotes
        pyproject.write_text(
            """
[project]
name = "myproject"
dependencies = [
    'djb[dev]>=0.2.4; sys_platform == "linux"',
]
"""
        )

        result = update_parent_dependency(tmp_path, "djb", "0.2.5")

        assert result is True
        content = pyproject.read_text()
        assert "'djb[dev]>=0.2.5; sys_platform == " in content
        assert "'djb[dev]>=0.2.4; sys_platform == " not in content

    def test_returns_false_when_package_not_found(self, tmp_path):
        """Test returns False when package is not a dependency."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"
dependencies = [
    "django>=4.0",
]
"""
        )

        result = update_parent_dependency(tmp_path, "djb", "0.2.5")
        assert result is False

    def test_handles_optional_dependencies(self, tmp_path):
        """Test updates package in optional dependencies."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"
dependencies = []

[project.optional-dependencies]
dev = [
    "djb>=0.2.4",
]
"""
        )

        result = update_parent_dependency(tmp_path, "djb", "0.2.5")

        assert result is True
        content = pyproject.read_text()
        assert '"djb>=0.2.5"' in content
        assert '"djb>=0.2.4"' not in content

    def test_preserves_formatting_and_comments(self, tmp_path):
        """Test preserves file formatting including comments."""
        pyproject = tmp_path / "pyproject.toml"
        original = """
[project]
name = "myproject"
# Important dependencies
dependencies = [
    "django>=4.0",  # Web framework
    "djb>=0.2.4",   # Deployment tool
    "requests>=2.0",
]
"""
        pyproject.write_text(original)

        result = update_parent_dependency(tmp_path, "djb", "0.2.5")

        assert result is True
        content = pyproject.read_text()
        assert '"djb>=0.2.5"' in content
        assert "# Important dependencies" in content
        assert "# Web framework" in content
        assert "# Deployment tool" in content
        assert '"django>=4.0"' in content
        assert '"requests>=2.0"' in content

    def test_single_quotes(self, tmp_path):
        """Test handles single-quoted dependencies."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"
dependencies = [
    'djb>=0.2.4',
]
"""
        )

        result = update_parent_dependency(tmp_path, "djb", "0.2.5")

        assert result is True
        content = pyproject.read_text()
        assert "'djb>=0.2.5'" in content
        assert "'djb>=0.2.4'" not in content

    def test_does_not_match_prefix_package(self, tmp_path):
        """Test does not match djb-extras when looking for djb."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "myproject"
dependencies = [
    "djb-extras>=0.2.4",
]
"""
        )

        result = update_parent_dependency(tmp_path, "djb", "0.2.5")
        assert result is False

        content = pyproject.read_text()
        assert '"djb-extras>=0.2.4"' in content

    def test_returns_false_for_invalid_toml(self, tmp_path):
        """Test returns False for invalid TOML syntax."""
        pyproject = tmp_path / "pyproject.toml"
        original_content = "invalid toml [ syntax"
        pyproject.write_text(original_content)

        result = update_parent_dependency(tmp_path, "djb", "0.2.5")

        assert result is False
        # Verify file wasn't modified
        assert pyproject.read_text() == original_content


class TestFindDependencyString:
    """Tests for _find_dependency_string function.

    This function uses TOML parsing and packaging.requirements.Requirement
    to find a dependency string. These direct tests cover edge cases not
    observable through update_parent_dependency() since both return
    None/False for error cases with no distinction.
    """

    def test_finds_simple_dependency(self, tmp_path):
        """Test finds basic dependency string."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = ["djb>=0.2.4"]\n')

        result = _find_dependency_string("djb", pyproject)

        assert result == "djb>=0.2.4"

    def test_finds_dependency_with_extras(self, tmp_path):
        """Test finds dependency with extras syntax."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = ["djb[dev,test]>=0.2.4"]\n')

        result = _find_dependency_string("djb", pyproject)

        assert result == "djb[dev,test]>=0.2.4"

    def test_finds_dependency_with_markers(self, tmp_path):
        """Test finds dependency with environment markers."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """[project]
dependencies = ['djb>=0.2.4; python_version >= "3.10"']
"""
        )

        result = _find_dependency_string("djb", pyproject)

        assert result == 'djb>=0.2.4; python_version >= "3.10"'

    def test_finds_dependency_in_optional_dependencies(self, tmp_path):
        """Test finds dependency in optional-dependencies section."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """[project]
dependencies = []

[project.optional-dependencies]
dev = ["djb>=0.2.4"]
"""
        )

        result = _find_dependency_string("djb", pyproject)

        assert result == "djb>=0.2.4"

    def test_returns_none_when_not_found(self, tmp_path):
        """Test returns None when package not in dependencies."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = ["django>=4.0"]\n')

        result = _find_dependency_string("djb", pyproject)

        assert result is None

    def test_returns_none_for_toml_parse_error(self, tmp_path):
        """Test returns None for invalid TOML syntax."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("invalid toml [ syntax")

        result = _find_dependency_string("djb", pyproject)

        assert result is None

    def test_returns_none_when_project_section_missing(self, tmp_path):
        """Test returns None when [project] section is missing."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.other]\nkey = "value"\n')

        result = _find_dependency_string("djb", pyproject)

        assert result is None

    def test_skips_malformed_deps_finds_valid(self, tmp_path):
        """Test skips malformed dependency strings but finds valid ones.

        This edge case is only testable with direct tests because
        update_parent_dependency() doesn't expose which deps were skipped.
        """
        pyproject = tmp_path / "pyproject.toml"
        # Include malformed deps that will fail Requirement() parsing
        pyproject.write_text(
            """[project]
dependencies = [
    "not a valid @ dependency string!!",
    "djb>=0.2.4",
    "another invalid >>>>> thing",
]
"""
        )

        result = _find_dependency_string("djb", pyproject)

        assert result == "djb>=0.2.4"

    def test_handles_non_list_dependencies(self, tmp_path):
        """Test handles non-list dependencies value gracefully."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = "not-a-list"\n')

        result = _find_dependency_string("djb", pyproject)

        assert result is None

    def test_handles_non_list_optional_dependencies(self, tmp_path):
        """Test handles non-list optional-dependencies value gracefully."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """[project]
dependencies = []

[project.optional-dependencies]
dev = "not-a-list"
"""
        )

        result = _find_dependency_string("djb", pyproject)

        assert result is None

    def test_package_name_case_sensitive(self, tmp_path):
        """Test package name matching is case-sensitive.

        Note: The current implementation uses exact string comparison
        with Requirement.name, which preserves the original case from
        the dependency string. PEP 503 normalization (lowercasing) is
        NOT applied, so searches must match the case used in pyproject.toml.
        """
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = ["Django>=4.0"]\n')

        # Matching case finds the dependency
        result = _find_dependency_string("Django", pyproject)
        assert result == "Django>=4.0"

        # Non-matching case does not find it
        result = _find_dependency_string("django", pyproject)
        assert result is None

    def test_does_not_match_prefix_package(self, tmp_path):
        """Test does not match djb-extras when looking for djb."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = ["djb-extras>=0.1"]\n')

        result = _find_dependency_string("djb", pyproject)

        assert result is None

    def test_multiple_optional_dependency_groups(self, tmp_path):
        """Test searches across multiple optional-dependencies groups."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """[project]
dependencies = ["requests>=2.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0"]
deploy = ["djb>=0.2.4"]
"""
        )

        result = _find_dependency_string("djb", pyproject)

        assert result == "djb>=0.2.4"


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


class TestIsDependencyOf:
    """Tests for is_dependency_of function."""

    @pytest.mark.parametrize(
        "content,package,expected",
        [
            # Basic dependency with version constraint
            ('[project]\ndependencies = ["djb>=0.2.4"]\n', "djb", True),
            ('[project]\ndependencies = ["djb>=0.2.4"]\n', "other", False),
            # Dependency with multiple constraints
            ('[project]\ndependencies = ["djb>=0.2.4,<1.0"]\n', "djb", True),
            # Dependency without version constraint
            ('[project]\ndependencies = ["djb"]\n', "djb", True),
            # Single quotes
            ("[project]\ndependencies = ['djb>=0.2.4']\n", "djb", True),
            # Package with hyphen
            (
                '[project]\ndependencies = ["django-model-changes>=0.5"]\n',
                "django-model-changes",
                True,
            ),
            # Package with underscore
            ('[project]\ndependencies = ["my_package>=1.0"]\n', "my_package", True),
            # Empty dependencies
            ("[project]\ndependencies = []\n", "djb", False),
            # Optional dependencies
            ('[project.optional-dependencies]\ndev = ["djb>=0.2"]\n', "djb", True),
            # Multiple dependencies
            (
                '[project]\ndependencies = ["other>=1.0", "djb>=0.2.4", "another>=2.0"]\n',
                "djb",
                True,
            ),
            # Prefix package names should NOT match (fixed false positive)
            ('[project]\ndependencies = ["djb-extras>=0.1"]\n', "djb", False),
            ('[project]\ndependencies = ["djb_extras>=0.1"]\n', "djb", False),
            ('[project]\ndependencies = ["djb123>=0.1"]\n', "djb", False),
            # Similar prefix in different package (should NOT match)
            ('[project]\ndependencies = ["django>=4.0"]\n', "djan", False),
            # Package with extras syntax
            ('[project]\ndependencies = ["djb[dev]>=0.1"]\n', "djb", True),
            # Package with environment marker
            ('[project]\ndependencies = ["djb ; python_version >= \\"3.8\\""]\n', "djb", True),
        ],
    )
    def test_is_dependency_of(self, tmp_path, content, package, expected):
        """Test is_dependency_of with various pyproject.toml content."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(content)

        result = is_dependency_of(package, tmp_path)
        assert result is expected

    def test_returns_false_when_no_pyproject(self, tmp_path):
        """Test returns False when pyproject.toml doesn't exist."""
        result = is_dependency_of("djb", tmp_path)
        assert result is False

    def test_returns_false_for_toml_parse_error(self, tmp_path):
        """Test returns False for invalid TOML syntax."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("invalid toml [ syntax")

        result = is_dependency_of("djb", tmp_path)

        assert result is False


class TestEnsurePublishWorkflow:
    """Tests for ensure_publish_workflow function."""

    def test_creates_workflow_when_not_exists(self, tmp_path):
        """Test creates workflow file when it doesn't exist."""
        result = ensure_publish_workflow(tmp_path)

        assert result is True
        workflow_file = tmp_path / ".github" / "workflows" / "publish.yaml"
        assert workflow_file.exists()
        content = workflow_file.read_text()
        assert content == PUBLISH_WORKFLOW_TEMPLATE

    def test_returns_false_when_exists(self, tmp_path):
        """Test returns False when workflow file already exists."""
        # Create existing workflow
        workflow_dir = tmp_path / ".github" / "workflows"
        workflow_dir.mkdir(parents=True)
        workflow_file = workflow_dir / "publish.yaml"
        workflow_file.write_text("existing content")

        result = ensure_publish_workflow(tmp_path)

        assert result is False
        # Content should be unchanged
        assert workflow_file.read_text() == "existing content"

    def test_is_idempotent(self, tmp_path):
        """Test calling multiple times has same result."""
        # First call creates
        result1 = ensure_publish_workflow(tmp_path)
        workflow_file = tmp_path / ".github" / "workflows" / "publish.yaml"
        content1 = workflow_file.read_text()

        # Second call doesn't modify
        result2 = ensure_publish_workflow(tmp_path)
        content2 = workflow_file.read_text()

        assert result1 is True
        assert result2 is False
        assert content1 == content2

    def test_creates_parent_directories(self, tmp_path):
        """Test creates .github/workflows directories if needed."""
        assert not (tmp_path / ".github").exists()

        ensure_publish_workflow(tmp_path)

        assert (tmp_path / ".github").is_dir()
        assert (tmp_path / ".github" / "workflows").is_dir()

    def test_workflow_contains_expected_content(self, tmp_path):
        """Test workflow file has expected GitHub Actions content."""
        ensure_publish_workflow(tmp_path)

        workflow_file = tmp_path / ".github" / "workflows" / "publish.yaml"
        content = workflow_file.read_text()

        # Check key sections are present
        assert "name: Publish to PyPI" in content
        assert "on:\n  push:\n    tags:" in content
        assert "v*.*.*" in content
        assert "permissions:" in content
        assert "id-token: write" in content
        assert "environment: pypi" in content
        assert "pypa/gh-action-pypi-publish" in content


class TestWaitForUvResolvable:
    """Tests for wait_for_uv_resolvable function."""

    def test_returns_true_on_immediate_success(self, tmp_path):
        """Test returns True when first lock attempt succeeds."""
        with (
            patch("djb.cli.publish.bust_uv_cache") as mock_bust,
            patch("djb.cli.publish.regenerate_uv_lock", return_value=True) as mock_lock,
            patch("djb.cli.publish.time.sleep") as mock_sleep,
        ):
            result = wait_for_uv_resolvable(tmp_path, "1.0.0")

        assert result is True
        mock_bust.assert_called_once()
        mock_lock.assert_called_once_with(tmp_path, quiet=True)
        mock_sleep.assert_not_called()

    def test_retries_until_success(self, tmp_path):
        """Test retries with exponential backoff until success."""
        with (
            patch("djb.cli.publish.bust_uv_cache") as mock_bust,
            patch("djb.cli.publish.regenerate_uv_lock") as mock_lock,
            patch("djb.cli.publish.time.sleep") as mock_sleep,
            patch("djb.cli.publish.time.time") as mock_time,
        ):
            # First two attempts fail, third succeeds
            mock_lock.side_effect = [False, False, True]
            # Start at 0, then 1, then 2 (still under timeout of 300)
            mock_time.side_effect = [0, 1, 2, 3]

            result = wait_for_uv_resolvable(tmp_path, "1.0.0", timeout=300)

        assert result is True
        assert mock_bust.call_count == 3
        assert mock_lock.call_count == 3
        # Should have slept twice (after first and second failures)
        assert mock_sleep.call_count == 2
        # Check exponential backoff: first sleep is initial_interval (5), second is doubled (10)
        mock_sleep.assert_any_call(5)
        mock_sleep.assert_any_call(10)

    def test_returns_false_on_timeout(self, tmp_path):
        """Test returns False when timeout is reached."""
        with (
            patch("djb.cli.publish.bust_uv_cache"),
            patch("djb.cli.publish.regenerate_uv_lock", return_value=False) as mock_lock,
            patch("djb.cli.publish.time.sleep"),
            patch("djb.cli.publish.time.time") as mock_time,
        ):
            # Time progresses past timeout
            mock_time.side_effect = [0, 0, 301]  # start, first check, second check (past timeout)

            result = wait_for_uv_resolvable(tmp_path, "1.0.0", timeout=300)

        assert result is False
        assert mock_lock.call_count == 1  # Only one attempt before timeout

    def test_uses_custom_timeout(self, tmp_path):
        """Test uses custom timeout value."""
        with (
            patch("djb.cli.publish.bust_uv_cache"),
            patch("djb.cli.publish.regenerate_uv_lock", return_value=False),
            patch("djb.cli.publish.time.sleep"),
            patch("djb.cli.publish.time.time") as mock_time,
        ):
            # With custom timeout of 60, time=61 should exceed it
            mock_time.side_effect = [0, 0, 61]

            result = wait_for_uv_resolvable(tmp_path, "1.0.0", timeout=60)

        assert result is False

    def test_exponential_backoff_caps_at_max_interval(self, tmp_path):
        """Test exponential backoff respects max_interval."""
        with (
            patch("djb.cli.publish.bust_uv_cache"),
            patch("djb.cli.publish.regenerate_uv_lock") as mock_lock,
            patch("djb.cli.publish.time.sleep") as mock_sleep,
            patch("djb.cli.publish.time.time") as mock_time,
        ):
            # Many failures then success
            mock_lock.side_effect = [False, False, False, False, False, True]
            # Time progresses slowly to allow many retries
            mock_time.side_effect = [0, 1, 2, 3, 4, 5, 6]

            result = wait_for_uv_resolvable(
                tmp_path, "1.0.0", initial_interval=5, max_interval=15, timeout=300
            )

        assert result is True
        # Sleep intervals: 5, 10, 15, 15, 15 (capped at 15)
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [5, 10, 15, 15, 15]

    def test_custom_initial_interval(self, tmp_path):
        """Test uses custom initial_interval value."""
        with (
            patch("djb.cli.publish.bust_uv_cache"),
            patch("djb.cli.publish.regenerate_uv_lock") as mock_lock,
            patch("djb.cli.publish.time.sleep") as mock_sleep,
            patch("djb.cli.publish.time.time") as mock_time,
        ):
            mock_lock.side_effect = [False, True]
            mock_time.side_effect = [0, 1, 2]

            result = wait_for_uv_resolvable(tmp_path, "1.0.0", initial_interval=10)

        assert result is True
        mock_sleep.assert_called_once_with(10)
