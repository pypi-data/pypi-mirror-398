"""
Shared test fixtures for djb tests.

This module provides reusable pytest fixtures that can be imported by both
CLI unit tests and E2E tests to avoid duplication.

Fixtures:
    pty_stdin - Creates a PTY and temporarily replaces stdin for interactive input testing
    make_age_key - Factory for creating age key pairs
    alice_key - Pre-made age key pair for Alice
    bob_key - Pre-made age key pair for Bob

Usage:
    Import the fixtures you need in your conftest.py:

        from djb.testing.fixtures import pty_stdin, make_age_key, alice_key, bob_key

    Or import all fixtures:

        from djb.testing.fixtures import *
"""

from __future__ import annotations

import os
import pty
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from djb.secrets import generate_age_key


@pytest.fixture
def pty_stdin():
    """Fixture that creates a PTY and temporarily replaces stdin.

    This fixture properly saves and restores stdin state between tests,
    avoiding pollution that can occur with manual save/restore.

    Yields the master fd which can be written to simulate user input.

    Example:
        def test_interactive_input(pty_stdin):
            os.write(pty_stdin, b"yes\\n")
            # ... code that reads from stdin
    """
    # Create PTY pair
    master_fd, slave_fd = pty.openpty()

    # Save original stdin state
    original_stdin_fd = os.dup(0)

    # Replace stdin with slave end of PTY
    os.dup2(slave_fd, 0)
    os.close(slave_fd)  # Close original fd since we dup2ed it
    sys.stdin = os.fdopen(0, "r", closefd=False)

    yield master_fd

    # Restore original stdin
    # First, close the current sys.stdin without closing fd 0
    sys.stdin.close()
    # Restore fd 0 to original
    os.dup2(original_stdin_fd, 0)
    os.close(original_stdin_fd)
    # Recreate sys.stdin from restored fd 0
    sys.stdin = os.fdopen(0, "r", closefd=False)
    # Close master end
    os.close(master_fd)


@pytest.fixture
def make_age_key(tmp_path: Path) -> Callable[[str], tuple[Path, str]]:
    """Factory fixture to create age key pairs.

    Creates age keys in a structured directory under tmp_path/.age/{name}/keys.txt.
    Each call with a different name creates a separate key pair.

    Returns a factory function that takes a name and returns (key_path, public_key).

    Example:
        def test_with_keys(make_age_key):
            alice_key_path, alice_public_key = make_age_key("alice")
            bob_key_path, bob_public_key = make_age_key("bob")
    """

    def _make_key(name: str) -> tuple[Path, str]:
        key_dir = tmp_path / ".age" / name
        key_dir.mkdir(parents=True, exist_ok=True)
        key_path = key_dir / "keys.txt"
        public_key, _ = generate_age_key(key_path)
        return key_path, public_key

    return _make_key


@pytest.fixture
def alice_key(make_age_key: Callable[[str], tuple[Path, str]]) -> tuple[Path, str]:
    """Create Alice's age key pair.

    Returns (key_path, public_key) tuple for Alice.
    Useful for tests that need a pre-made key without calling make_age_key directly.

    Example:
        def test_encryption(alice_key):
            key_path, public_key = alice_key
            # ... use key for encryption
    """
    return make_age_key("alice")


@pytest.fixture
def bob_key(make_age_key: Callable[[str], tuple[Path, str]]) -> tuple[Path, str]:
    """Create Bob's age key pair.

    Returns (key_path, public_key) tuple for Bob.
    Useful for tests that need two different keys (e.g., testing key rotation).

    Example:
        def test_rotation(alice_key, bob_key):
            alice_path, alice_public = alice_key
            bob_path, bob_public = bob_key
            # ... test key rotation
    """
    return make_age_key("bob")


__all__ = [
    "pty_stdin",
    "make_age_key",
    "alice_key",
    "bob_key",
]
