"""End-to-end tests for djb publish CLI command.

Commands tested:
- djb publish

Run with: pytest --run-e2e
"""

from __future__ import annotations

from pathlib import Path

import pytest

from djb.cli.publish import bump_version, get_version, set_version


# Mark all tests in this module as e2e (skipped by default, use --run-e2e to include)
pytestmark = pytest.mark.e2e_skipped_by_default


@pytest.fixture
def djb_project(tmp_path: Path) -> Path:
    """Create a minimal djb package structure for publish tests."""
    project_dir = tmp_path / "djb"
    project_dir.mkdir()

    # Create pyproject.toml for djb (without [tool.djb] section)
    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text(
        """\
[project]
name = "djb"
version = "0.2.0"
dependencies = ["click>=8.0"]
"""
    )

    # Create src/djb/_version.py (djb-specific structure)
    src_dir = project_dir / "src" / "djb"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text("")
    (src_dir / "_version.py").write_text('__version__ = "0.2.0"\n')

    return project_dir


class TestVersionFunctions:
    """E2E tests for version management functions."""

    def test_get_version(self, djb_project: Path):
        """Test reading version from pyproject.toml."""
        version = get_version(djb_project)
        assert version == "0.2.0"

    def test_set_version(self, djb_project: Path):
        """Test setting version in pyproject.toml and _version.py."""
        set_version(djb_project, "djb", "0.3.0")

        # Verify pyproject.toml updated
        pyproject = djb_project / "pyproject.toml"
        assert 'version = "0.3.0"' in pyproject.read_text()

        # Verify _version.py updated
        version_file = djb_project / "src" / "djb" / "_version.py"
        assert '__version__ = "0.3.0"' in version_file.read_text()

    def test_bump_version_patch(self):
        """Test bumping patch version."""
        new_version = bump_version("1.2.3", "patch")
        assert new_version == "1.2.4"

    def test_bump_version_minor(self):
        """Test bumping minor version resets patch."""
        new_version = bump_version("1.2.3", "minor")
        assert new_version == "1.3.0"

    def test_bump_version_major(self):
        """Test bumping major version resets minor and patch."""
        new_version = bump_version("1.2.3", "major")
        assert new_version == "2.0.0"
