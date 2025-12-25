"""Tests for djb.config module."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import djb
import pytest

from djb.config import (
    LOCAL,
    PROJECT,
    ConfigSource,
    ConfigValidationError,
    DjbConfig,
    config,
    configure,
    get_config_dir,
    get_config_path,
    get_project_name_from_pyproject,
    load_config,
    save_config,
)
from djb.types import Mode, Target


class TestConfigPaths:
    """Tests for config path helpers."""

    def test_get_config_dir(self, tmp_path):
        """Test get_config_dir returns .djb directory."""
        result = get_config_dir(tmp_path)
        assert result == tmp_path / ".djb"

    def test_get_config_path_local(self, tmp_path):
        """Test get_config_path returns local.yaml path for LOCAL type."""
        result = get_config_path(LOCAL, tmp_path)
        assert result == tmp_path / ".djb" / "local.yaml"

    def test_get_config_path_project(self, tmp_path):
        """Test get_config_path returns project.yaml path for PROJECT type."""
        result = get_config_path(PROJECT, tmp_path)
        assert result == tmp_path / ".djb" / "project.yaml"

    def test_get_config_path_invalid_type(self, tmp_path):
        """Test get_config_path raises error for invalid config type."""
        with pytest.raises(ValueError, match="Unknown config type"):
            get_config_path("invalid", tmp_path)  # type: ignore[arg-type]


class TestLoadSaveConfig:
    """Tests for load_config and save_config."""

    def test_load_config_missing(self, tmp_path):
        """Test loading when config file doesn't exist."""
        result = load_config(LOCAL, tmp_path)
        assert result == {}

    def test_load_config_exists(self, tmp_path, make_config_file):
        """Test loading existing config file."""
        make_config_file("name: John\nemail: john@example.com\n")

        result = load_config(LOCAL, tmp_path)
        assert result == {"name": "John", "email": "john@example.com"}

    def test_load_config_empty(self, tmp_path, make_config_file):
        """Test loading empty config file."""
        make_config_file("")

        result = load_config(LOCAL, tmp_path)
        assert result == {}

    def test_load_config_rejects_non_mapping(self, tmp_path, make_config_file):
        """Test load_config raises when YAML isn't a mapping."""
        make_config_file("- item\n")

        with pytest.raises(ValueError, match="expected a mapping"):
            load_config(LOCAL, tmp_path)

    def test_save_config_creates_directory(self, tmp_path):
        """Test save_config creates .djb directory if needed."""
        data = {"name": "John"}
        save_config(LOCAL, data, tmp_path)

        assert (tmp_path / ".djb").exists()
        assert (tmp_path / ".djb" / "local.yaml").exists()

    def test_save_config_content(self, tmp_path):
        """Test save_config writes correct content."""
        data = {"name": "John", "email": "john@example.com"}
        save_config(LOCAL, data, tmp_path)

        result = load_config(LOCAL, tmp_path)
        assert result == data

    def test_load_missing_files(self, tmp_path):
        """Test loading config when files don't exist uses defaults."""
        configure(project_dir=str(tmp_path))
        # Config uses defaults when no files exist
        assert config.name is None
        assert config.email is None
        assert config.mode == Mode.DEVELOPMENT  # default
        assert config.target == Target.HEROKU  # default

    def test_load_merges_both(self, tmp_path, make_config_file):
        """Test DjbConfig.load merges project + local configs."""
        # Project config
        make_config_file("hostname: example.com\ntarget: heroku\n", config_type="project")
        # Local config
        make_config_file("name: John\nemail: john@example.com\n")

        configure(project_dir=str(tmp_path))
        assert config.hostname == "example.com"
        assert config.target == Target.HEROKU
        assert config.name == "John"
        assert config.email == "john@example.com"

    def test_local_config_overrides_project_config(self, tmp_path, make_config_file):
        """Test local config takes precedence over project config."""
        # Project config sets hostname
        make_config_file("hostname: project.example.com\n", config_type="project")
        # Local config overrides hostname
        make_config_file("hostname: local.example.com\n")

        configure(project_dir=str(tmp_path))
        assert config.hostname == "local.example.com"


