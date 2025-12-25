"""Type checking test for djb.

This test verifies that all djb source files pass pyright type checking.
"""

from __future__ import annotations

from pathlib import Path

from djb.testing.typecheck import run_typecheck


def test_typecheck() -> None:
    """Verify djb source files pass type checking.

    Explicitly sets the project root to djb's directory to ensure
    we only check djb's files, not the host project's files.
    """
    # Find djb's root by going up from this file
    djb_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    run_typecheck(djb_root)
