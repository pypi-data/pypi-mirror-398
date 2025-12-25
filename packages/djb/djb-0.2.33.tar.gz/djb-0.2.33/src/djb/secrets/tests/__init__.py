"""
djb.secrets.tests - Test utilities for djb secrets tests.

Factory fixtures:
    mock_subprocess_result - Factory for creating subprocess.run mock results.
                             Usage: mock_subprocess_result(returncode=0, stdout="out")

    make_age_key - Factory for creating age key files in .age directory.
                   Usage: make_age_key() -> creates .age/keys.txt
                          make_age_key(protected=True) -> creates .age/keys.txt.gpg
"""

from __future__ import annotations

__all__: list[str] = []