class TestGetProjectNameFromPyproject:
    """Tests for get_project_name_from_pyproject."""

    def test_reads_project_name(self, tmp_path):
        """Test reading project name from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\nversion = "1.0.0"\n')

        result = get_project_name_from_pyproject(tmp_path)
        assert result == "myproject"

    def test_normalizes_project_name(self, tmp_path):
        """Test project name normalization for DNS-safe values."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "My_Project.Name"\nversion = "1.0.0"\n')

        result = get_project_name_from_pyproject(tmp_path)
        assert result == "my-project-name"

    def test_invalid_project_name_returns_none(self, tmp_path):
        """Test invalid project name returns None."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "My Project"\n')

        result = get_project_name_from_pyproject(tmp_path)
        assert result is None

    def test_missing_pyproject(self, tmp_path):
        """Test when pyproject.toml doesn't exist."""
        result = get_project_name_from_pyproject(tmp_path)
        assert result is None

    def test_missing_project_section(self, tmp_path):
        """Test when pyproject.toml has no project section."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.pytest]\n")

        result = get_project_name_from_pyproject(tmp_path)
        assert result is None

    def test_missing_name_field(self, tmp_path):
        """Test when project section has no name."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "1.0.0"\n')

        result = get_project_name_from_pyproject(tmp_path)
        assert result is None

    def test_invalid_toml(self, tmp_path):
        """Test with invalid TOML content."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("this is not valid toml [[[")

        result = get_project_name_from_pyproject(tmp_path)
        assert result is None


class TestDjbConfig:
    """Tests for DjbConfig class."""

    def test_default_values(self, tmp_path):
        """Test DjbConfig default values."""
        cfg = DjbConfig()
        cfg.load({"project_dir": str(tmp_path), "project_name": "testproject"})
        assert cfg.project_dir == tmp_path
        assert cfg.project_name == "testproject"
        assert cfg.mode == Mode.DEVELOPMENT
        assert cfg.target == Target.HEROKU
        assert cfg.name is None
        assert cfg.email is None

    def test_validation_rejects_invalid_project_name(self, tmp_path):
        """Test invalid project_name raises a validation error."""
        with pytest.raises(ConfigValidationError, match="DNS label"):
            cfg = DjbConfig()
            cfg.load({"project_dir": str(tmp_path), "project_name": "Bad_Project"})

    def test_validation_rejects_invalid_email(self, tmp_path):
        """Test invalid email raises a validation error."""
        with pytest.raises(ConfigValidationError, match="email"):
            cfg = DjbConfig()
            cfg.load(
                {"project_dir": str(tmp_path), "project_name": "test", "email": "not-an-email"}
            )

    def test_validation_rejects_invalid_seed_command(self, tmp_path):
        """Test invalid seed_command raises a validation error."""
        with pytest.raises(ConfigValidationError, match="module.path:attribute"):
            cfg = DjbConfig()
            cfg.load(
                {
                    "project_dir": str(tmp_path),
                    "project_name": "test",
                    "seed_command": "not-a-command",
                }
            )

    def test_validation_rejects_invalid_yaml_types(self, tmp_path):
        """Test that non-string YAML types are caught during validation."""
        # When loading from config files, YAML can produce non-string types.
        # Booleans like True normalize to "True" which fails DNS validation.
        save_config(PROJECT, {"project_name": True}, tmp_path)  # YAML boolean
        with pytest.raises(ConfigValidationError, match="DNS label"):
            cfg = DjbConfig()
            cfg.load({"project_dir": str(tmp_path)})

    def test_load_overrides(self, tmp_path):
        """Test DjbConfig.load applies overrides."""
        configure(
            project_dir=str(tmp_path),
            name="John",
            email="john@example.com",
            mode=Mode.PRODUCTION,
        )

        assert config.name == "John"
        assert config.email == "john@example.com"
        assert config.mode == Mode.PRODUCTION

    def test_load_ignores_none(self, tmp_path):
        """Test DjbConfig.load ignores None values in overrides."""
        # Set up a config file with name
        save_config(LOCAL, {"name": "John"}, tmp_path)

        # Override with None should preserve the file value
        configure(project_dir=str(tmp_path), name=None, email="john@example.com")

        # name should be preserved since override was None
        assert config.name == "John"
        assert config.email == "john@example.com"

    def test_load_tracks_cli_overrides(self, tmp_path):
        """Test DjbConfig.load tracks CLI overrides via provenance."""
        configure(project_dir=str(tmp_path), mode=Mode.STAGING, name="John")

        # Access a field to trigger loading
        assert config.mode == Mode.STAGING
        assert config.name == "John"

        # CLI overrides are tracked in provenance with ConfigSource.CLI
        assert config.get_source("mode") == ConfigSource.CLI
        assert config.get_source("name") == ConfigSource.CLI
        # project_dir comes from CLI override too
        assert config.get_source("project_dir") == ConfigSource.CLI

    def test_save(self, tmp_path):
        """Test save persists config to file."""
        cfg = DjbConfig()
        cfg.load(
            {
                "project_dir": str(tmp_path),
                "project_name": "myproject",
                "name": "John",
                "email": "john@example.com",
                "mode": Mode.STAGING,
                "target": Target.HEROKU,
                "hostname": "example.com",
                "seed_command": "myapp.cli.seed:seed",
            }
        )
        cfg.save()

        # User settings go to local config
        local = load_config(LOCAL, tmp_path)
        assert local["name"] == "John"
        assert local["email"] == "john@example.com"
        assert local["mode"] == "staging"

        # Project settings go to project config
        project = load_config(PROJECT, tmp_path)
        assert project["project_name"] == "myproject"
        assert project["target"] == "heroku"
        assert project["hostname"] == "example.com"
        assert project["seed_command"] == "myapp.cli.seed:seed"

    def test_save_removes_none_values(self, tmp_path):
        """Test save doesn't write None values."""
        # Note: email is typed as str but defaults to None at runtime.
        # This tests that None values aren't persisted to the config file.
        cfg = DjbConfig()
        cfg.load({"project_dir": str(tmp_path), "project_name": "test", "name": "John"})
        cfg.save()

        loaded = load_config(LOCAL, tmp_path)
        assert loaded["name"] == "John"
        assert "email" not in loaded

    def test_save_mode(self, tmp_path):
        """Test save_mode only saves mode."""
        # Create existing config
        save_config(LOCAL, {"name": "John", "mode": "development"}, tmp_path)

        cfg = DjbConfig()
        cfg.load({"project_dir": str(tmp_path), "project_name": "test", "mode": Mode.PRODUCTION})
        cfg.save_mode()

        loaded = load_config(LOCAL, tmp_path)
        assert loaded["mode"] == "production"
        assert loaded["name"] == "John"  # Preserved

    def test_to_dict(self, tmp_path):
        """Test to_dict returns JSON-serializable dictionary."""
        cfg = DjbConfig()
        cfg.load(
            {
                "project_dir": str(tmp_path),
                "project_name": "myproject",
                "name": "John",
                "email": "john@example.com",
                "mode": Mode.STAGING,
                "target": Target.HEROKU,
            }
        )
        result = cfg.to_dict()

        assert result["project_dir"] == str(tmp_path)
        assert result["project_name"] == "myproject"
        assert result["name"] == "John"
        assert result["email"] == "john@example.com"
        assert result["mode"] == "staging"
        assert result["target"] == "heroku"
        assert "_cli_overrides" not in result

    def test_to_dict_excludes_cli_overrides(self, tmp_path):
        """Test to_dict excludes _cli_overrides."""
        configure(project_dir=str(tmp_path), name="John")

        result = config.to_dict()
        assert "_cli_overrides" not in result

    def test_to_json(self, tmp_path):
        """Test to_json returns valid JSON string."""
        cfg = DjbConfig()
        cfg.load(
            {
                "project_dir": str(tmp_path),
                "project_name": "myproject",
                "name": "John",
            }
        )
        result = cfg.to_json()

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed["project_name"] == "myproject"
        assert parsed["name"] == "John"

    def test_to_json_custom_indent(self, tmp_path):
        """Test to_json respects indent parameter."""
        cfg = DjbConfig()
        cfg.load({"project_dir": str(tmp_path), "project_name": "test"})

        # Default indent is 2
        result_default = cfg.to_json()
        assert "  " in result_default

        # Custom indent of 4
        result_4 = cfg.to_json(indent=4)
        assert "    " in result_4


