"""
djb.core - Core utilities and exception hierarchy.

Example:
    from djb.core import DjbError, SecretsError, get_logger

    logger = get_logger(__name__)

    try:
        secrets = load_secrets("production")
    except SecretsError as e:
        logger.error(f"Secrets error: {e}")
    except DjbError as e:
        logger.error(f"djb error: {e}")

Logging:
    setup_logging - Initialize the djb logging system
    get_logger - Get a logger instance for a module
    Level - Enum of log levels (DEBUG, INFO, etc.)
    DjbLogger - Logger class for output formatting

Exception hierarchy:
    DjbError (base)
    ├── ImproperlyConfigured - Invalid configuration
    ├── ProjectNotFound - Project directory not found
    ├── SecretsError - Secrets-related errors
    │   ├── SecretsKeyNotFound - Age key file missing
    │   ├── SecretsDecryptionFailed - Decryption failed
    │   └── SecretsFileNotFound - Secrets file missing
    └── DeploymentError - Deployment-related errors
        ├── HerokuAuthError - Heroku authentication failed
        └── HerokuPushError - Heroku push failed
"""

from __future__ import annotations

from djb.core.exceptions import (
    DeploymentError,
    DjbError,
    HerokuAuthError,
    HerokuPushError,
    ImproperlyConfigured,
    ProjectNotFound,
    SecretsDecryptionFailed,
    SecretsError,
    SecretsFileNotFound,
    SecretsKeyNotFound,
)
from djb.core.logging import DjbLogger, Level, get_logger, setup_logging

__all__ = [
    # Logging
    "DjbLogger",
    "Level",
    "get_logger",
    "setup_logging",
    # Base exceptions
    "DjbError",
    "ImproperlyConfigured",
    "ProjectNotFound",
    # Secrets exceptions
    "SecretsDecryptionFailed",
    "SecretsError",
    "SecretsFileNotFound",
    "SecretsKeyNotFound",
    # Deployment exceptions
    "DeploymentError",
    "HerokuAuthError",
    "HerokuPushError",
]
