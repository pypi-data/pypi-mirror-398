"""
ProjectDirField - Field for the project root directory.

Also provides project detection utilities:
- find_project_root: Find the djb project root directory
- find_pyproject_root: Find nearest pyproject.toml
- _is_djb_project: Check if a directory is a djb project
"""

from __future__ import annotations

import os
import re
import tomllib
from collections.abc import Callable
from pathlib import Path

from djb.config.field import ConfigFieldABC
from djb.config.resolution import ConfigSource, ResolutionContext
from djb.core.exceptions import ProjectNotFound

# Environment variable name for project directory
PROJECT_DIR_ENV_KEY = "DJB_PROJECT_DIR"


def find_pyproject_root(
    start_path: Path | None = None,
    *,
    predicate: Callable[[Path], bool] | None = None,
) -> Path:
    """Find the nearest directory containing pyproject.toml that matches predicate.

    Walks up from start_path (or cwd) looking for pyproject.toml files.
    If a predicate is provided, the directory must also satisfy the predicate.

    Args:
        start_path: Starting directory for search. Defaults to current working directory.
        predicate: Optional function to test each candidate directory.
                   If provided, directory must satisfy predicate(path) == True.
                   If None, just checks for pyproject.toml existence.

    Returns:
        Path to the directory containing pyproject.toml (that matches predicate).

    Raises:
        FileNotFoundError: If no matching pyproject.toml is found.
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    while current != current.parent:
        if (current / "pyproject.toml").exists():
            if predicate is None or predicate(current):
                return current
        current = current.parent

    raise FileNotFoundError(f"Could not find pyproject.toml starting from {start_path}")


def _is_djb_project(path: Path) -> bool:
    """Check if a directory is a djb project (has pyproject.toml with djb dependency)."""
    pyproject_path = path / "pyproject.toml"

    if not pyproject_path.is_file():
        return False

    try:
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
    except tomllib.TOMLDecodeError:
        return False

    # Check for djb in dependencies
    # Match "djb" followed by version specifier, extras bracket, whitespace, or end
    # Excludes packages like "djb-tools" or "djb_something"
    if (
        "project" in pyproject
        and "dependencies" in pyproject["project"]
        and isinstance(pyproject["project"]["dependencies"], list)
    ):
        for dep in pyproject["project"]["dependencies"]:
            if re.match(r"^djb(?:[<>=!~\[\s]|$)", dep):
                return True

    return False


def find_project_root(
    project_root: Path | None = None,
    start_path: Path | None = None,
    *,
    fallback_to_cwd: bool = False,
) -> tuple[Path, ConfigSource]:
    """Find the project root directory.

    Called before config files are loaded to determine where to load them from.
    All project_dir discovery logic lives here.

    Priority:
    1. Explicit project_root (trusted when provided) -> CLI
    2. DJB_PROJECT_DIR environment variable (trusted when set) -> ENV
    3. Search for djb project in parent directories -> PYPROJECT
    4. Fall back to cwd (if fallback_to_cwd=True) -> CWD_PATH

    Args:
        project_root: Explicit project root to use. If provided, returned directly.
        start_path: Starting directory for search. Defaults to cwd.
        fallback_to_cwd: If True, return cwd when no project is found.

    Returns:
        Tuple of (path, source) where source indicates how the path was found.

    Raises:
        ProjectNotFound: If no djb project is found and fallback_to_cwd is False.
    """
    # 1. Explicit project_root takes precedence
    if project_root is not None:
        return (project_root, ConfigSource.CLI)

    # 2. Check environment variable - trust it when set
    env_project_dir = os.getenv(PROJECT_DIR_ENV_KEY)
    if env_project_dir:
        return (Path(env_project_dir), ConfigSource.ENV)

    # 3. Search for djb project in parent directories
    try:
        return (find_pyproject_root(start_path, predicate=_is_djb_project), ConfigSource.PYPROJECT)
    except FileNotFoundError:
        if fallback_to_cwd:
            return (Path.cwd(), ConfigSource.CWD_PATH)
        raise ProjectNotFound()


class ProjectDirField(ConfigFieldABC):
    """Field for project_dir - the root directory of the project.

    Resolution order:
    1. Config layers (cli > env > local > project)
    2. From project_root in context with its tracked source
    """

    def resolve(self, ctx: ResolutionContext) -> tuple[Path, ConfigSource]:
        """Resolve project_dir from config layers or context."""
        # 1. Config layers (cli > env > local > project)
        raw, source = ctx.configs.get("project_dir", PROJECT_DIR_ENV_KEY)
        if raw is not None and source is not None:
            return (Path(raw), source)

        # 2. Use project_root with its tracked source (PYPROJECT, CWD_PATH, etc.)
        return (ctx.project_root, ctx.project_root_source)