class TestDjbConfigLoad:
    """Tests for DjbConfig.load() method."""

    def test_loads_from_file(self, tmp_path):
        """Test DjbConfig.load loads from config file."""
        save_config(
            LOCAL, {"name": "John", "email": "john@example.com", "mode": "staging"}, tmp_path
        )

        configure(project_dir=str(tmp_path))
        assert config.name == "John"
        assert config.email == "john@example.com"
        assert config.mode == Mode.STAGING

    def test_env_overrides_file(self, tmp_path):
        """Test environment variables override file config."""
        save_config(LOCAL, {"name": "John"}, tmp_path)

        with patch.dict(os.environ, {"DJB_NAME": "Jane"}):
            configure(project_dir=str(tmp_path))
            assert config.name == "Jane"

    def test_project_name_from_pyproject(self, tmp_path):
        """Test project_name falls back to pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\n')

        configure(project_dir=str(tmp_path))
        assert config.project_name == "myproject"

    def test_invalid_pyproject_name_falls_back_to_dir_name(self, tmp_path):
        """Test invalid pyproject name falls back to directory name derivation."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "My Project"\n')

        configure(project_dir=str(tmp_path))
        # project_name is now always derived - falls back to directory name
        # The tmp_path directory name is normalized to a DNS-safe label
        assert config.project_name is not None
        assert config.project_name != ""

    def test_project_name_config_overrides_pyproject(self, tmp_path):
        """Test config file project_name overrides pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "pyproject-name"\n')
        save_config(PROJECT, {"project_name": "config-name"}, tmp_path)

        configure(project_dir=str(tmp_path))
        assert config.project_name == "config-name"

    def test_default_mode(self, tmp_path):
        """Test default mode is DEVELOPMENT."""
        configure(project_dir=str(tmp_path))
        assert config.mode == Mode.DEVELOPMENT

    def test_default_target(self, tmp_path):
        """Test default target is HEROKU."""
        configure(project_dir=str(tmp_path))
        assert config.target == Target.HEROKU

    def test_env_mode(self, tmp_path):
        """Test DJB_MODE environment variable."""
        with patch.dict(os.environ, {"DJB_MODE": "production"}):
            configure(project_dir=str(tmp_path))
            assert config.mode == Mode.PRODUCTION

    def test_env_target(self, tmp_path):
        """Test DJB_TARGET environment variable."""
        with patch.dict(os.environ, {"DJB_TARGET": "heroku"}):
            configure(project_dir=str(tmp_path))
            assert config.target == Target.HEROKU

    def test_project_dir_defaults_to_passed_root(self, tmp_path):
        """Test project_dir defaults to the passed project_root."""
        configure(project_dir=str(tmp_path))
        assert config.project_dir == tmp_path

    def test_env_project_dir_used_for_config_lookup(self, tmp_path, monkeypatch, make_config_file):
        """Test DJB_PROJECT_DIR is used to locate config files."""
        make_config_file("name: John\n")

        other_dir = tmp_path / "other"
        other_dir.mkdir()
        monkeypatch.chdir(other_dir)

        with patch.dict(os.environ, {"DJB_PROJECT_DIR": str(tmp_path)}):
            # No configure call - rely on env var
            assert config.project_dir == tmp_path
            assert config.name == "John"

    def test_project_root_overrides_env_project_dir(self, tmp_path):
        """Test explicit project_root wins over DJB_PROJECT_DIR."""
        env_root = tmp_path / "env"
        env_root.mkdir()
        (env_root / "pyproject.toml").write_text('[project]\nname = "env"\n')

        project_root = tmp_path / "root"
        project_root.mkdir()
        (project_root / "pyproject.toml").write_text('[project]\nname = "root"\n')

        with patch.dict(os.environ, {"DJB_PROJECT_DIR": str(env_root)}):
            configure(project_dir=str(project_root))
            assert config.project_dir == project_root
            assert config.project_name == "root"

    @pytest.mark.parametrize(
        "field,value,expected",
        [
            ("mode", "invalid_mode", Mode.DEVELOPMENT),
            ("target", "invalid_target", Target.HEROKU),
            ("mode", "true", Mode.DEVELOPMENT),  # YAML parses as bool
            ("target", "true", Target.HEROKU),  # YAML parses as bool
        ],
    )
    def test_invalid_enum_falls_back_to_default(
        self, tmp_path, make_config_file, field, value, expected
    ):
        """Test that invalid enum values in config fall back to defaults."""
        make_config_file(f"{field}: {value}\n")

        configure(project_dir=str(tmp_path))

        assert getattr(config, field) == expected


class TestConfigPriority:
    """Tests for configuration priority (CLI > env > file > default)."""

    def test_cli_overrides_env(self, tmp_path):
        """Test that CLI overrides take precedence over env vars."""
        with patch.dict(os.environ, {"DJB_MODE": "staging"}):
            configure(project_dir=str(tmp_path), mode=Mode.PRODUCTION)

            assert config.mode == Mode.PRODUCTION


class TestDualSourceConfig:
    """Tests for dual-source configuration (project.yaml + local.yaml)."""

    def test_load_project_config_missing(self, tmp_path):
        """Test loading when project config file doesn't exist."""
        result = load_config(PROJECT, tmp_path)
        assert result == {}

    def test_load_project_config_exists(self, tmp_path, make_config_file):
        """Test loading existing project config file."""
        make_config_file("hostname: example.com\nproject_name: myproject\n", config_type="project")

        result = load_config(PROJECT, tmp_path)
        assert result == {"hostname": "example.com", "project_name": "myproject"}

    def test_save_project_config(self, tmp_path):
        """Test saving project config file."""
        save_config(PROJECT, {"hostname": "example.com"}, tmp_path)

        result = load_config(PROJECT, tmp_path)
        assert result == {"hostname": "example.com"}


