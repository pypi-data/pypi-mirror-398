"""Shared test fixtures for djb.cli.utils tests."""

from __future__ import annotations

from djb.testing.fixtures import pty_stdin

# Re-export shared fixtures so they're available to tests in this package
__all__ = ["pty_stdin"]
