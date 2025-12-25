"""Type checking test utility.

This module provides a reusable test that runs pyright to verify
all project files pass type checking.

Usage in a host project:

    # In tests/test_types.py or similar:
    from djb.testing import test_typecheck

    # The test function is automatically discovered by pytest

Or to customize the project root:

    from djb.testing.typecheck import run_typecheck

    def test_types():
        run_typecheck("/path/to/project")
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from djb.config import find_pyproject_root


def run_typecheck(project_root: Path | str | None = None) -> None:
    """Run pyright type checker on the project.

    Args:
        project_root: Path to the project root. If None, will search
            for pyproject.toml starting from the current directory.

    Raises:
        AssertionError: If type checking fails with errors.
        FileNotFoundError: If pyright is not installed or project root not found.
    """
    if project_root is None:
        root = find_pyproject_root()
    else:
        root = Path(project_root)

    # Run pyright from the project root
    result = subprocess.run(
        ["pyright"],
        cwd=root,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        # Format error message with pyright output
        error_msg = f"Type checking failed with {result.returncode} error(s):\n\n"
        if result.stdout:
            error_msg += result.stdout
        if result.stderr:
            error_msg += f"\nstderr:\n{result.stderr}"
        raise AssertionError(error_msg)


def test_typecheck() -> None:
    """Pytest test that verifies all project files pass type checking.

    This test can be imported directly into a host project's test suite:

        from djb.testing import test_typecheck

    When pytest discovers this test, it will run pyright on the project
    and fail if there are any type errors.

    The project root is determined by searching upward from the current
    working directory for a pyproject.toml file.
    """
    run_typecheck()
