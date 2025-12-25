"""
djb.testing - Reusable testing utilities for djb-based projects.

Usage in your conftest.py:
    from djb.testing import (
        pytest_addoption,
        pytest_configure,
        pytest_collection_modifyitems,
        alice_key,
        bob_key,
    )

    # Re-export pytest hooks (required for pytest to find them)
    __all__ = ["pytest_addoption", "pytest_configure", "pytest_collection_modifyitems"]

    # Use fixtures in tests
    def test_encryption(alice_key, bob_key):
        assert alice_key.public != bob_key.public

Pytest Secrets Plugin:
    Register in pytest.ini to automatically set up test secrets:
        [pytest]
        addopts = -p djb.testing.pytest_secrets
        DJANGO_SETTINGS_MODULE = myproject.settings

    Or use the functions directly for custom setup:
        from djb.testing import setup_test_secrets, cleanup_test_secrets

Exports:
    test_typecheck - Importable test function for running pyright
    pytest_addoption - Add --run-e2e and --only-e2e options
    pytest_configure - Register e2e marker
    pytest_collection_modifyitems - Skip e2e tests by default
    setup_test_secrets - Create isolated test secrets (for custom plugins)
    cleanup_test_secrets - Clean up test secrets directory
    TestSecretsPaths - NamedTuple returned by setup_test_secrets

Shared Fixtures (import in your conftest.py):
    pty_stdin - Creates a PTY and temporarily replaces stdin
    make_age_key - Factory for creating age key pairs
    alice_key - Pre-made age key pair for Alice
    bob_key - Pre-made age key pair for Bob
"""

from __future__ import annotations

from djb.testing.fixtures import (
    alice_key,
    bob_key,
    make_age_key,
    pty_stdin,
)
from djb.testing.pytest_e2e import (
    pytest_addoption,
    pytest_collection_modifyitems,
    pytest_configure,
)
from djb.testing.pytest_secrets import (
    TestSecretsPaths,
    cleanup_test_secrets,
    setup_test_secrets,
)
from djb.testing.typecheck import test_typecheck

__all__ = [
    # Type checking
    "test_typecheck",
    # Pytest E2E hooks
    "pytest_addoption",
    "pytest_collection_modifyitems",
    "pytest_configure",
    # Test secrets setup
    "TestSecretsPaths",
    "cleanup_test_secrets",
    "setup_test_secrets",
    # Shared fixtures
    "pty_stdin",
    "make_age_key",
    "alice_key",
    "bob_key",
]
