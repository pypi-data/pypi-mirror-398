"""Tests for djb config CLI command."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from djb import reset_config
from djb.cli.config_cmd import _format_json_with_provenance, _get_field_metadata
from djb.cli.djb import djb_cli
from djb.config import ConfigSource
from djb.config.field import ConfigFieldABC


class TestConfigShow:
    """Tests for djb config --show."""

    def test_show_outputs_json(self, runner, tmp_path):
        """Test that --show outputs valid JSON."""
        result = runner.invoke(djb_cli, ["-q", "config", "--show"])

        assert result.exit_code == 0
        # Should be valid JSON
        config = json.loads(result.output)
        assert isinstance(config, dict)

    def test_show_contains_expected_keys(self, runner, tmp_path):
        """Test that --show output contains all expected config keys."""
        result = runner.invoke(djb_cli, ["-q", "config", "--show"])

        assert result.exit_code == 0
        config = json.loads(result.output)

        expected_keys = {
            "project_dir",
            "project_name",
            "name",
            "email",
            "hostname",
            "seed_command",
            "mode",
            "target",
            "log_level",
        }
        assert expected_keys == set(config.keys())

    def test_show_excludes_private_attributes(self, runner, tmp_path):
        """Test that --show output excludes private attributes."""
        result = runner.invoke(djb_cli, ["-q", "config", "--show"])

        assert result.exit_code == 0
        config = json.loads(result.output)

        # Private attributes should not be in output
        assert "_loaded" not in config
        assert "_provenance" not in config

    def test_show_serializes_enums_as_strings(self, runner, tmp_path):
        """Test that mode and target are serialized as strings, not enum objects."""
        result = runner.invoke(djb_cli, ["-q", "config", "--show"])

        assert result.exit_code == 0
        config = json.loads(result.output)

        # Should be string values, not enum representations
        assert config["mode"] == "development"
        assert config["target"] == "heroku"

    def test_show_serializes_path_as_string(self, runner, tmp_path):
        """Test that project_dir is serialized as a string path."""
        result = runner.invoke(djb_cli, ["-q", "config", "--show"])

        assert result.exit_code == 0
        config = json.loads(result.output)

        # Should be a string, not a Path object representation
        assert isinstance(config["project_dir"], str)
        assert not config["project_dir"].startswith("PosixPath")

    def test_config_without_args_shows_help(self, runner, tmp_path):
        """Test that 'djb config' without args shows help."""
        result = runner.invoke(djb_cli, ["-q", "config"])

        assert result.exit_code == 0
        assert "Manage djb configuration" in result.output
        assert "--show" in result.output

    def test_with_provenance_outputs_json_with_comments(self, runner, tmp_path):
        """Test that --with-provenance adds provenance comments to JSON."""
        result = runner.invoke(djb_cli, ["-q", "config", "--with-provenance"])

        assert result.exit_code == 0
        # Should contain JSON-like structure with // comments
        assert "{" in result.output
        assert "}" in result.output
        assert "//" in result.output

    def test_with_provenance_shows_environment_source(self, runner, tmp_path):
        """Test that --with-provenance shows environment as source for env vars."""
        result = runner.invoke(djb_cli, ["-q", "config", "--with-provenance"])

        assert result.exit_code == 0
        # Fixture sets DJB_PROJECT_NAME, so it should show "environment"
        assert "environment" in result.output

    def test_with_provenance_shows_all_keys(self, runner, tmp_path):
        """Test that --with-provenance output contains all config keys."""
        result = runner.invoke(djb_cli, ["-q", "config", "--with-provenance"])

        assert result.exit_code == 0
        assert '"project_dir"' in result.output
        assert '"project_name"' in result.output
        assert '"mode"' in result.output

    def test_with_provenance_alone_shows_output(self, runner, tmp_path):
        """Test that --with-provenance alone (without --show) shows output."""
        result = runner.invoke(djb_cli, ["-q", "config", "--with-provenance"])

        assert result.exit_code == 0
        # Should output config, not help
        assert '"project_dir"' in result.output


class TestConfigProjectName:
    """Tests for djb config project_name subcommand."""

    def test_show_current_value_from_pyproject(self, runner, tmp_path):
        """Test showing current project_name (falls back to pyproject.toml)."""
        result = runner.invoke(djb_cli, ["-q", "config", "project_name"])

        assert result.exit_code == 0
        # Should show the project name from pyproject.toml
        assert "project_name:" in result.output

    def test_set_valid_project_name(self, runner, tmp_path):
        """Test setting a valid project name."""
        result = runner.invoke(djb_cli, ["-q", "config", "project_name", "my-app"])

        assert result.exit_code == 0
        assert "project_name set to: my-app" in result.output

    def test_set_invalid_project_name_uppercase(self, runner, tmp_path):
        """Test that uppercase project names are rejected."""
        result = runner.invoke(djb_cli, ["-q", "config", "project_name", "MyApp"])

        assert result.exit_code != 0
        assert "DNS label" in result.output

    def test_set_invalid_project_name_starts_with_hyphen(self, runner, tmp_path):
        """Test that project names starting with hyphen are rejected."""
        # Use -- to separate options from arguments (otherwise -myapp is parsed as -m option)
        result = runner.invoke(djb_cli, ["-q", "config", "project_name", "--", "-myapp"])

        assert result.exit_code != 0
        assert "DNS label" in result.output

    def test_delete_project_name(self, runner, tmp_path, monkeypatch):
        """Test deleting the project_name setting."""
        # Clear env var so we can test deleting from config file
        # (env has higher priority than config files, so if set it would shadow)
        monkeypatch.delenv("DJB_PROJECT_NAME", raising=False)

        # First set a value
        result = runner.invoke(djb_cli, ["-q", "config", "project_name", "my-app"])
        assert result.exit_code == 0

        # Reset config singleton between invocations
        reset_config()

        # Then delete it
        result = runner.invoke(djb_cli, ["-q", "config", "project_name", "--delete"])

        assert result.exit_code == 0
        assert "project_name removed" in result.output

    def test_delete_refuses_to_delete_from_environment(self, runner, tmp_path):
        """Test that delete warns when value comes from environment, not config file."""
        # The fixture sets DJB_PROJECT_NAME in environment
        # Try to delete - should warn that it's from environment
        result = runner.invoke(djb_cli, ["-q", "config", "project_name", "--delete"])

        assert result.exit_code == 0
        assert "set from environment" in result.output
        assert "not from a config file" in result.output

    def test_delete_refuses_to_delete_from_directory_name(self, runner, tmp_path, monkeypatch):
        """Test that delete warns when value is derived from directory name."""
        # Clear explicit sources - project_name will fall back to directory name
        monkeypatch.delenv("DJB_PROJECT_NAME", raising=False)
        # Clear pyproject.toml so it falls back to directory name
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        reset_config()

        result = runner.invoke(djb_cli, ["-q", "config", "project_name", "--delete"])

        assert result.exit_code == 0
        assert "set from cwd_name" in result.output
        assert "not from a config file" in result.output


class TestFormatJsonWithProvenance:
    """Unit tests for _format_json_with_provenance helper function."""

    def test_formats_config_as_json_with_comments(self):
        """Test _format_json_with_provenance produces JSON with provenance comments."""
        # Create a mock config object
        mock_config = Mock()
        mock_config.to_dict.return_value = {
            "project_dir": "/path/to/project",
            "mode": "development",
        }
        mock_config.get_source.side_effect = lambda key: {
            "project_dir": ConfigSource.CLI,
            "mode": ConfigSource.DEFAULT,
        }.get(key)

        result = _format_json_with_provenance(mock_config)

        # Should have JSON structure with comments
        assert "{" in result
        assert "}" in result
        assert "//" in result
        assert '"project_dir"' in result
        assert '"mode"' in result

    def test_includes_provenance_for_each_key(self):
        """Test _format_json_with_provenance shows provenance for each config key."""
        mock_config = Mock()
        mock_config.to_dict.return_value = {
            "name": "Test User",
            "email": "test@example.com",
        }
        mock_config.get_source.side_effect = lambda key: {
            "name": ConfigSource.LOCAL_CONFIG,
            "email": ConfigSource.ENV,
        }.get(key)

        result = _format_json_with_provenance(mock_config)

        # Should include provenance values
        assert "local_config" in result
        assert "environment" in result

    def test_shows_not_set_for_none_source(self):
        """Test _format_json_with_provenance shows '(not set)' when source is None."""
        mock_config = Mock()
        mock_config.to_dict.return_value = {
            "hostname": None,
        }
        mock_config.get_source.return_value = None

        result = _format_json_with_provenance(mock_config)

        assert "(not set)" in result

    def test_aligns_provenance_comments(self):
        """Test _format_json_with_provenance aligns comments across lines."""
        mock_config = Mock()
        mock_config.to_dict.return_value = {
            "short": "a",
            "very_long_key_name": "value",
        }
        mock_config.get_source.return_value = ConfigSource.DEFAULT

        result = _format_json_with_provenance(mock_config)

        # Both lines should have "//" at the same column
        lines = [line for line in result.split("\n") if "//" in line]
        comment_positions = [line.index("//") for line in lines]
        assert len(set(comment_positions)) == 1, "Comments should be aligned"


class TestGetFieldMetadata:
    """Unit tests for _get_field_metadata helper function."""

    def test_returns_config_field_for_valid_field(self):
        """Test _get_field_metadata returns ConfigFieldABC for valid field."""
        result = _get_field_metadata("project_name")
        assert isinstance(result, ConfigFieldABC)
        assert result.field_name == "project_name"

    def test_raises_for_unknown_field(self):
        """Test _get_field_metadata raises ValueError for unknown field."""
        with pytest.raises(ValueError) as exc_info:
            _get_field_metadata("nonexistent_field")
        assert "Unknown field" in str(exc_info.value)

    def test_raises_for_non_config_field(self):
        """Test _get_field_metadata raises ValueError for non-config attrs field."""
        # _loaded and _provenance are internal fields without ConfigFieldABC metadata
        # but they shouldn't be exposed anyway - try an internal field
        # This test verifies the error path even if no such field exists in practice
        # by patching attrs.fields to return a field without the metadata
        fake_field = MagicMock()
        fake_field.name = "fake_field"
        fake_field.metadata = {}  # No ATTRSLIB_METADATA_KEY

        with (
            patch("djb.cli.config_cmd.attrs.fields", return_value=[fake_field]),
            pytest.raises(ValueError) as exc_info,
        ):
            _get_field_metadata("fake_field")
        assert "not a config field" in str(exc_info.value)
