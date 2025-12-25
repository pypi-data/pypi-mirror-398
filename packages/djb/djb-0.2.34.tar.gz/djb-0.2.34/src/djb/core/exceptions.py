"""
djb exception hierarchy.

This module defines custom exceptions for djb, providing:
- Consistent error handling across the codebase
- Helpful error messages with actionable guidance
- Clear exception hierarchy for different failure domains

Exception Hierarchy:
    DjbError (base)
    ├── ImproperlyConfigured
    ├── SecretsError
    │   ├── SecretsKeyNotFound
    │   ├── SecretsDecryptionFailed
    │   └── SecretsFileNotFound
    └── DeploymentError
        ├── HerokuAuthError
        └── HerokuPushError

Usage:
    from djb.core.exceptions import SecretsKeyNotFound

    if not key_path.exists():
        raise SecretsKeyNotFound(key_path)
"""

from __future__ import annotations

from pathlib import Path


class DjbError(Exception):
    """Base class for all djb exceptions.

    All djb-specific exceptions inherit from this class, making it easy
    to catch any djb error with a single except clause.
    """


class ImproperlyConfigured(DjbError):
    """djb is improperly configured.

    Raised when djb cannot proceed due to invalid or missing configuration.
    This typically indicates a setup issue that the user needs to resolve.
    """


class ProjectNotFound(DjbError):
    """No djb project found.

    Raised when searching for a djb project root but no pyproject.toml
    with a djb dependency is found in the current directory or its parents.
    """

    def __init__(self):
        super().__init__(
            "Could not find a djb project.\n\n"
            "A djb project must have a pyproject.toml with 'djb' in dependencies.\n\n"
            "Make sure you are running this command from within a djb project directory,\n"
            "or set the DJB_PROJECT_DIR environment variable."
        )


# =============================================================================
# Secrets Exceptions
# =============================================================================


class SecretsError(DjbError):
    """Base class for secrets-related errors."""


class SecretsKeyNotFound(SecretsError):
    """Age encryption key file not found.

    Raised when attempting to decrypt secrets but the age key file
    is missing. This usually means secrets have not been initialized.
    """

    def __init__(self, key_path: Path | str):
        self.key_path = Path(key_path)
        super().__init__(
            f"Age key file not found at {self.key_path}\n\n"
            f"To fix this, run:\n"
            f"  djb init\n\n"
            f"This will generate a new age key and initialize secrets management."
        )


class SecretsDecryptionFailed(SecretsError):
    """Failed to decrypt a secret value.

    Raised when decryption fails, typically because the wrong key
    was used or the encrypted data is corrupted.
    """

    def __init__(self, environment: str, detail: str | None = None):
        self.environment = environment
        msg = f"Failed to decrypt secrets for '{environment}'"
        if detail:
            msg = f"{msg}: {detail}"
        msg = (
            f"{msg}\n\n"
            f"This usually means:\n"
            f"  1. You're using the wrong age key\n"
            f"  2. The secrets file is corrupted\n"
            f"  3. The secrets were encrypted for different recipients\n\n"
            f"Check that .age/keys.txt contains the correct private key."
        )
        super().__init__(msg)


class SecretsFileNotFound(SecretsError):
    """Secrets file for environment not found.

    Raised when the encrypted secrets file for a specific environment
    does not exist.
    """

    def __init__(self, environment: str, secrets_dir: Path | str):
        self.environment = environment
        self.secrets_dir = Path(secrets_dir)
        self.expected_path = self.secrets_dir / f"{environment}.yaml"
        super().__init__(
            f"Secrets file not found: {self.expected_path}\n\n"
            f"Available environments can be listed with:\n"
            f"  djb secrets list\n\n"
            f"To create secrets for '{environment}', run:\n"
            f"  djb init"
        )


# =============================================================================
# Deployment Exceptions
# =============================================================================


class DeploymentError(DjbError):
    """Base class for deployment-related errors."""


class HerokuAuthError(DeploymentError):
    """Not authenticated with Heroku.

    Raised when attempting to deploy but the user is not logged
    into the Heroku CLI.
    """

    def __init__(self):
        super().__init__(
            "Not logged into Heroku.\n\n"
            "To fix this, run:\n"
            "  heroku login\n\n"
            "Then retry your deployment command."
        )


class HerokuPushError(DeploymentError):
    """Failed to push to Heroku.

    Raised when git push to Heroku fails, with details about
    what went wrong.
    """

    def __init__(self, app: str, detail: str | None = None):
        self.app = app
        msg = f"Failed to push to Heroku app '{app}'"
        if detail:
            msg = f"{msg}:\n{detail}"
        msg = (
            f"{msg}\n\n"
            f"Common causes:\n"
            f"  1. No heroku remote configured (run: heroku git:remote -a {app})\n"
            f"  2. Build failed on Heroku (check: heroku logs --tail --app {app})\n"
            f"  3. Git branch doesn't exist or has conflicts"
        )
        super().__init__(msg)
