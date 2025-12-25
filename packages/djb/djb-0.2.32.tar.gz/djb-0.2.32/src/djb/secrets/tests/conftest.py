"""
Shared test fixtures for djb secrets tests.

Auto-enabled fixtures:
    clean_config - Resets djb config before and after each test

Factory Fixtures:
    mock_subprocess_result - Factory for creating subprocess.run mock results
        Creates MagicMock with returncode, stdout, stderr attributes.
        Usage: mock_subprocess_result(returncode=0, stdout="output", stderr="")

    make_age_key - Factory for creating age key files in .age directory
        Creates plaintext or GPG-protected key files for testing.
        Usage: make_age_key() -> creates .age/keys.txt
               make_age_key(protected=True) -> creates .age/keys.txt.gpg
               make_age_key(content="custom") -> custom key content
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from djb import reset_config

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.fixture(autouse=True)
def clean_config() -> Generator[None, None, None]:
    """Reset djb config before and after each test.

    This fixture ensures each test gets a fresh config state.
    """
    reset_config()
    try:
        yield
    finally:
        reset_config()


@pytest.fixture
def mock_subprocess_result() -> Callable[..., MagicMock]:
    """Factory for creating subprocess.run mock results.

    Returns a factory function that creates MagicMock objects with:
    - returncode: int (default 0)
    - stdout: str (default "")
    - stderr: str (default "")

    Usage:
        def test_something(mock_subprocess_result):
            mock = mock_subprocess_result(returncode=0, stdout="output")
            with patch("subprocess.run", return_value=mock):
                ...

        # For failure cases:
            mock = mock_subprocess_result(returncode=1, stderr="error message")
    """

    def _create(
        returncode: int = 0,
        stdout: str = "",
        stderr: str = "",
    ) -> MagicMock:
        result = MagicMock()
        result.returncode = returncode
        result.stdout = stdout
        result.stderr = stderr
        return result

    return _create


@pytest.fixture
def make_age_key(tmp_path: Path) -> Callable[..., Path]:
    """Factory for creating age key files in .age directory.

    Returns a factory function that creates age key files with the given content.

    Args:
        content: Key content (default: "AGE-SECRET-KEY-...")
        protected: If True, create .gpg file instead of plaintext (default: False)
        gpg_content: Content for .gpg file when protected=True (default: "encrypted")

    Returns:
        Path to the created key file (keys.txt or keys.txt.gpg)

    Usage:
        def test_something(make_age_key):
            # Create plaintext key
            key_path = make_age_key()
            # Creates .age/keys.txt with "AGE-SECRET-KEY-..."

            # Create with custom content
            key_path = make_age_key(content="AGE-SECRET-KEY-CUSTOM...")

            # Create protected (GPG-encrypted) key
            gpg_path = make_age_key(protected=True)
            # Creates .age/keys.txt.gpg with "encrypted"
    """
    age_dir = tmp_path / ".age"

    def _create(
        content: str = "AGE-SECRET-KEY-...",
        protected: bool = False,
        gpg_content: str = "encrypted",
    ) -> Path:
        age_dir.mkdir(exist_ok=True)

        if protected:
            gpg_file = age_dir / "keys.txt.gpg"
            gpg_file.write_text(gpg_content)
            return gpg_file
        else:
            key_file = age_dir / "keys.txt"
            key_file.write_text(content)
            return key_file

    return _create
