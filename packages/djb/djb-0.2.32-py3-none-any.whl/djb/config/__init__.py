"""
djb.config - Unified configuration system for djb CLI.

Quick start:
    from djb import config

    print(f"Mode: {config.mode}")        # development, staging, production
    print(f"Target: {config.target}")    # local or heroku
    print(f"Project: {config.project_name}")

Configuration is loaded with the following priority (highest to lowest):
1. CLI flags (applied via configure() before accessing config singleton)
2. Environment variables (DJB_ prefix)
3. Local config (.djb/local.yaml) - user-specific, gitignored
4. Project config (.djb/project.yaml) - shared, committed
5. Default values

Two config files are used:
- .djb/local.yaml: User-specific settings (name, email, mode) - NOT committed
- .djb/project.yaml: Project settings (hostname, project_name, target) - committed

Local config can override any project setting for user experimentation.

## Public API

### Main API
- config: Global lazy config instance, loads on first access
- configure: Set CLI overrides before config loads
- DjbConfig: Main configuration class with declarative fields
- ConfigSource: Enum tracking where a config value came from

### Test Utilities
- reset_config: Reset config singleton to unloaded state

### Config File Operations
- get_config_dir: Get path to .djb/ directory
- get_config_path: Get path to a specific config file
- load_config: Load a config file by type
- save_config: Save a config file by type
- LOCAL, PROJECT: Config type constants

### Field System (for extending DjbConfig)
- ConfigFieldABC: Abstract base class for config fields
- StringField, EnumField: Common field types
- ProjectDirField, ProjectNameField, EmailField, SeedCommandField: Specialized fields
- ProvenanceChainMap: Layered config resolution with provenance tracking
- ResolutionContext: Context passed to field resolution
- DjbConfigBase: Base class for DjbConfig (lazy loading + provenance)
- ATTRSLIB_METADATA_KEY: Metadata key for storing ConfigField in attrs metadata

### Project Detection
- find_project_root: Find the project root directory
- find_pyproject_root: Find the nearest pyproject.toml

### Validation & Normalization
- ConfigValidationError: Exception for validation failures
- ConfigFileType: Type alias for config file types
- normalize_project_name: Normalize a string to DNS-safe label
- get_project_name_from_pyproject: Extract project name from pyproject.toml
- DEFAULT_PROJECT_NAME: Default project name when resolution fails
- DNS_LABEL_PATTERN: Pattern for validating DNS labels
"""

from djb.config.acquisition import (
    AcquisitionContext,
    AcquisitionResult,
    ExternalSource,
    GitConfigSource,
    acquire_all_fields,
)
from djb.config.field import (
    ConfigFieldABC,
    ConfigValidationError,
    StringField,
)
from djb.config.fields import EnumField
from djb.config.resolution import (
    ConfigSource,
    ProvenanceChainMap,
    ResolutionContext,
)
from djb.config.config import (
    DjbConfig,
    DjbConfigBase,
    config,
    config_for_project,
    configure,
    reset_config,
)
from djb.config.fields import (
    DEFAULT_PROJECT_NAME,
    DNS_LABEL_PATTERN,
    EmailField,
    ProjectDirField,
    ProjectNameField,
    SeedCommandField,
    get_project_name_from_pyproject,
    normalize_project_name,
)
from djb.config.file import (
    LOCAL,
    PROJECT,
    ConfigFileType,
    get_config_dir,
    get_config_path,
    load_config,
    save_config,
)
from djb.config.fields import find_project_root, find_pyproject_root
from djb.config.constants import ATTRSLIB_METADATA_KEY

__all__ = [
    # Main API
    "config",
    "config_for_project",
    "configure",
    "DjbConfig",
    "ConfigSource",
    # Test utilities
    "reset_config",
    # Config file operations
    "get_config_dir",
    "get_config_path",
    "load_config",
    "save_config",
    "LOCAL",
    "PROJECT",
    # Field system
    "ConfigFieldABC",
    "StringField",
    "EnumField",
    "ProjectDirField",
    "ProjectNameField",
    "EmailField",
    "SeedCommandField",
    "ProvenanceChainMap",
    "ResolutionContext",
    "DjbConfigBase",
    "ATTRSLIB_METADATA_KEY",
    # Interactive acquisition (for field.acquire())
    "AcquisitionContext",
    "AcquisitionResult",
    "ExternalSource",
    "GitConfigSource",
    "acquire_all_fields",
    # Project detection
    "find_project_root",
    "find_pyproject_root",
    # Validation & normalization
    "ConfigValidationError",
    "ConfigFileType",
    "normalize_project_name",
    "get_project_name_from_pyproject",
    "DEFAULT_PROJECT_NAME",
    "DNS_LABEL_PATTERN",
]
