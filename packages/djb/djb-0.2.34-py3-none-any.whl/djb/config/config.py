"""
DjbConfig: configuration class.

This module provides two classes:
- DjbConfigBase: Abstract base class providing lazy loading, immutability
  (@attrs.frozen), and config field provenance tracking.
- DjbConfig: Concrete config class with field definitions, serialization,
  and persistence methods.

Configuration is loaded with the following priority (highest to lowest):
1. CLI flags (passed via configure() before accessing config singleton)
2. Environment variables (DJB_ prefix)
3. Local config (.djb/local.yaml) - user-specific, gitignored
4. Project config (.djb/project.yaml) - shared, committed
5. Default values
"""

from __future__ import annotations

import json
import threading
import traceback
from abc import ABC
from collections.abc import Generator
from contextlib import contextmanager
from enum import Enum, auto
from pathlib import Path
from typing import Any, ClassVar

import attrs


from djb.config.resolution import (
    _NOT_LOADED,
    ProvenanceChainMap,
    ResolutionContext,
)
from djb.config.fields import (
    DEFAULT_LOG_LEVEL,
    EmailField,
    EnumField,
    HostnameField,
    LogLevelField,
    NameField,
    ProjectDirField,
    ProjectNameField,
    SeedCommandField,
    find_project_root,
)
from djb.config.constants import ATTRSLIB_METADATA_KEY
from djb.config.file import LOCAL, PROJECT, load_config, save_config
from djb.config.resolution import ConfigSource
from djb.types import Mode, Target


class LoadState(Enum):
    """Loading state for DjbConfigBase instances.

    CONSTRUCTING: attrs is building the instance. During __init__, attrs validates
        each field by accessing it via __getattribute__ (e.g., to pass to validators).
        We must not trigger lazy loading during this phase because field values are
        still being set up. This state prevents __getattribute__ from calling load().

    READY: Construction complete (__attrs_post_init__ has run). Safe to trigger
        lazy loading when a field with a sentinel value is accessed.

    LOADED: Configuration has been fully loaded. All field values are resolved.
    """

    CONSTRUCTING = auto()
    READY = auto()
    LOADED = auto()