class TestConfigure:
    """Tests for djb.configure() function."""

    def test_configure_sets_overrides_applied_on_load(self, tmp_path):
        """Test configure() sets overrides that get applied when config loads."""
        # Set overrides before accessing config
        djb.configure(
            project_dir=tmp_path,
            mode=Mode.PRODUCTION,
        )

        # Now access config - should have overrides applied
        assert djb.config.project_dir == tmp_path
        assert djb.config.mode == Mode.PRODUCTION

    def test_configure_raises_if_config_already_loaded(self, tmp_path):
        """Test configure() raises RuntimeError if called after config access."""
        # Configure with project_dir so config can load
        djb.configure(project_dir=tmp_path)

        # Access config to trigger load
        _ = djb.config.project_dir

        # Now configure() should raise
        with pytest.raises(RuntimeError, match="must be called before accessing config"):
            djb.configure(mode=Mode.STAGING)

    def test_configure_filters_none_values(self, tmp_path):
        """Test configure() ignores None values - they don't overwrite existing values."""
        # Create a config file with a name value
        save_config(LOCAL, {"name": "John"}, tmp_path)

        # Set overrides with None for name - should NOT overwrite the file value
        djb.configure(
            project_dir=tmp_path,
            mode=Mode.STAGING,
            name=None,  # Should be ignored, not overwrite "John"
        )

        # Access config
        assert djb.config.mode == Mode.STAGING
        # name should still be "John" from file, not overwritten by None
        assert djb.config.name == "John"

    def test_reset_config_clears_pending_overrides(self, tmp_path):
        """Test reset_config() clears any pending overrides."""
        # Set overrides
        djb.configure(project_dir=tmp_path, mode=Mode.PRODUCTION)

        # Reset before accessing config
        djb.reset_config()

        # Set different overrides
        djb.configure(project_dir=tmp_path, mode=Mode.STAGING)

        # Access config - should have STAGING, not PRODUCTION
        assert djb.config.mode == Mode.STAGING

    def test_configure_can_be_called_multiple_times_before_load(self, tmp_path):
        """Test configure() can be called multiple times before config loads."""
        # First call
        djb.configure(project_dir=tmp_path, mode=Mode.DEVELOPMENT)

        # Second call - should merge/override
        djb.configure(mode=Mode.PRODUCTION, name="John")

        # Access config - should have merged overrides
        assert djb.config.project_dir == tmp_path
        assert djb.config.mode == Mode.PRODUCTION  # Overridden by second call
        assert djb.config.name == "John"


