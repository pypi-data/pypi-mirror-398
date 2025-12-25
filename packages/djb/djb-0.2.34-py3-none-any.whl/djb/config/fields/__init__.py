"""
Specialized config field subclasses.

Re-exports all field classes for convenient importing.
"""

from djb.config.fields.email import EmailField
from djb.config.fields.enum import EnumField
from djb.config.fields.hostname import HostnameField
from djb.config.fields.log_level import DEFAULT_LOG_LEVEL, VALID_LOG_LEVELS, LogLevelField
from djb.config.fields.name import NameField
from djb.config.fields.project_dir import (
    PROJECT_DIR_ENV_KEY,
    ProjectDirField,
    _is_djb_project,
    find_project_root,
    find_pyproject_root,
)
from djb.config.fields.project_name import (
    DEFAULT_PROJECT_NAME,
    DNS_LABEL_PATTERN,
    ProjectNameField,
    get_project_name_from_pyproject,
    normalize_project_name,
)
from djb.config.fields.seed_command import SeedCommandField

__all__ = [
    # Field classes
    "EnumField",
    "ProjectDirField",
    "ProjectNameField",
    "EmailField",
    "HostnameField",
    "LogLevelField",
    "NameField",
    "SeedCommandField",
    # Project detection
    "find_project_root",
    "find_pyproject_root",
    "_is_djb_project",
    "PROJECT_DIR_ENV_KEY",
    # Helpers
    "normalize_project_name",
    "get_project_name_from_pyproject",
    "DNS_LABEL_PATTERN",
    "DEFAULT_PROJECT_NAME",
    "DEFAULT_LOG_LEVEL",
    "VALID_LOG_LEVELS",
]