@attrs.frozen
class DjbConfigBase(ABC):
    """Base class for DjbConfig with lazy loading, immutability, and provenance.

    This class implements a lazy-loading immutable configuration singleton using
    several interacting mechanisms:

    ## Lazy Loading via Sentinel Values

    Each config field starts with the `_NOT_LOADED` sentinel value (not the actual
    resolved value). This defers all config file and environment variable access
    until the first field is accessed, avoiding I/O at import time.

    ## `__getattribute__` Override

    Intercepts all attribute access to implement transparent lazy loading:

    1. Private attributes (`_name`) and methods bypass lazy loading entirely
    2. During construction (CONSTRUCTING) or after loading (LOADED), returns value directly
    3. When READY and field contains `_NOT_LOADED`, calls `load()` to resolve all fields
    4. After loading, returns the resolved value; subsequent accesses return directly

    This makes lazy loading invisible to callers. E.g. `config.project_name` works
    identically whether accessed before or after loading.

    ## `__attrs_post_init__` Hook

    Transitions `_loaded` from CONSTRUCTING to READY after attrs completes `__init__`.
    This is necessary because attrs validates fields during construction by accessing
    them through `__getattribute__` (to pass values to validators). Without this
    guard, the validator access would trigger lazy loading before the instance is
    fully constructed.

    ## Working with @attrs.frozen

    The `@attrs.frozen` decorator prevents attribute mutation after initialization
    by installing a custom `__setattr__` that raises `FrozenInstanceError`.

    However, mutation is required during lazy loading. The solution is
    `object.__setattr__()`, which bypasses the frozen restriction by calling
    the base object class directly. This is the officially documented attrs pattern
    for modifying frozen instances.

    Used in `load()` for populating field values, `_provenance`, and `_loaded`.

    ## Thread Safety

    The class-level `_lock` ensures only one thread performs config resolution.
    Once `_loaded` is True, the instance is effectively immutable and safe
    for concurrent read access.

    ## Provenance Tracking

    The `_provenance` dict maps field names to their `ConfigSource` values,
    recording where each value came from (CLI, env, local.yaml, project.yaml,
    pyproject.toml, git config, defaults, etc.). This enables:

    - Consistent save behavior (preserve original source file)
    - Init workflow (skip already-configured fields)
    - Debugging (show source in `djb config show --provenance`)

    ## Public Methods

    - `load(overrides)`: Load config (called automatically on first access)
    - `is_explicit(field)`: True if field came from CLI, env, or config file
    - `is_derived(field)`: True if field came from pyproject, git, or fallback
    - `has_no_source(field)`: True if field has no tracked provenance
    - `get_source(field)`: Get the ConfigSource for a field
    """

    # === Class-level state ===
    _lock: ClassVar[threading.Lock] = threading.Lock()
    _pending_overrides: ClassVar[dict[str, Any]] = {}
    _first_access_stack: ClassVar[str | None] = None

    # === Instance state ===
    _loaded: LoadState = attrs.field(default=LoadState.CONSTRUCTING, init=False, repr=False)
    _provenance: dict[str, ConfigSource] = attrs.field(
        factory=dict, repr=False, alias="_provenance"
    )

    def __attrs_post_init__(self) -> None:
        """Mark instance as ready for lazy loading (done constructing)."""
        object.__setattr__(self, "_loaded", LoadState.READY)

    def __getattribute__(self, name: str) -> Any:
        """Trigger loading when accessing a field with sentinel value.

        _loaded states: CONSTRUCTING, READY, LOADED.
        Only trigger lazy load when READY and field has sentinel value.
        """
        # Allow internal attributes and methods without any special handling
        if name.startswith("_") or not name[0].islower():
            return object.__getattribute__(self, name)

        # Check _loaded state to only allow load when READY
        loaded = object.__getattribute__(self, "_loaded")
        if loaded is not LoadState.READY:
            return object.__getattribute__(self, name)

        # READY: check if this field needs loading (has sentinel value)
        value = object.__getattribute__(self, name)
        if value is _NOT_LOADED:
            self.load()
            return object.__getattribute__(self, name)

        return value

    def __repr__(self) -> str:
        """Show unloaded state or field values."""
        if object.__getattribute__(self, "_loaded") is not LoadState.LOADED:
            return f"<{type(self).__name__} [not loaded]>"
        # Build repr manually to avoid triggering __getattribute__
        loaded_attrs = []
        for field in attrs.fields(type(self)):
            if field.name.startswith("_") or not field.repr:
                continue
            value = object.__getattribute__(self, field.name)
            loaded_attrs.append(f"{field.name}={value!r}")
        return f"{type(self).__name__}({', '.join(loaded_attrs)})"

    def load(self, overrides: dict[str, Any] | None = None) -> None:
        """Load config from sources. Thread-safe.

        Args:
            overrides: CLI overrides dict (highest priority). If None, uses
                class-level _pending_overrides (for singleton lazy loading).
                None values are filtered out.
        """
        with self._lock:
            if object.__getattribute__(self, "_loaded") is LoadState.LOADED:
                return

            # Filter None values and use pending overrides if not provided
            if overrides is None:
                type(self)._first_access_stack = "".join(traceback.format_stack()[:-3])
                overrides = self._pending_overrides
            else:
                overrides = {k: v for k, v in overrides.items() if v is not None}

            # Bootstrap: determine project root for file loading
            cli_project_dir = Path(overrides["project_dir"]) if "project_dir" in overrides else None
            resolved_root, root_source = find_project_root(
                project_root=cli_project_dir,
                fallback_to_cwd=True,
            )

            # Load all config layers (env defaults to os.environ)
            configs = ProvenanceChainMap(
                cli=overrides,
                local=load_config(LOCAL, resolved_root, known_keys=self._get_known_keys("local")),
                project=load_config(
                    PROJECT, resolved_root, known_keys=self._get_known_keys("project")
                ),
            )

            # Create resolution context
            ctx = ResolutionContext(
                project_root=resolved_root,
                project_root_source=root_source,
                configs=configs,
            )

            # Resolve each field using its ConfigField from metadata
            provenance: dict[str, ConfigSource] = {}
            for field in attrs.fields(type(self)):
                if field.name.startswith("_"):
                    continue  # Skip internal fields

                config_field = field.metadata.get(ATTRSLIB_METADATA_KEY)
                if config_field is None:
                    continue  # Not a config field

                # Skip fields that already have non-sentinel values (explicit instantiation)
                current_value = object.__getattribute__(self, field.name)
                if current_value is not _NOT_LOADED:
                    continue

                # Set field_name so env_key/file_key can auto-derive
                config_field.field_name = field.name

                # All resolution logic is inside the ConfigField class
                value, source = config_field.resolve(ctx)

                # Validate the resolved value
                config_field.validate(value)

                object.__setattr__(self, field.name, value)
                if source:
                    provenance[field.name] = source

            object.__setattr__(self, "_provenance", provenance)
            object.__setattr__(self, "_loaded", LoadState.LOADED)

    @classmethod
    def _get_known_keys(cls, config_file: str) -> frozenset[str]:
        """Get known config keys for a file type by introspecting fields.

        Args:
            config_file: Either "local" or "project".

        Returns:
            Frozenset of known key names for that config file.

        Note:
            For local config, returns all config keys (local + project) since
            local.yaml can override any project setting. For project config,
            returns only project-level keys.
        """
        keys: set[str] = set()
        for field in attrs.fields(cls):
            config_field = field.metadata.get(ATTRSLIB_METADATA_KEY)
            if config_field is None:
                continue
            # Local config can contain any key (local or project) since it can override
            # project settings. Project config only contains project-level keys.
            if config_file == "local" or config_field.config_file == config_file:
                keys.add(config_field.config_file_key or field.name)
        return frozenset(keys)

    def is_explicit(self, field: str) -> bool:
        """Check if a field was explicitly configured.

        Args:
            field: Field name to check.

        Returns:
            True if the field value came from an explicit source
            (CLI, env var, or config file).
        """
        source = self._provenance.get(field)
        return source is not None and source.is_explicit()

    def is_derived(self, field: str) -> bool:
        """Check if a field was derived from secondary sources.

        Args:
            field: Field name to check.

        Returns:
            True if the field value was derived (from pyproject.toml,
            git config, or directory name).
        """
        source = self._provenance.get(field)
        return source is not None and source.is_derived()

    def is_configured(self, field: str) -> bool:
        """Check if a field has no configured value.

        Args:
            field: Field name to check.

        Returns:
            True if the field has no source in provenance tracking
            (not from CLI, env, config file, or derived sources).
        """
        return self.get_source(field) is not None

    def get_source(self, field: str) -> ConfigSource | None:
        """Get the source of a field's value.

        Args:
            field: Field name to check.

        Returns:
            The ConfigSource for the field, or None if not tracked.
        """
        return self._provenance.get(field)