class TestConfigSource:
    """Tests for ConfigSource enum and provenance tracking."""

    @pytest.mark.parametrize(
        "source,expected_explicit,expected_derived",
        [
            # Explicit sources
            (ConfigSource.CLI, True, False),
            (ConfigSource.ENV, True, False),
            (ConfigSource.LOCAL_CONFIG, True, False),
            (ConfigSource.PROJECT_CONFIG, True, False),
            # Derived sources
            (ConfigSource.PYPROJECT, False, True),
            (ConfigSource.GIT, False, True),
            (ConfigSource.DERIVED, False, True),
            # Prompted is neither explicit nor derived
            (ConfigSource.PROMPTED, False, False),
        ],
    )
    def test_source_classification(self, source, expected_explicit, expected_derived):
        """Test is_explicit() and is_derived() classification."""
        assert source.is_explicit() is expected_explicit
        assert source.is_derived() is expected_derived


class TestDjbConfigProvenance:
    """Tests for DjbConfig provenance tracking methods."""

    def test_is_explicit_checks_source(self, tmp_path):
        """Test DjbConfig.is_explicit() checks provenance source."""
        # Create actual config file
        save_config(PROJECT, {"project_name": "from-file"}, tmp_path)

        cfg = DjbConfig()
        cfg.load({"project_dir": str(tmp_path)})

        assert cfg.is_explicit("project_name") is True
        assert cfg.is_explicit("name") is False  # Not in provenance

    def test_is_derived_checks_source(self, tmp_path):
        """Test DjbConfig.is_derived() checks provenance source."""
        # Create pyproject.toml for derived project_name
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "from-pyproject"\n')

        cfg = DjbConfig()
        cfg.load({"project_dir": str(tmp_path)})

        assert cfg.is_derived("project_name") is True
        assert cfg.is_derived("name") is False  # Not in provenance

    def test_has_no_source_returns_true_for_missing(self, tmp_path):
        """Test DjbConfig.has_no_source() returns True for fields without provenance."""
        # Create config with project_name only
        save_config(PROJECT, {"project_name": "test"}, tmp_path)

        cfg = DjbConfig()
        cfg.load({"project_dir": str(tmp_path)})

        # project_name is configured in config file
        assert cfg.is_configured("project_name") is True
        # name has no configured value(just default None)
        assert cfg.is_configured("name") is False

    def test_get_source_returns_source(self, tmp_path):
        """Test DjbConfig.get_source() returns the source for a field."""
        # Create pyproject.toml for derived project_name
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "from-pyproject"\n')

        cfg = DjbConfig()
        cfg.load({"project_dir": str(tmp_path)})

        assert cfg.get_source("project_name") == ConfigSource.PYPROJECT
        assert cfg.get_source("name") is None


