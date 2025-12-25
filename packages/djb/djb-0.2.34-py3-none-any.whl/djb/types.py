"""
djb types - Core type definitions for djb configuration.

Provides enums for mode and target that are used throughout the djb CLI
and can be synced to deployment environments.
"""

from __future__ import annotations

from enum import Enum
from typing import Union

__all__ = ["Mode", "NestedDict", "Target"]

# Recursive type for nested dictionaries with primitive values
# Note: Union is required here because recursive type aliases with | and forward refs
# don't work at runtime (TypeError: unsupported operand type(s) for |: 'type' and 'str')
NestedDict = dict[str, Union[str, int, float, bool, None, "NestedDict"]]


class Mode(str, Enum):
    """Deployment mode for djb projects.

    Modes control behavior and which secrets are loaded:
    - development: Local development (default)
    - staging: Staging/test environment
    - production: Production deployment
    """

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

    def __str__(self) -> str:
        return self.value

    @property
    def secrets_env(self) -> str:
        """Get the secrets environment name for this mode.

        Maps mode to secrets file name (without .yaml extension):
        - development → dev
        - staging → staging
        - production → production
        """
        if self == Mode.DEVELOPMENT:
            return "dev"
        return self.value

    @classmethod
    def parse(cls, value: str | None, default: Mode | None = None) -> Mode | None:
        """Parse a string to Mode, returning default on failure.

        Args:
            value: String to parse (case-insensitive)
            default: Value to return if parsing fails

        Returns:
            Parsed Mode or default value
        """
        if value is None or not isinstance(value, str):
            return default
        try:
            return cls(value.lower())
        except ValueError:
            return default


class Target(str, Enum):
    """Deployment target platform.

    Targets control where and how the application is deployed:
    - heroku: Deploy to Heroku (default)
    - docker: Build Docker image (future)
    - k8s: Deploy to Kubernetes (future)
    """

    HEROKU = "heroku"
    # Future targets:
    # DOCKER = "docker"
    # K8S = "k8s"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def parse(cls, value: str | None, default: Target | None = None) -> Target | None:
        """Parse a string to Target, returning default on failure.

        Args:
            value: String to parse (case-insensitive)
            default: Value to return if parsing fails

        Returns:
            Parsed Target or default value
        """
        if value is None or not isinstance(value, str):
            return default
        try:
            return cls(value.lower())
        except ValueError:
            return default
