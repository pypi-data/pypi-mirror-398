"""Tests for djb.config.resolution module; ProvenanceChainMap and ResolutionContext."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from djb.config.resolution import (
    ConfigSource,
    ProvenanceChainMap,
    ResolutionContext,
    _NOT_LOADED,
)


class TestNotLoadedSentinel:
    """Tests for _NOT_LOADED sentinel."""

    def test_is_singleton(self):
        """Test _NOT_LOADED is a unique object."""
        # Each reference should be the same object
        assert _NOT_LOADED is _NOT_LOADED

    def test_not_equal_to_none(self):
        """Test _NOT_LOADED is not equal to None."""
        assert _NOT_LOADED is not None
        assert _NOT_LOADED != None  # noqa: E711

    def test_identity_check(self):
        """Test identity check works for sentinel."""
        value = _NOT_LOADED
        assert value is _NOT_LOADED


class TestProvenanceChainMapGet:
    """Tests for ProvenanceChainMap.get() method."""

    def test_get_from_cli_layer(self):
        """Test get() returns value from CLI layer with correct source."""
        chain = ProvenanceChainMap(
            cli={"project_name": "cli-value"},
            local={"project_name": "local-value"},
            project={"project_name": "project-value"},
        )

        value, source = chain.get("project_name", "DJB_PROJECT_NAME")
        assert value == "cli-value"
        assert source == ConfigSource.CLI

    def test_get_from_env_layer(self):
        """Test get() returns value from env layer with correct source."""
        chain = ProvenanceChainMap(
            cli={},
            env={"DJB_PROJECT_NAME": "env-value"},
            local={"project_name": "local-value"},
            project={"project_name": "project-value"},
        )

        value, source = chain.get("project_name", "DJB_PROJECT_NAME")
        assert value == "env-value"
        assert source == ConfigSource.ENV

    def test_get_from_local_layer(self):
        """Test get() returns value from local layer with correct source."""
        chain = ProvenanceChainMap(
            cli={},
            env={},
            local={"name": "local-value"},
            project={"name": "project-value"},
        )

        value, source = chain.get("name", "DJB_NAME")
        assert value == "local-value"
        assert source == ConfigSource.LOCAL_CONFIG

    def test_get_from_project_layer(self):
        """Test get() returns value from project layer with correct source."""
        chain = ProvenanceChainMap(
            cli={},
            env={},
            local={},
            project={"hostname": "project-value"},
        )

        value, source = chain.get("hostname", "DJB_HOSTNAME")
        assert value == "project-value"
        assert source == ConfigSource.PROJECT_CONFIG

    def test_get_not_found(self):
        """Test get() returns (None, None) when key not found."""
        chain = ProvenanceChainMap(cli={}, env={}, local={}, project={})

        value, source = chain.get("missing_key", "DJB_MISSING")
        assert value is None
        assert source is None

    def test_get_respects_priority_order(self):
        """Test get() respects cli > env > local > project priority."""
        chain = ProvenanceChainMap(
            cli={"key": "cli"},
            env={"DJB_KEY": "env"},
            local={"key": "local"},
            project={"key": "project"},
        )

        # CLI wins
        value, source = chain.get("key", "DJB_KEY")
        assert value == "cli"
        assert source == ConfigSource.CLI

    def test_get_skips_empty_string_in_env(self):
        """Test get() treats empty string as not set (especially for env vars)."""
        chain = ProvenanceChainMap(
            cli={},
            env={"DJB_NAME": ""},
            local={"name": "local-value"},
            project={},
        )

        value, source = chain.get("name", "DJB_NAME")
        assert value == "local-value"
        assert source == ConfigSource.LOCAL_CONFIG

    def test_get_skips_empty_string_in_config(self):
        """Test get() treats empty string as not set in config layers too."""
        chain = ProvenanceChainMap(
            cli={"name": ""},
            env={},
            local={"name": "local-value"},
            project={},
        )

        value, source = chain.get("name", "DJB_NAME")
        assert value == "local-value"
        assert source == ConfigSource.LOCAL_CONFIG

    def test_get_with_no_env_key_skips_env(self):
        """Test get() skips env layer when env_key is None."""
        chain = ProvenanceChainMap(
            cli={},
            env={"DJB_PROJECT_DIR": "env-value"},
            local={},
            project={},
        )

        # Passing None for env_key should skip env layer
        value, source = chain.get("project_dir", None)
        assert value is None
        assert source is None

    def test_get_uses_different_keys_per_layer(self):
        """Test get() uses config_file_key for cli/local/project and env_key for env."""
        chain = ProvenanceChainMap(
            cli={},
            env={"DJB_EMAIL": "env@example.com"},
            local={},
            project={},
        )

        # env layer should be accessed with env_key, not config_file_key
        value, source = chain.get("email", "DJB_EMAIL")
        assert value == "env@example.com"
        assert source == ConfigSource.ENV

        # If we don't provide env_key, env layer should be skipped
        chain2 = ProvenanceChainMap(
            cli={},
            env={"email": "env@example.com"},  # Won't match without env_key
            local={},
            project={},
        )
        value2, source2 = chain2.get("email", None)
        assert value2 is None
        assert source2 is None


class TestProvenanceChainMapContains:
    """Tests for ProvenanceChainMap.__contains__() method."""

    def test_contains_in_cli(self):
        """Test __contains__ finds key in CLI layer."""
        chain = ProvenanceChainMap(cli={"key": "value"})
        assert "key" in chain

    def test_contains_in_env(self):
        """Test __contains__ finds key in env layer (uses config_file_key)."""
        # Note: __contains__ uses config_file_key for all layers
        chain = ProvenanceChainMap(env={"key": "value"})
        assert "key" in chain

    def test_contains_in_local(self):
        """Test __contains__ finds key in local layer."""
        chain = ProvenanceChainMap(local={"key": "value"})
        assert "key" in chain

    def test_contains_in_project(self):
        """Test __contains__ finds key in project layer."""
        chain = ProvenanceChainMap(project={"key": "value"})
        assert "key" in chain

    def test_not_contains(self):
        """Test __contains__ returns False for missing key."""
        chain = ProvenanceChainMap(cli={}, env={}, local={}, project={})
        assert "missing" not in chain


class TestProvenanceChainMapDefaults:
    """Tests for ProvenanceChainMap default behavior."""

    def test_default_env_is_os_environ(self):
        """Test default env layer uses os.environ."""
        # Create a chain without specifying env
        chain = ProvenanceChainMap()

        # Access internal layers to verify os.environ is used
        assert chain._layers["env"] is os.environ

    def test_default_layers_are_empty_dicts(self):
        """Test default cli/local/project layers are empty dicts."""
        chain = ProvenanceChainMap()

        assert chain._layers["cli"] == {}
        assert chain._layers["local"] == {}
        assert chain._layers["project"] == {}


class TestResolutionContext:
    """Tests for ResolutionContext dataclass."""

    def test_creation(self, tmp_path: Path):
        """Test ResolutionContext can be created."""
        chain = ProvenanceChainMap()
        ctx = ResolutionContext(
            project_root=tmp_path,
            project_root_source=ConfigSource.PYPROJECT,
            configs=chain,
        )

        assert ctx.project_root == tmp_path
        assert ctx.project_root_source == ConfigSource.PYPROJECT
        assert ctx.configs is chain

    def test_is_frozen(self, tmp_path: Path):
        """Test ResolutionContext is immutable (frozen)."""
        ctx = ResolutionContext(
            project_root=tmp_path,
            project_root_source=ConfigSource.PYPROJECT,
        )

        with pytest.raises(AttributeError):
            ctx.project_root = tmp_path / "other"  # type: ignore[misc]

    def test_default_configs(self, tmp_path: Path):
        """Test ResolutionContext has default empty ProvenanceChainMap."""
        ctx = ResolutionContext(
            project_root=tmp_path,
            project_root_source=ConfigSource.CWD_PATH,
        )

        assert isinstance(ctx.configs, ProvenanceChainMap)
        value, source = ctx.configs.get("any_key", "DJB_ANY")
        assert value is None
        assert source is None


class TestConfigSourceEnum:
    """Additional tests for ConfigSource enum beyond test_config.py coverage."""

    def test_config_file_type_for_local(self):
        """Test config_file_type property returns 'local' for LOCAL_CONFIG."""
        assert ConfigSource.LOCAL_CONFIG.config_file_type == "local"

    def test_config_file_type_for_project(self):
        """Test config_file_type property returns 'project' for PROJECT_CONFIG."""
        assert ConfigSource.PROJECT_CONFIG.config_file_type == "project"

    def test_config_file_type_for_non_config_sources(self):
        """Test config_file_type returns None for non-config sources."""
        assert ConfigSource.CLI.config_file_type is None
        assert ConfigSource.ENV.config_file_type is None
        assert ConfigSource.PYPROJECT.config_file_type is None
        assert ConfigSource.GIT.config_file_type is None
        assert ConfigSource.CWD_PATH.config_file_type is None
        assert ConfigSource.CWD_NAME.config_file_type is None
        assert ConfigSource.DEFAULT.config_file_type is None
        assert ConfigSource.DERIVED.config_file_type is None
        assert ConfigSource.PROMPTED.config_file_type is None

    def test_cwd_path_and_cwd_name_are_derived(self):
        """Test CWD_PATH and CWD_NAME are classified as derived."""
        assert ConfigSource.CWD_PATH.is_derived() is True
        assert ConfigSource.CWD_NAME.is_derived() is True
        assert ConfigSource.CWD_PATH.is_explicit() is False
        assert ConfigSource.CWD_NAME.is_explicit() is False

    def test_default_is_derived(self):
        """Test DEFAULT is classified as derived."""
        assert ConfigSource.DEFAULT.is_derived() is True
        assert ConfigSource.DEFAULT.is_explicit() is False