class TestDjbConfigLoadProvenance:
    """Tests for DjbConfig.load() provenance tracking."""

    def test_tracks_project_name_from_config_file(self, tmp_path):
        """Test DjbConfig.load tracks project_name source from config file."""
        save_config(PROJECT, {"project_name": "myproject"}, tmp_path)

        configure(project_dir=str(tmp_path))
        assert config.project_name == "myproject"
        assert config.get_source("project_name") == ConfigSource.PROJECT_CONFIG
        assert config.is_explicit("project_name") is True

    def test_tracks_project_name_from_pyproject(self, tmp_path):
        """Test DjbConfig.load tracks project_name source from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "pyprojectname"\n')

        configure(project_dir=str(tmp_path))
        assert config.project_name == "pyprojectname"
        assert config.get_source("project_name") == ConfigSource.PYPROJECT
        assert config.is_derived("project_name") is True

    def test_tracks_project_name_from_dir_fallback(self, tmp_path):
        """Test DjbConfig.load tracks project_name from directory name fallback."""
        # No config, no pyproject.toml - should derive from directory name
        configure(project_dir=str(tmp_path))
        assert config.project_name is not None
        assert config.get_source("project_name") == ConfigSource.CWD_NAME
        assert config.is_derived("project_name") is True

    def test_tracks_name_from_local_config(self, tmp_path):
        """Test DjbConfig.load tracks name source from local config."""
        save_config(LOCAL, {"name": "John"}, tmp_path)

        configure(project_dir=str(tmp_path))
        assert config.name == "John"
        assert config.get_source("name") == ConfigSource.LOCAL_CONFIG
        assert config.is_explicit("name") is True

    def test_env_overrides_file_config(self, tmp_path):
        """Test DjbConfig.load tracks env var source when it overrides file."""
        save_config(PROJECT, {"project_name": "filename"}, tmp_path)

        with patch.dict(os.environ, {"DJB_PROJECT_NAME": "envname"}):
            configure(project_dir=str(tmp_path))
            assert config.project_name == "envname"
            assert config.get_source("project_name") == ConfigSource.ENV

    def test_load_overrides_updates_provenance(self, tmp_path):
        """Test DjbConfig.load with overrides updates provenance to CLI source."""
        save_config(PROJECT, {"project_name": "filename"}, tmp_path)

        # First load without override - access field to trigger loading
        configure(project_dir=str(tmp_path))
        assert config.project_name == "filename"  # Trigger loading
        assert config.get_source("project_name") == ConfigSource.PROJECT_CONFIG

        # Second load with override (need to reset first)
        djb.reset_config()
        configure(project_dir=str(tmp_path), project_name="cliname")
        assert config.project_name == "cliname"  # Trigger loading
        assert config.get_source("project_name") == ConfigSource.CLI

    def test_project_name_always_has_value(self, tmp_path):
        """Test project_name is always resolved (never None)."""
        # No config, no pyproject - should still derive from dir name
        configure(project_dir=str(tmp_path))
        assert config.project_name is not None
        assert config.project_name != ""


class TestLogLevelConfig:
    """Tests for log_level configuration field."""

    def test_default_log_level(self, tmp_path):
        """Test log_level defaults to 'info'."""
        configure(project_dir=str(tmp_path))
        assert config.log_level == "info"

    def test_log_level_from_project_config(self, tmp_path):
        """Test log_level loaded from project.yaml."""
        save_config(PROJECT, {"log_level": "debug"}, tmp_path)

        configure(project_dir=str(tmp_path))
        assert config.log_level == "debug"
        assert config.get_source("log_level") == ConfigSource.PROJECT_CONFIG

    def test_log_level_from_local_config(self, tmp_path):
        """Test log_level loaded from local.yaml."""
        save_config(LOCAL, {"log_level": "warning"}, tmp_path)

        configure(project_dir=str(tmp_path))
        assert config.log_level == "warning"
        assert config.get_source("log_level") == ConfigSource.LOCAL_CONFIG

    def test_local_config_overrides_project_config(self, tmp_path):
        """Test local.yaml log_level overrides project.yaml."""
        save_config(PROJECT, {"log_level": "info"}, tmp_path)
        save_config(LOCAL, {"log_level": "debug"}, tmp_path)

        configure(project_dir=str(tmp_path))
        assert config.log_level == "debug"
        assert config.get_source("log_level") == ConfigSource.LOCAL_CONFIG

    def test_log_level_from_env(self, tmp_path):
        """Test DJB_LOG_LEVEL environment variable."""
        with patch.dict(os.environ, {"DJB_LOG_LEVEL": "error"}):
            configure(project_dir=str(tmp_path))
            assert config.log_level == "error"
            assert config.get_source("log_level") == ConfigSource.ENV

    def test_env_overrides_config_file(self, tmp_path):
        """Test DJB_LOG_LEVEL overrides config file values."""
        save_config(PROJECT, {"log_level": "info"}, tmp_path)

        with patch.dict(os.environ, {"DJB_LOG_LEVEL": "debug"}):
            configure(project_dir=str(tmp_path))
            assert config.log_level == "debug"
            assert config.get_source("log_level") == ConfigSource.ENV

    def test_cli_overrides_env(self, tmp_path):
        """Test CLI override has highest priority."""
        with patch.dict(os.environ, {"DJB_LOG_LEVEL": "warning"}):
            configure(project_dir=str(tmp_path), log_level="error")
            assert config.log_level == "error"
            assert config.get_source("log_level") == ConfigSource.CLI

    def test_log_level_case_insensitive(self, tmp_path):
        """Test log_level is normalized to lowercase."""
        save_config(PROJECT, {"log_level": "DEBUG"}, tmp_path)

        configure(project_dir=str(tmp_path))
        assert config.log_level == "debug"

    def test_log_level_validation_accepts_valid_values(self, tmp_path):
        """Test all valid log levels are accepted."""
        valid_levels = ["error", "warning", "info", "note", "debug"]

        for level in valid_levels:
            cfg = DjbConfig()
            cfg.load({"project_dir": str(tmp_path), "project_name": "test", "log_level": level})
            assert cfg.log_level == level

    def test_log_level_validation_rejects_invalid_value(self, tmp_path):
        """Test invalid log level raises validation error."""
        with pytest.raises(ConfigValidationError, match="Invalid log_level"):
            cfg = DjbConfig()
            cfg.load({"project_dir": str(tmp_path), "project_name": "test", "log_level": "verbose"})

    def test_log_level_validation_rejects_invalid_yaml_types(self, tmp_path):
        """Test that non-string YAML types are caught during validation."""
        # When loading from config files, YAML can produce non-string types.
        # Booleans like True normalize to "true" which fails enum validation.
        save_config(PROJECT, {"log_level": True}, tmp_path)  # YAML boolean
        with pytest.raises(ConfigValidationError, match="Invalid log_level"):
            cfg = DjbConfig()
            cfg.load({"project_dir": str(tmp_path)})