@attrs.frozen
class DjbConfig(DjbConfigBase):
    """Unified configuration for djb CLI with lazy loading.

    Loads configuration from multiple sources with priority:
    1. CLI flags (passed via configure() before accessing config singleton)
    2. Environment variables (DJB_ prefix)
    3. Local config (.djb/local.yaml)
    4. Project config (.djb/project.yaml)
    5. Defaults (e.g. pyproject.toml for project_name)

    Each field uses the ConfigField()() pattern - the first call creates the
    ConfigField instance, the second returns an attrs.field() with metadata.

    Fields start as sentinel values and are resolved lazily on first access.
    Immutability is enforced by @attrs.frozen (inherited from DjbConfigBase).

    Inherits lazy loading and provenance tracking from DjbConfigBase.
    """

    # === Mandatory fields ===
    # These fields always resolve to a value through their resolve() method
    project_dir: Path = ProjectDirField()()
    project_name: str = ProjectNameField(config_file="project")()

    # === Optional fields ===
    # Enum fields
    mode: Mode = EnumField(Mode, config_file="local", default=Mode.DEVELOPMENT)()
    target: Target = EnumField(Target, config_file="project", default=Target.HEROKU)()

    # User identity fields (configured during init via INIT_CONFIGURABLE_FIELDS)
    name: str | None = NameField(config_file="local", default=None)()
    email: str | None = EmailField(config_file="local", default=None)()

    # Project settings (hostname configured during init)
    hostname: str | None = HostnameField(config_file="project", default=None)()
    seed_command: str | None = SeedCommandField(config_file="project", default=None)()
    log_level: str = LogLevelField(config_file="project", default=DEFAULT_LOG_LEVEL)()

    def to_dict(self) -> dict[str, Any]:
        """Convert config to a JSON-serializable dictionary.

        Returns:
            Dictionary with all config values. Path objects are converted
            to strings, Enum values to their string values, and private
            attributes are excluded.
        """
        config_dict = attrs.asdict(self)
        # Convert Path to string
        config_dict["project_dir"] = str(config_dict["project_dir"])
        # Convert Enum values to strings
        config_dict["mode"] = config_dict["mode"].value
        config_dict["target"] = config_dict["target"].value
        # Remove private attributes
        config_dict.pop("_loaded", None)
        config_dict.pop("_provenance", None)
        return config_dict

    def to_json(self, indent: int = 2) -> str:
        """Convert config to a JSON string.

        Args:
            indent: Number of spaces for indentation. Default is 2.

        Returns:
            JSON string representation of the config.
        """
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, project_root: Path | None = None) -> None:
        """Save config using provenance (or config_file default) for storage location.

        Only saves config files that have changes.

        Args:
            project_root: Project root path. Defaults to self.project_dir.
        """
        if project_root is None:
            project_root = self.project_dir

        local_config = load_config(LOCAL, project_root)
        project_config = load_config(PROJECT, project_root)
        local_changed = False
        project_changed = False

        for field in attrs.fields(self.__class__):
            config_field = field.metadata.get(ATTRSLIB_METADATA_KEY)
            if config_field is None or config_field.config_file is None:
                continue  # Skip internal fields and transient fields

            config_field.field_name = field.name  # For config_file_key derivation
            value = getattr(self, field.name)
            if value is None:
                continue

            # Convert enums to strings for storage
            if isinstance(value, Enum):
                value = str(value)

            file_key = config_field.config_file_key or field.name

            # Determine storage: provenance takes precedence over config_file default
            source = self._provenance.get(field.name)
            target_file = (source.config_file_type if source else None) or config_field.config_file

            if target_file == LOCAL:
                local_config[file_key] = value
                local_changed = True
            elif target_file == PROJECT:
                project_config[file_key] = value
                project_changed = True

        if local_changed:
            save_config(LOCAL, local_config, project_root)
        if project_changed:
            save_config(PROJECT, project_config, project_root)

    def save_mode(self, project_root: Path | None = None) -> None:
        """Save only the mode to local config file.

        Used when --mode is explicitly passed to persist it.

        Args:
            project_root: Project root path. Defaults to self.project_dir.
        """
        if project_root is None:
            project_root = self.project_dir

        existing = load_config(LOCAL, project_root)
        existing["mode"] = str(self.mode)
        save_config(LOCAL, existing, project_root)


