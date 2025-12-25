"""
Stash/restore editable djb configuration.

Provides a clean way to temporarily remove editable djb configuration for
operations that need to push/commit clean files (like deploy and publish),
then restore the editable state afterward.

Uses `djb editable-djb` commands under the hood, which delegate pyproject.toml
manipulation to uv.
"""

from __future__ import annotations

import subprocess
from contextlib import contextmanager
from pathlib import Path

import click

from djb.core.logging import get_logger
from djb.cli.editable import (
    install_editable_djb,
    is_djb_editable,
    uninstall_editable_djb,
)

logger = get_logger(__name__)


def bust_uv_cache() -> None:
    """Clear uv's cache for djb to ensure fresh resolution."""
    subprocess.run(
        ["uv", "cache", "clean", "djb"],
        capture_output=True,
        text=True,
    )


def regenerate_uv_lock(repo_root: Path, quiet: bool = False) -> bool:
    """Regenerate uv.lock with the current pyproject.toml.

    Returns True on success, False on failure.
    If quiet=False (default), prints stderr on failure to help diagnose issues.
    """
    result = subprocess.run(
        ["uv", "lock", "--refresh"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 and not quiet:
        if result.stderr:
            logger.fail(f"uv lock error: {result.stderr.strip()}")
        if result.stdout:
            logger.info(f"uv lock output: {result.stdout.strip()}")
    return result.returncode == 0


@contextmanager
def stashed_editable(repo_root: Path, quiet: bool = False):
    """Context manager to temporarily remove editable djb configuration.

    Uses `djb editable-djb --uninstall` to remove and `djb editable-djb` to
    restore.

    Usage:
        with stashed_editable(repo_root) as was_editable:
            # pyproject.toml no longer has editable config
            # do git operations here
            pass
        # editable config is restored

    Yields:
        bool: True if djb was in editable mode before stashing, False otherwise.

    If an exception occurs, the original state is still restored.
    """
    was_editable = is_djb_editable(repo_root)

    if was_editable:
        if not quiet:
            logger.info("Temporarily removing editable djb configuration...")
        uninstall_editable_djb(repo_root, quiet=True)

    try:
        yield was_editable
    finally:
        if was_editable:
            if not quiet:
                logger.info("Restoring editable djb configuration...")
            install_editable_djb(repo_root, quiet=True)


def restore_editable(repo_root: Path, quiet: bool = False) -> bool:
    """Re-enable editable mode for local development.

    Used by publish after committing the version bump. This installs djb
    in editable mode using `uv add --editable`, which handles all the
    TOML manipulation correctly.

    Args:
        repo_root: Path to the project root
        quiet: If True, suppress output messages

    Returns:
        True on success, False on failure
    """
    return install_editable_djb(repo_root, quiet=quiet)
