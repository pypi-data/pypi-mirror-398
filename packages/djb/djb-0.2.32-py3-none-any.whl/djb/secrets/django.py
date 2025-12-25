"""
Django settings integration for djb secrets.

Provides a convenience function for loading secrets in Django settings.py
with automatic support for test overrides and environment detection.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Any

from djb.secrets.core import SopsError, load_secrets
from djb.secrets.gpg import GpgError
from djb.secrets.protected import ProtectedFileError


def load_secrets_for_django(
    base_dir: Path,
    *,
    warn_on_failure: bool = True,
) -> dict[str, Any]:
    """
    Load secrets for Django settings with automatic environment detection.

    This is a convenience wrapper for Django settings.py that:
    - Auto-detects environment (production on Heroku, else from ENVIRONMENT env var)
    - Respects TEST_SECRETS_DIR and TEST_AGE_KEY_PATH environment variables
    - Falls back to base_dir/secrets for the secrets directory
    - Handles failures gracefully (returns empty dict with optional warning)
    - Skips loading on Heroku where secrets come from environment variables

    Usage in settings.py:
        from djb.secrets import load_secrets_for_django
        BASE_DIR = Path(__file__).resolve().parent.parent
        _secrets = load_secrets_for_django(BASE_DIR)
        SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or _secrets.get("django_secret_key")

    Args:
        base_dir: Project base directory (typically Django's BASE_DIR)
        warn_on_failure: If True, emit warnings on failure (default True)

    Returns:
        Dictionary of decrypted secrets, or empty dict on failure/Heroku

    Environment variables:
        DYNO: If set, assumes Heroku and returns empty dict
        ENVIRONMENT: Secrets environment (dev, staging, production). Defaults to "dev"
        TEST_SECRETS_DIR: Override secrets directory (for pytest)
        TEST_AGE_KEY_PATH: Override age key path (for pytest)
    """
    # On Heroku, secrets come from environment variables
    is_heroku = "DYNO" in os.environ
    if is_heroku:
        return {}

    # Determine environment
    environment = "production" if is_heroku else os.environ.get("ENVIRONMENT", "dev")

    # Allow tests to provide their own secrets infrastructure
    secrets_dir = (
        Path(os.environ["TEST_SECRETS_DIR"])
        if "TEST_SECRETS_DIR" in os.environ
        else base_dir / "secrets"
    )
    key_path = Path(os.environ["TEST_AGE_KEY_PATH"]) if "TEST_AGE_KEY_PATH" in os.environ else None

    try:
        return load_secrets(
            environment=environment,
            secrets_dir=secrets_dir,
            key_path=key_path,
        )
    except (FileNotFoundError, SopsError, GpgError, ProtectedFileError) as e:
        if warn_on_failure:
            warnings.warn(f"Could not load secrets: {e}", stacklevel=2)
        return {}