# =============================================================================
# Module-level singleton
# =============================================================================

# The config singleton - just a DjbConfig instance with lazy loading built-in
config: DjbConfig = DjbConfig()


def reset_config() -> None:
    """Reset the global config singleton to an unloaded state.

    This is a test utility that allows tests to start fresh with different
    environment variables or project paths. It resets the existing instance
    rather than creating a new one, so modules that imported `config` directly
    will see the reset state.

    Typically used via the autouse `test_config_env` fixture which calls this
    before and after each test. May also be called manually when a test needs
    to reset config between multiple CLI invocations.
    """
    # Clear class-level state
    DjbConfig._pending_overrides = {}
    DjbConfig._first_access_stack = None

    # Reset the existing instance to unloaded state
    object.__setattr__(config, "_loaded", LoadState.READY)
    object.__setattr__(config, "_provenance", {})

    # Reset all public fields to sentinel
    for field in attrs.fields(DjbConfig):
        if not field.name.startswith("_"):
            object.__setattr__(config, field.name, _NOT_LOADED)


def configure(**overrides: Any) -> None:
    """Set CLI overrides before config loads.

    Must be called before any code accesses the config. Raises RuntimeError
    if called after config has already materialized.

    Args:
        **overrides: Config values to override. None values are filtered out.

    Raises:
        RuntimeError: If config has already been accessed.

    Example:
        from djb import config
        from djb.config import configure
        configure(mode=Mode.PRODUCTION, project_dir=Path("/my/project"))
        # Now accessing config will include the overrides
        print(config.mode)  # Mode.PRODUCTION
    """
    # Check if config is already loaded
    if object.__getattribute__(config, "_loaded") is LoadState.LOADED:
        first_access = DjbConfig._first_access_stack
        msg = "configure() must be called before accessing config. Config has already been loaded."
        if first_access:
            msg += f"\n\nConfig was first accessed at:\n{first_access}"
        raise RuntimeError(msg)

    # Filter out None values and store in class-level overrides
    DjbConfig._pending_overrides.update({k: v for k, v in overrides.items() if v is not None})


@contextmanager
def config_for_project(project_dir: Path | str) -> Generator[DjbConfig, None, None]:
    """Temporarily load config for a different project.

    Creates an isolated config instance for the specified project,
    yielding it for use within the context. Does not affect the
    global singleton.

    Args:
        project_dir: Path to the project directory.

    Yields:
        A loaded DjbConfig instance for the specified project.

    Example:
        from djb.config import config_for_project

        with config_for_project("/path/to/other/project") as other:
            print(other.project_name)
    """
    instance = DjbConfig()
    instance.load({"project_dir": str(project_dir)})
    yield instance
